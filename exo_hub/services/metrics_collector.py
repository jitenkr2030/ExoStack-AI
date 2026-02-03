"""
Enhanced metrics collection service
"""

import logging
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
from threading import Lock
from collections import defaultdict
from ..models import Node, NodeStatus

logger = logging.getLogger(__name__)

class MetricsCollector:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(MetricsCollector, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._metrics_store = defaultdict(list)
        self._alerts_store = []
        self._lock = Lock()
        self._initialized = True
        self._alert_thresholds = {
            "cpu_usage": 80.0,
            "memory_usage": 85.0,
            "disk_usage": 90.0,
            "gpu_usage": 85.0
        }

    def record_metrics(self, node_id: str, metrics: Dict[str, Any]):
        """Record metrics for a node"""
        with self._lock:
            timestamp = datetime.now()
            metrics_entry = {
                "timestamp": timestamp,
                "node_id": node_id,
                **metrics
            }

            # Store metrics
            self._metrics_store[node_id].append(metrics_entry)

            # Cleanup old metrics (keep last 24 hours)
            cutoff_time = timestamp - timedelta(hours=24)
            self._metrics_store[node_id] = [
                m for m in self._metrics_store[node_id]
                if m["timestamp"] > cutoff_time
            ]

            # Check for alerts
            self._check_alerts(node_id, metrics)

    def get_system_metrics(self) -> Dict[str, Any]:
        """Get aggregated system metrics"""
        with self._lock:
            current_time = datetime.now()
            recent_metrics = defaultdict(list)

            # Aggregate recent metrics across all nodes
            for node_metrics in self._metrics_store.values():
                for metric in node_metrics:
                    if (current_time - metric["timestamp"]).total_seconds() <= 300:  # Last 5 minutes
                        for key, value in metric.items():
                            if isinstance(value, (int, float)) and key not in ["timestamp"]:
                                recent_metrics[key].append(value)

            # Calculate averages
            aggregated_metrics = {}
            for key, values in recent_metrics.items():
                if values:
                    aggregated_metrics[key] = {
                        "average": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values)
                    }

            return aggregated_metrics

    def get_node_metrics(self, node_id: str) -> Dict[str, Any]:
        """Get metrics for a specific node"""
        with self._lock:
            if node_id not in self._metrics_store:
                return {}

            node_metrics = self._metrics_store[node_id]
            if not node_metrics:
                return {}

            latest_metrics = node_metrics[-1]
            historical_metrics = self._calculate_historical_metrics(node_metrics)

            return {
                "current": latest_metrics,
                "historical": historical_metrics
            }

    def get_historical_metrics(
        self,
        node_id: Optional[str] = None,
        metric_type: Optional[str] = None,
        from_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get historical metrics with optional filtering"""
        with self._lock:
            metrics = []

            # Filter metrics based on parameters
            for node, node_metrics in self._metrics_store.items():
                if node_id and node != node_id:
                    continue

                for metric in node_metrics:
                    if from_time and metric["timestamp"] < from_time:
                        continue

                    if metric_type:
                        if metric_type in metric:
                            metrics.append({
                                "node_id": node,
                                "timestamp": metric["timestamp"],
                                metric_type: metric[metric_type]
                            })
                    else:
                        metrics.append({
                            "node_id": node,
                            "timestamp": metric["timestamp"],
                            **{k: v for k, v in metric.items() if k != "timestamp"}
                        })

            return {"metrics": metrics}

    def get_alerts(
        self,
        severity: Optional[str] = None,
        node_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Get system alerts with optional filtering"""
        with self._lock:
            filtered_alerts = self._alerts_store

            if severity:
                filtered_alerts = [a for a in filtered_alerts if a["severity"] == severity]
            if node_id:
                filtered_alerts = [a for a in filtered_alerts if a["node_id"] == node_id]

            return sorted(
                filtered_alerts,
                key=lambda x: x["timestamp"],
                reverse=True
            )[:limit]

    def _check_alerts(self, node_id: str, metrics: Dict[str, Any]):
        """Check metrics against thresholds and generate alerts"""
        for metric_name, threshold in self._alert_thresholds.items():
            if metric_name in metrics:
                value = metrics[metric_name]
                if value > threshold:
                    severity = "critical" if value > threshold + 10 else "warning"
                    self._add_alert(
                        node_id=node_id,
                        metric_name=metric_name,
                        value=value,
                        threshold=threshold,
                        severity=severity
                    )

    def _add_alert(
        self,
        node_id: str,
        metric_name: str,
        value: float,
        threshold: float,
        severity: str
    ):
        """Add a new alert to the alert store"""
        with self._lock:
            alert = {
                "timestamp": datetime.now(),
                "node_id": node_id,
                "metric_name": metric_name,
                "value": value,
                "threshold": threshold,
                "severity": severity
            }
            self._alerts_store.append(alert)

            # Keep only recent alerts (last 1000)
            if len(self._alerts_store) > 1000:
                self._alerts_store = self._alerts_store[-1000:]

    def _calculate_historical_metrics(self, metrics: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate historical metrics statistics"""
        if not metrics:
            return {}

        metric_types = set()
        for metric in metrics:
            metric_types.update(k for k, v in metric.items() 
                              if isinstance(v, (int, float)) and k != "timestamp")

        historical_stats = {}
        for metric_type in metric_types:
            values = [m[metric_type] for m in metrics if metric_type in m]
            if values:
                historical_stats[metric_type] = {
                    "average": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "current": values[-1]
                }

        return historical_stats

metrics_collector = MetricsCollector()