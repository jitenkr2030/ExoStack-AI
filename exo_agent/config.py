# Import shared configuration
from shared.config.env import (
    AGENT_ID,
    HUB_URL,
    AGENT_HOST,
    AGENT_PORT,
    LOG_LEVEL,
    HEARTBEAT_INTERVAL,
    MAX_CONCURRENT_TASKS,
    TASK_TIMEOUT_SECONDS
)

"""
Enhanced agent configuration with monitoring settings
"""
import os
from typing import Dict, Any
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).parent.parent
CACHE_DIR = BASE_DIR / "cache"
LOG_DIR = BASE_DIR / "logs"

# Ensure directories exist
CACHE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Health monitoring configuration
HEALTH_MONITOR_CONFIG = {
    "collection_interval": float(os.getenv("HEALTH_COLLECTION_INTERVAL", "1.0")),
    "metrics_retention_hours": int(os.getenv("METRICS_RETENTION_HOURS", "24")),
    "max_samples": int(os.getenv("MAX_METRIC_SAMPLES", "100")),
    "alert_thresholds": {
        "cpu_usage": float(os.getenv("ALERT_THRESHOLD_CPU", "80.0")),
        "memory_usage": float(os.getenv("ALERT_THRESHOLD_MEMORY", "85.0")),
        "disk_usage": float(os.getenv("ALERT_THRESHOLD_DISK", "90.0")),
        "gpu_usage": float(os.getenv("ALERT_THRESHOLD_GPU", "85.0"))
    }
}

# Resource limits
RESOURCE_LIMITS = {
    "max_cpu_percent": float(os.getenv("MAX_CPU_PERCENT", "90.0")),
    "max_memory_percent": float(os.getenv("MAX_MEMORY_PERCENT", "85.0")),
    "max_gpu_percent": float(os.getenv("MAX_GPU_PERCENT", "85.0")),
    "min_free_disk_gb": float(os.getenv("MIN_FREE_DISK_GB", "10.0"))
}

# Monitoring endpoints
METRICS_ENDPOINT = os.getenv("METRICS_ENDPOINT", "http://localhost:8000/metrics")
HEALTH_CHECK_INTERVAL = int(os.getenv("HEALTH_CHECK_INTERVAL", "60"))
METRICS_REPORT_INTERVAL = int(os.getenv("METRICS_REPORT_INTERVAL", "30"))

# GPU monitoring settings
GPU_MONITORING_ENABLED = os.getenv("GPU_MONITORING_ENABLED", "true").lower() == "true"
GPU_METRICS_INTERVAL = float(os.getenv("GPU_METRICS_INTERVAL", "1.0"))

def get_monitoring_config() -> Dict[str, Any]:
    """Get complete monitoring configuration"""
    return {
        "health_monitor": HEALTH_MONITOR_CONFIG,
        "resource_limits": RESOURCE_LIMITS,
        "endpoints": {
            "metrics": METRICS_ENDPOINT,
            "health_check_interval": HEALTH_CHECK_INTERVAL,
            "metrics_report_interval": METRICS_REPORT_INTERVAL
        },
        "gpu": {
            "enabled": GPU_MONITORING_ENABLED,
            "metrics_interval": GPU_METRICS_INTERVAL
        }
    }