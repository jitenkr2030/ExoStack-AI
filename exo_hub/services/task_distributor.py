"""
Task Distribution Service for coordinating distributed model execution
"""
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from .distributed_executor import DistributedExecutor
from .registry import Registry
from .metrics_collector import MetricsCollector
from ..models import TaskStatus

logger = logging.getLogger(__name__)

class TaskDistributor:
    def __init__(self):
        self.executor = DistributedExecutor()
        self.registry = Registry()
        self.metrics_collector = MetricsCollector()
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self._task_locks: Dict[str, asyncio.Lock] = {}

    async def distribute_task(
        self,
        task_id: str,
        model_name: str,
        input_data: Dict[str, Any],
        distribution_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Distribute and execute a task across available nodes
        """
        try:
            # Initialize task tracking
            self.active_tasks[task_id] = {
                "status": TaskStatus.PENDING,
                "start_time": datetime.now(),
                "model_name": model_name,
                "distribution_config": distribution_config or {}
            }
            self._task_locks[task_id] = asyncio.Lock()

            # Prepare model distribution if not already distributed
            if model_name not in self.executor.model_shards:
                model_config = await self._get_model_config(model_name)
                shards = await self.executor.prepare_model_distribution(
                    model_name,
                    model_config
                )
                distribution_plan = await self.executor.distribute_model(
                    model_name,
                    shards
                )
                logger.info(
                    f"Model {model_name} distributed across "
                    f"{len(distribution_plan)} nodes"
                )

            # Execute the distributed task
            self.active_tasks[task_id]["status"] = TaskStatus.RUNNING
            result = await self.executor.execute_distributed(
                task_id,
                model_name,
                input_data
            )

            # Update task status
            self.active_tasks[task_id].update({
                "status": TaskStatus.COMPLETED,
                "end_time": datetime.now(),
                "result": result
            })

            # Record metrics
            await self._record_task_metrics(task_id)

            return result

        except Exception as e:
            logger.error(f"Error distributing task {task_id}: {e}")
            if task_id in self.active_tasks:
                self.active_tasks[task_id]["status"] = TaskStatus.FAILED
                self.active_tasks[task_id]["error"] = str(e)
            raise

    async def get_task_status(
        self,
        task_id: str
    ) -> Dict[str, Any]:
        """
        Get current status of a distributed task
        """
        if task_id not in self.active_tasks:
            raise ValueError(f"Task {task_id} not found")

        task_info = self.active_tasks[task_id].copy()
        if "result" in task_info:
            task_info["result"] = {
                "status": "completed",
                "output_size": len(task_info["result"].get("output", "")),
                "metrics": task_info["result"].get("metrics", {})
            }

        return task_info

    async def cancel_task(
        self,
        task_id: str
    ) -> Dict[str, Any]:
        """
        Cancel a running distributed task
        """
        if task_id not in self.active_tasks:
            raise ValueError(f"Task {task_id} not found")

        async with self._task_locks[task_id]:
            if self.active_tasks[task_id]["status"] == TaskStatus.RUNNING:
                # Implement task cancellation logic here
                self.active_tasks[task_id]["status"] = TaskStatus.CANCELLED
                self.active_tasks[task_id]["end_time"] = datetime.now()

        return {"status": "cancelled", "task_id": task_id}

    async def _get_model_config(
        self,
        model_name: str
    ) -> Dict[str, Any]:
        """
        Get model configuration for distribution
        """
        # This would typically come from a model registry or configuration service
        # For now, using a simple example configuration
        return {
            "model_size": 8000,  # MB
            "memory_per_shard": 4000,  # MB
            "gpu_required": True,
            "min_nodes": 2,
            "max_nodes": 8
        }

    async def _record_task_metrics(
        self,
        task_id: str
    ):
        """
        Record metrics for completed task
        """
        task_info = self.active_tasks[task_id]
        if task_info["status"] != TaskStatus.COMPLETED:
            return

        metrics = {
            "task_id": task_id,
            "model_name": task_info["model_name"],
            "execution_time": (
                task_info["end_time"] - task_info["start_time"]
            ).total_seconds(),
            "status": task_info["status"],
            "result_metrics": task_info.get("result", {}).get("metrics", {})
        }

        self.metrics_collector.record_metrics(task_id, metrics)

    async def cleanup_task(
        self,
        task_id: str
    ):
        """
        Clean up resources for a completed task
        """
        if task_id in self.active_tasks:
            async with self._task_locks[task_id]:
                if task_id in self._task_locks:
                    del self._task_locks[task_id]
                if task_id in self.active_tasks:
                    del self.active_tasks[task_id]
