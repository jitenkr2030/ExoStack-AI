"""
Enhanced Distributed Task Scheduler for AI Compute on Idle Laptops
Prioritizes idle laptops and manages power-aware task distribution
"""

import asyncio
import logging
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import aiohttp
from ..models import Task, TaskStatus
from .registry import registry
from .logger import get_logger, log_task_event

logger = get_logger(__name__)

class DistributedScheduler:
    def __init__(self):
        self.running = False
        self.task_queue = asyncio.Queue()
        self.node_loads: Dict[str, float] = {}
        self.task_assignments: Dict[str, str] = {}
        self.ai_readiness_cache: Dict[str, Tuple[Dict, float]] = {}  # node_id -> (readiness, timestamp)
        self.readiness_cache_ttl = 30  # seconds
        
    async def start(self):
        self.running = True
        logger.info("Starting AI-aware distributed scheduler for idle laptops")
        asyncio.create_task(self._process_task_queue())
        asyncio.create_task(self._monitor_node_health())
        asyncio.create_task(self._cleanup_readiness_cache())
        
    async def stop(self):
        self.running = False
        logger.info("Stopping distributed scheduler")
        
    async def schedule_task(self, task: Task) -> bool:
        """Schedule AI task with laptop-aware optimization"""
        try:
            best_node = await self._select_optimal_ai_node(task)
            if not best_node:
                logger.warning(f"No available laptop nodes ready for AI task {task.id}")
                return False
                
            success = await self._assign_task_to_node(task, best_node)
            if success:
                self.task_assignments[task.id] = best_node["id"]
                log_task_event(task.id, "scheduled", best_node["id"])
                logger.info(f"Scheduled AI task {task.id} to laptop {best_node['id']} (readiness: {best_node.get('readiness_score', 0)})")
                
            return success
            
        except Exception as e:
            logger.error(f"Error scheduling AI task {task.id}: {e}")
            return False
            
    async def _select_optimal_ai_node(self, task: Task) -> Optional[Dict]:
        """Select optimal laptop node based on AI compute readiness"""
        available_nodes = await self._get_ai_ready_nodes()
        if not available_nodes:
            return None
            
        # Sort nodes by AI compute readiness score (highest first)
        sorted_nodes = sorted(
            available_nodes, 
            key=lambda node: node.get('readiness_score', 0), 
            reverse=True
        )
        
        # Additional filtering for task requirements
        task_type = task.task_type.lower() if hasattr(task, 'task_type') else 'general'
        
        for node in sorted_nodes:
            # Check if node meets task requirements
            if self._node_meets_requirements(node, task_type):
                logger.debug(f"Selected node {node['id']} with readiness score {node.get('readiness_score', 0)}")
                return node
                
        # Fallback to highest scoring node if none meet requirements
        return sorted_nodes[0] if sorted_nodes else None
        
    def _node_meets_requirements(self, node: Dict, task_type: str) -> bool:
        """Check if node meets task-specific requirements"""
        readiness_score = node.get('readiness_score', 0)
        gpu_available = node.get('gpu_available', False)
        max_concurrent = node.get('max_concurrent_tasks', 1)
        current_load = node.get('current_load', 0)
        
        # Basic readiness check
        if readiness_score < 60:
            return False
            
        # Task-specific requirements
        if task_type in ['gpu_inference', 'training'] and not gpu_available:
            return False
            
        # Load check
        if current_load >= max_concurrent:
            return False
            
        return True
        
    async def _get_ai_ready_nodes(self) -> List[Dict]:
        """Get list of nodes ready for AI compute"""
        all_nodes = registry.get_all_nodes()
        ai_ready_nodes = []
        
        for node in all_nodes:
            if node.get("status") != "online":
                continue
                
            # Get AI readiness from cache or fetch fresh
            readiness = await self._get_ai_readiness(node["id"])
            if not readiness or not readiness.get("ready_for_ai", False):
                continue
                
            # Add readiness info to node
            node["readiness_score"] = readiness.get("readiness_score", 0)
            node["idle_state"] = readiness.get("idle_state", {})
            node["power_state"] = readiness.get("power_state", {})
            node["compute_limits"] = readiness.get("compute_limits", {})
            node["current_resources"] = readiness.get("current_resources", {})
            node["gpu_available"] = readiness.get("current_resources", {}).get("gpu_available", False)
            
            ai_ready_nodes.append(node)
            
        return ai_ready_nodes
        
    async def _get_ai_readiness(self, node_id: str) -> Optional[Dict]:
        """Get AI compute readiness for a node, using cache when possible"""
        current_time = time.time()
        
        # Check cache
        if node_id in self.ai_readiness_cache:
            cached_readiness, cached_time = self.ai_readiness_cache[node_id]
            if current_time - cached_time < self.readiness_cache_ttl:
                return cached_readiness
                
        # Fetch fresh data
        node = registry.get_node(node_id)
        if not node:
            return None
            
        try:
            node_url = f"http://{node['host']}:{node['port']}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{node_url}/ai-readiness",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        readiness = await response.json()
                        # Cache the result
                        self.ai_readiness_cache[node_id] = (readiness, current_time)
                        return readiness
                        
        except Exception as e:
            logger.debug(f"Failed to get AI readiness for node {node_id}: {e}")
            
        return None
        
    async def _assign_task_to_node(self, task: Task, node: Dict) -> bool:
        """Assign task to node with AI compute validation"""
        try:
            registry.update_task_status(task.id, TaskStatus.RUNNING, node["id"])
            success = await self._send_task_to_node(task, node)
            
            if not success:
                registry.update_task_status(task.id, TaskStatus.PENDING)
                logger.warning(f"Failed to send AI task {task.id} to node {node['id']}")
            else:
                logger.info(f"Successfully assigned AI task {task.id} to laptop {node['id']}")
                
            return success
            
        except Exception as e:
            logger.error(f"Error assigning AI task {task.id}: {e}")
            registry.update_task_status(task.id, TaskStatus.PENDING)
            return False
            
    async def _send_task_to_node(self, task: Task, node: Dict) -> bool:
        """Send task to node with AI compute context"""
        try:
            node_url = f"http://{node['host']}:{node['port']}"
            
            # Add AI compute context to task
            task_data = task.dict()
            task_data["ai_compute_context"] = {
                "node_readiness_score": node.get('readiness_score', 0),
                "scheduled_at": datetime.now().isoformat(),
                "power_aware": True
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{node_url}/tasks/execute",
                    json=task_data,
                    timeout=aiohttp.ClientTimeout(total=60)  # Longer timeout for AI tasks
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        if result.get("status") == "rejected":
                            logger.warning(f"Node {node['id']} rejected AI task {task.id}: {result.get('error')}")
                            return False
                        return True
                    else:
                        logger.warning(f"Node {node['id']} returned status {response.status} for task {task.id}")
                        return False
                    
        except Exception as e:
            logger.error(f"Failed to send AI task to laptop {node['id']}: {e}")
            return False
            
    async def _get_available_nodes(self) -> List[Dict]:
        """Get basic list of available nodes (legacy compatibility)"""
        all_nodes = registry.get_all_nodes()
        return [node for node in all_nodes if node.get("status") == "online"]
        
    async def _process_task_queue(self):
        """Process pending AI tasks with intelligent scheduling"""
        while self.running:
            try:
                pending_tasks = registry.get_tasks_by_status(TaskStatus.PENDING)
                
                # Sort tasks by priority and creation time
                pending_tasks.sort(key=lambda t: (t.get('priority', 0), t.get('created_at', '')))
                
                for task_data in pending_tasks:
                    if not self.running:
                        break
                    task = Task(**task_data)
                    await self.schedule_task(task)
                    
                await asyncio.sleep(2)  # Slightly longer interval for AI tasks
                
            except Exception as e:
                logger.error(f"Error processing AI task queue: {e}")
                await asyncio.sleep(5)
                
    async def _monitor_node_health(self):
        """Monitor node health with AI readiness tracking"""
        while self.running:
            try:
                nodes = registry.get_all_nodes()
                
                for node in nodes:
                    if node.get("status") == "online":
                        health_data = await self._get_node_health(node)
                        if health_data:
                            registry.update_node_health(node["id"], health_data)
                            
                            # Update AI readiness cache
                            if "ai_compute_readiness" in health_data:
                                self.ai_readiness_cache[node["id"]] = (
                                    health_data["ai_compute_readiness"], 
                                    time.time()
                                )
                            
                await asyncio.sleep(30)
                
            except Exception as e:
                logger.error(f"Error monitoring laptop node health: {e}")
                await asyncio.sleep(60)
                
    async def _cleanup_readiness_cache(self):
        """Clean up expired AI readiness cache entries"""
        while self.running:
            try:
                current_time = time.time()
                expired_nodes = [
                    node_id for node_id, (_, cached_time) in self.ai_readiness_cache.items()
                    if current_time - cached_time > self.readiness_cache_ttl
                ]
                
                for node_id in expired_nodes:
                    del self.ai_readiness_cache[node_id]
                    logger.debug(f"Cleaned up expired AI readiness cache for node {node_id}")
                
                await asyncio.sleep(60)  # Cleanup every minute
                
            except Exception as e:
                logger.error(f"Error cleaning up AI readiness cache: {e}")
                await asyncio.sleep(120)
                
    async def _get_node_health(self, node: Dict) -> Optional[Dict]:
        """Get comprehensive node health including AI readiness"""
        try:
            node_url = f"http://{node['host']}:{node['port']}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{node_url}/health/detailed",
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as response:
                    if response.status == 200:
                        return await response.json()
                        
        except Exception as e:
            logger.debug(f"Failed to get health for laptop node {node['id']}: {e}")
            
        return None
        
    def get_scheduler_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics for monitoring"""
        return {
            "running": self.running,
            "task_assignments": len(self.task_assignments),
            "ai_readiness_cache_size": len(self.ai_readiness_cache),
            "cached_nodes": list(self.ai_readiness_cache.keys()),
            "active_tasks": [
                task_id for task_id in self.task_assignments.keys()
                if registry.get_task(task_id) and registry.get_task(task_id).get("status") == "running"
            ]
        }

distributed_scheduler = DistributedScheduler()