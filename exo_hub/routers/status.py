"""
Enhanced status endpoints for health monitoring
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from ..models import NodeStatus
from ..services.metrics_collector import MetricsCollector
from ..services.registry import Registry

router = APIRouter(prefix="/status")

@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@router.get("/system")
async def system_status() -> Dict[str, Any]:
    """Get detailed system status including all nodes"""
    try:
        registry = Registry()
        metrics_collector = MetricsCollector()

        nodes = registry.get_all_nodes()
        system_metrics = metrics_collector.get_system_metrics()

        return {
            "timestamp": datetime.now().isoformat(),
            "nodes": {
                "total": len(nodes),
                "online": sum(1 for node in nodes if node.status == NodeStatus.ONLINE),
                "offline": sum(1 for node in nodes if node.status == NodeStatus.OFFLINE),
                "error": sum(1 for node in nodes if node.status == NodeStatus.ERROR)
            },
            "system_metrics": system_metrics,
            "overall_status": _calculate_overall_status(nodes)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching system status: {str(e)}")

@router.get("/nodes/{node_id}/health")
async def node_health(node_id: str) -> Dict[str, Any]:
    """Get detailed health information for a specific node"""
    try:
        registry = Registry()
        node = registry.get_node(node_id)
        if not node:
            raise HTTPException(status_code=404, detail=f"Node {node_id} not found")

        metrics_collector = MetricsCollector()
        node_metrics = metrics_collector.get_node_metrics(node_id)

        return {
            "node_id": node_id,
            "status": node.status,
            "last_heartbeat": node.last_heartbeat,
            "uptime": _calculate_uptime(node.registered_at),
            "health_metrics": node_metrics,
            "capabilities": node.capabilities.dict() if node.capabilities else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching node health: {str(e)}")

@router.get("/metrics")
async def get_metrics(
    node_id: Optional[str] = None,
    metric_type: Optional[str] = None,
    time_range: Optional[int] = Query(default=3600, description="Time range in seconds")
) -> Dict[str, Any]:
    """Get historical metrics with optional filtering"""
    try:
        metrics_collector = MetricsCollector()
        from_time = datetime.now() - timedelta(seconds=time_range)

        metrics = metrics_collector.get_historical_metrics(
            node_id=node_id,
            metric_type=metric_type,
            from_time=from_time
        )

        return {
            "timestamp": datetime.now().isoformat(),
            "time_range": time_range,
            "metrics": metrics
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching metrics: {str(e)}")

@router.get("/alerts")
async def get_alerts(
    severity: Optional[str] = None,
    node_id: Optional[str] = None,
    limit: int = Query(default=100, le=1000)
) -> List[Dict[str, Any]]:
    """Get system alerts with optional filtering"""
    try:
        metrics_collector = MetricsCollector()
        alerts = metrics_collector.get_alerts(
            severity=severity,
            node_id=node_id,
            limit=limit
        )
        return alerts
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching alerts: {str(e)}")

def _calculate_overall_status(nodes: List[Any]) -> str:
    """Calculate overall system status based on node health"""
    if not nodes:
        return "unknown"

    online_nodes = sum(1 for node in nodes if node.status == NodeStatus.ONLINE)
    error_nodes = sum(1 for node in nodes if node.status == NodeStatus.ERROR)
    total_nodes = len(nodes)

    if error_nodes > total_nodes * 0.2:  # More than 20% nodes in error
        return "critical"
    elif online_nodes < total_nodes * 0.5:  # Less than 50% nodes online
        return "warning"
    elif online_nodes == total_nodes:  # All nodes online
        return "healthy"
    else:
        return "degraded"

def _calculate_uptime(start_time: Optional[datetime]) -> Optional[float]:
    """Calculate uptime in seconds"""
    if not start_time:
        return None
    return (datetime.now() - start_time).total_seconds()