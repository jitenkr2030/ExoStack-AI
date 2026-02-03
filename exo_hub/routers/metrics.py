from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from ..services.metrics_collector import metrics_collector
from ..services.logger import get_logger

router = APIRouter(prefix="/metrics", tags=["metrics"])
logger = get_logger(__name__)

@router.get("/system")
async def get_system_metrics() -> Dict[str, Any]:
    """Get overall system metrics."""
    try:
        return metrics_collector.get_system_metrics()
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system metrics")

@router.get("/tasks")
async def get_task_metrics(task_id: Optional[str] = None) -> Dict[str, Any]:
    """Get task metrics."""
    try:
        return metrics_collector.get_task_metrics(task_id)
    except Exception as e:
        logger.error(f"Error getting task metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get task metrics")

@router.get("/nodes")
async def get_node_metrics(node_id: Optional[str] = None) -> Dict[str, Any]:
    """Get node metrics."""
    try:
        return metrics_collector.get_node_metrics(node_id)
    except Exception as e:
        logger.error(f"Error getting node metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get node metrics")

@router.get("/events")
async def get_recent_events(limit: int = 100) -> Dict[str, Any]:
    """Get recent system events."""
    try:
        events = metrics_collector.get_recent_events(limit)
        return {"events": events, "count": len(events)}
    except Exception as e:
        logger.error(f"Error getting recent events: {e}")
        raise HTTPException(status_code=500, detail="Failed to get recent events")

@router.post("/cleanup")
async def cleanup_old_metrics(days: int = 7) -> Dict[str, str]:
    """Clean up old metrics."""
    try:
        metrics_collector.cleanup_old_metrics(days)
        return {"message": f"Cleaned up metrics older than {days} days"}
    except Exception as e:
        logger.error(f"Error cleaning up metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to cleanup metrics")