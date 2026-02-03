"""
Enhanced Agent Health Monitoring System for AI Compute on Idle Laptops
Includes idle detection, power management, and resource optimization
"""

import psutil
import time
import logging
import torch
import platform
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from threading import Thread, Lock
from queue import Queue
import GPUtil
import subprocess
import os

logger = logging.getLogger(__name__)

@dataclass
class MetricSample:
    timestamp: float
    value: float
    metric_type: str

@dataclass
class IdleState:
    is_idle: bool
    idle_duration: float
    cpu_threshold: float
    memory_threshold: float
    user_active: bool
    last_activity: datetime

class LaptopPowerManager:
    """Manages laptop power settings and battery monitoring"""
    
    def __init__(self):
        self.on_battery = False
        self.battery_level = 100.0
        self.power_saver_mode = False
        
    def get_battery_info(self) -> Dict[str, Any]:
        """Get battery information if available"""
        try:
            battery = psutil.sensors_battery()
            if battery:
                self.on_battery = not battery.power_plugged
                self.battery_level = battery.percent
                return {
                    "on_battery": self.on_battery,
                    "battery_level": self.battery_level,
                    "power_plugged": battery.power_plugged,
                    "time_left": battery.secsleft if battery.secsleft != -1 else None
                }
        except Exception as e:
            logger.debug(f"Could not get battery info: {e}")
        
        return {
            "on_battery": False,
            "battery_level": 100.0,
            "power_plugged": True,
            "time_left": None
        }
    
    def should_throttle_compute(self) -> bool:
        """Determine if compute should be throttled based on power state"""
        battery_info = self.get_battery_info()
        return (
            battery_info["on_battery"] and 
            battery_info["battery_level"] < 20.0
        )
    
    def get_compute_limits(self) -> Dict[str, Any]:
        """Get compute resource limits based on power state"""
        battery_info = self.get_battery_info()
        
        if battery_info["on_battery"]:
            if battery_info["battery_level"] < 20:
                return {"max_cpu_usage": 30, "max_memory_usage": 50, "max_concurrent_tasks": 1}
            elif battery_info["battery_level"] < 50:
                return {"max_cpu_usage": 50, "max_memory_usage": 70, "max_concurrent_tasks": 2}
            else:
                return {"max_cpu_usage": 70, "max_memory_usage": 80, "max_concurrent_tasks": 3}
        else:
            return {"max_cpu_usage": 90, "max_memory_usage": 90, "max_concurrent_tasks": 5}

class MetricsBuffer:
    def __init__(self, max_samples: int = 100):
        self.max_samples = max_samples
        self.samples: Dict[str, List[MetricSample]] = {}
        self.lock = Lock()

    def add_sample(self, metric_type: str, value: float):
        with self.lock:
            if metric_type not in self.samples:
                self.samples[metric_type] = []
            
            self.samples[metric_type].append(
                MetricSample(
                    timestamp=time.time(),
                    value=value,
                    metric_type=metric_type
                )
            )
            
            # Keep only recent samples
            if len(self.samples[metric_type]) > self.max_samples:
                self.samples[metric_type] = self.samples[metric_type][-self.max_samples:]

    def get_metrics(self, metric_type: str) -> List[MetricSample]:
        with self.lock:
            return self.samples.get(metric_type, [])

class HealthMonitor:
    def __init__(self, collection_interval: float = 1.0):
        self.start_time = time.time()
        self.collection_interval = collection_interval
        self.metrics_buffer = MetricsBuffer()
        self.task_history: List[Dict] = []
        self.max_history = 1000
        self.is_collecting = False
        self.collection_thread: Optional[Thread] = None
        self.gpu_enabled = torch.cuda.is_available()
        
        # Laptop-specific features
        self.power_manager = LaptopPowerManager()
        self.idle_threshold_cpu = 10.0  # CPU usage below this is considered idle
        self.idle_threshold_duration = 300  # 5 minutes of low activity to be considered idle
        self.last_user_activity = datetime.now()
        self.idle_start_time: Optional[datetime] = None
        self.currently_idle = False
        
        # Initialize GPU monitoring if available
        self.gpus = []
        if self.gpu_enabled:
            try:
                self.gpus = GPUtil.getGPUs()
                logger.info(f"Initialized GPU monitoring for {len(self.gpus)} GPUs")
            except Exception as e:
                logger.warning(f"Failed to initialize GPU monitoring: {e}")

    def detect_idle_state(self) -> IdleState:
        """Detect if the laptop is idle based on system activity"""
        try:
            # Check CPU usage
            cpu_usage = psutil.cpu_percent(interval=1)
            
            # Check mouse/keyboard activity (platform specific)
            user_active = self._check_user_activity()
            
            # Check if system is under low load
            memory_usage = psutil.virtual_memory().percent
            low_load = cpu_usage < self.idle_threshold_cpu and memory_usage < 70
            
            # Determine idle state
            current_time = datetime.now()
            
            if user_active:
                self.last_user_activity = current_time
                self.idle_start_time = None
                self.currently_idle = False
            elif low_load and not self.currently_idle:
                if self.idle_start_time is None:
                    self.idle_start_time = current_time
                elif (current_time - self.idle_start_time).total_seconds() > self.idle_threshold_duration:
                    self.currently_idle = True
            elif not low_load:
                self.idle_start_time = None
                self.currently_idle = False
            
            idle_duration = 0
            if self.idle_start_time:
                idle_duration = (current_time - self.idle_start_time).total_seconds()
            
            return IdleState(
                is_idle=self.currently_idle,
                idle_duration=idle_duration,
                cpu_threshold=self.idle_threshold_cpu,
                memory_threshold=70.0,
                user_active=user_active,
                last_activity=self.last_user_activity
            )
            
        except Exception as e:
            logger.error(f"Error detecting idle state: {e}")
            return IdleState(
                is_idle=False,
                idle_duration=0,
                cpu_threshold=self.idle_threshold_cpu,
                memory_threshold=70.0,
                user_active=True,
                last_activity=datetime.now()
            )
    
    def _check_user_activity(self) -> bool:
        """Check for user activity (mouse/keyboard)"""
        try:
            if platform.system() == "Linux":
                # Check for recent user input using xprintidle or similar
                try:
                    result = subprocess.run(['xprintidle'], capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        idle_ms = int(result.stdout.strip())
                        # If idle time is less than 30 seconds, consider user active
                        return idle_ms < 30000
                except (subprocess.TimeoutExpired, FileNotFoundError, ValueError):
                    pass
                
                # Fallback: check process list for user applications
                user_processes = ['chrome', 'firefox', 'code', 'vscode', 'slack', 'discord']
                for proc in psutil.process_iter(['name']):
                    try:
                        if any(app in proc.info['name'].lower() for app in user_processes):
                            return True
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                        
            elif platform.system() == "Darwin":  # macOS
                # Use ioreg to check for user activity on macOS
                try:
                    result = subprocess.run(['ioreg', '-c', 'IOHIDSystem'], 
                                          capture_output=True, text=True, timeout=5)
                    if 'HIDIdleTime' in result.stdout:
                        # Parse idle time from ioreg output
                        for line in result.stdout.split('\n'):
                            if 'HIDIdleTime' in line and '"' in line:
                                idle_ns = int(line.split('"')[-2])
                                idle_ms = idle_ns / 1_000_000  # Convert nanoseconds to milliseconds
                                return idle_ms < 30000
                except (subprocess.TimeoutExpired, ValueError):
                    pass
                    
            elif platform.system() == "Windows":
                # Use Windows API to check for idle time
                try:
                    import ctypes
                    class LASTINPUTINFO(ctypes.Structure):
                        _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]
                    
                    lii = LASTINPUTINFO()
                    lii.cbSize = ctypes.sizeof(LASTINPUTINFO)
                    ctypes.windll.user32.GetLastInputInfo(ctypes.byref(lii))
                    
                    idle_ms = ctypes.windll.kernel32.GetTickCount() - lii.dwTime
                    return idle_ms < 30000
                except Exception:
                    pass
            
            # Default fallback: assume user is active if we can't detect
            return True
            
        except Exception as e:
            logger.debug(f"Error checking user activity: {e}")
            return True
    
    def get_ai_compute_readiness(self) -> Dict[str, Any]:
        """Get AI compute readiness score and recommendations"""
        idle_state = self.detect_idle_state()
        battery_info = self.power_manager.get_battery_info()
        compute_limits = self.power_manager.get_compute_limits()
        
        # Calculate readiness score (0-100)
        readiness_score = 0
        
        # Idle state contributes 40 points
        if idle_state.is_idle:
            if idle_state.idle_duration > 1800:  # > 30 minutes
                readiness_score += 40
            elif idle_state.idle_duration > 600:  # > 10 minutes
                readiness_score += 30
            else:
                readiness_score += 20
        else:
            readiness_score += 5
        
        # Power state contributes 30 points
        if not battery_info["on_battery"]:
            readiness_score += 30
        elif battery_info["battery_level"] > 80:
            readiness_score += 25
        elif battery_info["battery_level"] > 50:
            readiness_score += 15
        elif battery_info["battery_level"] > 20:
            readiness_score += 5
        
        # System resources contribute 30 points
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_usage = psutil.virtual_memory().percent
        
        if cpu_usage < 20 and memory_usage < 50:
            readiness_score += 30
        elif cpu_usage < 50 and memory_usage < 70:
            readiness_score += 20
        elif cpu_usage < 80 and memory_usage < 85:
            readiness_score += 10
        
        # Determine if ready for AI compute
        ready_for_ai = (
            readiness_score >= 60 and
            not self.power_manager.should_throttle_compute()
        )
        
        return {
            "ready_for_ai": ready_for_ai,
            "readiness_score": readiness_score,
            "idle_state": {
                "is_idle": idle_state.is_idle,
                "idle_duration": idle_state.idle_duration,
                "user_active": idle_state.user_active
            },
            "power_state": battery_info,
            "compute_limits": compute_limits,
            "current_resources": {
                "cpu_usage": cpu_usage,
                "memory_usage": memory_usage,
                "gpu_available": self.gpu_enabled
            },
            "recommendations": self._get_compute_recommendations(readiness_score, idle_state, battery_info)
        }
    
    def _get_compute_recommendations(self, score: int, idle_state: IdleState, battery_info: Dict) -> List[str]:
        """Get recommendations for AI compute based on current state"""
        recommendations = []
        
        if score < 30:
            recommendations.append("System is busy - not ideal for AI compute")
        elif score < 60:
            recommendations.append("System has limited availability - light AI tasks only")
        
        if not idle_state.is_idle:
            recommendations.append("Wait for system to be idle for better performance")
        elif idle_state.idle_duration < 600:
            recommendations.append("System recently active - monitor for stability")
        
        if battery_info["on_battery"]:
            if battery_info["battery_level"] < 20:
                recommendations.append("Critical battery level - avoid AI compute")
            elif battery_info["battery_level"] < 50:
                recommendations.append("Consider connecting to power for intensive tasks")
        
        if psutil.cpu_percent(interval=1) > 80:
            recommendations.append("High CPU usage - may impact AI task performance")
        
        if psutil.virtual_memory().percent > 85:
            recommendations.append("High memory usage - may limit model size")
        
        if not recommendations and score >= 60:
            recommendations.append("System ready for AI compute tasks")
        
        return recommendations

    def start_collection(self):
        """Start the metrics collection thread"""
        if not self.is_collecting:
            self.is_collecting = True
            self.collection_thread = Thread(target=self._collect_metrics, daemon=True)
            self.collection_thread.start()
            logger.info("Started health metrics collection")

    def stop_collection(self):
        """Stop the metrics collection thread"""
        self.is_collecting = False
        if self.collection_thread:
            self.collection_thread.join()
            logger.info("Stopped health metrics collection")

    def _collect_metrics(self):
        """Continuously collect metrics at the specified interval"""
        while self.is_collecting:
            try:
                # Collect CPU metrics
                cpu_percent = psutil.cpu_percent(interval=None)
                self.metrics_buffer.add_sample("cpu_usage", cpu_percent)

                # Collect memory metrics
                memory = psutil.virtual_memory()
                self.metrics_buffer.add_sample("memory_usage", memory.percent)
                self.metrics_buffer.add_sample("memory_available", memory.available / 1024 / 1024)  # MB

                # Collect GPU metrics if available
                if self.gpu_enabled:
                    for gpu_id, gpu in enumerate(self.gpus):
                        try:
                            gpu.load = GPUtil.getGPUs()[gpu_id].load * 100
                            gpu.memoryUtil = GPUtil.getGPUs()[gpu_id].memoryUtil * 100
                            self.metrics_buffer.add_sample(f"gpu_{gpu_id}_usage", gpu.load)
                            self.metrics_buffer.add_sample(f"gpu_{gpu_id}_memory", gpu.memoryUtil)
                        except Exception as e:
                            logger.warning(f"Failed to collect GPU metrics: {e}")

                # Add more metrics as needed

            except Exception as e:
                logger.error(f"Error collecting metrics: {e}")

    def get_detailed_health(self) -> Dict[str, Any]:
        """Get comprehensive health information including AI compute readiness"""
        return {
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": time.time() - self.start_time,
            "system": self._get_system_info(),
            "resources": self._get_resource_usage(),
            "tasks": self._get_task_stats(),
            "status": self._get_overall_status(),
            "ai_compute_readiness": self.get_ai_compute_readiness(),
            "idle_state": self.detect_idle_state()._asdict(),
            "power_management": self.power_manager.get_battery_info()
        }
        
    def _get_system_info(self) -> Dict[str, Any]:
        return {
            "cpu_count": psutil.cpu_count(),
            "cpu_count_logical": psutil.cpu_count(logical=True),
            "memory_total": psutil.virtual_memory().total,
            "boot_time": psutil.boot_time()
        }
        
    def _get_resource_usage(self) -> Dict[str, Any]:
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "cpu_usage": psutil.cpu_percent(interval=1),
            "memory_usage": memory.percent,
            "memory_total": memory.total,
            "memory_available": memory.available,
            "memory_used": memory.used,
            "disk_usage": disk.percent,
            "disk_total": disk.total,
            "disk_free": disk.free
        }
        
    def _get_task_stats(self) -> Dict[str, Any]:
        if not self.task_history:
            return {
                "total_tasks": 0,
                "completed_tasks": 0,
                "failed_tasks": 0,
                "avg_duration": 0.0,
                "success_rate": 0.0
            }
            
        completed = [t for t in self.task_history if t.get("status") == "completed"]
        failed = [t for t in self.task_history if t.get("status") == "failed"]
        
        avg_duration = 0.0
        if completed:
            total_duration = sum(t.get("duration", 0) for t in completed)
            avg_duration = total_duration / len(completed)
            
        success_rate = len(completed) / len(self.task_history) * 100 if self.task_history else 0
        
        return {
            "total_tasks": len(self.task_history),
            "completed_tasks": len(completed),
            "failed_tasks": len(failed),
            "avg_duration": avg_duration,
            "success_rate": success_rate
        }
        
    def _get_overall_status(self) -> str:
        try:
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_usage = psutil.virtual_memory().percent
            
            if cpu_usage > 90 or memory_usage > 90:
                return "critical"
            elif cpu_usage > 70 or memory_usage > 70:
                return "warning"
            else:
                return "healthy"
        except Exception:
            return "unknown"
            
    def record_task(self, task_id: str, status: str, duration: float = 0.0):
        task_record = {
            "task_id": task_id,
            "status": status,
            "duration": duration,
            "timestamp": datetime.now().isoformat()
        }
        
        self.task_history.append(task_record)
        
        if len(self.task_history) > self.max_history:
            self.task_history = self.task_history[-self.max_history:]

health_monitor = HealthMonitor()