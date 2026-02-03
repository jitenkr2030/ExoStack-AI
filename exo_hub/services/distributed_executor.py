"""
Distributed Model Execution Service
Handles model sharding, distribution, and execution coordination
"""
import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import numpy as np
from pydantic import BaseModel
from ..models import Node, TaskStatus
from .registry import Registry
from .scheduler import TaskScheduler
from .metrics_collector import MetricsCollector

logger = logging.getLogger(__name__)

class ModelShard(BaseModel):
    """Model shard configuration"""
    shard_id: str
    model_name: str
    shard_size: int
    memory_required: int
    gpu_required: bool
    node_id: Optional[str] = None
    status: str = "unassigned"

class ExecutionMetrics(BaseModel):
    """Execution performance metrics"""
    start_time: datetime
    end_time: Optional[datetime] = None
    processing_time: Optional[float] = None
    input_tokens: int = 0
    output_tokens: int = 0
    memory_used: float = 0
    gpu_memory_used: Optional[float] = None

class DistributedExecutor:
    def __init__(self):
        self.registry = Registry()
        self.scheduler = TaskScheduler()
        self.metrics_collector = MetricsCollector()
        self.model_shards: Dict[str, List[ModelShard]] = {}
        self.execution_metrics: Dict[str, ExecutionMetrics] = {}
        self._shard_locks: Dict[str, asyncio.Lock] = {}

    async def prepare_model_distribution(
        self,
        model_name: str,
        model_config: Dict[str, Any]
    ) -> List[ModelShard]:
        """
        Prepare model for distributed execution by creating shards
        """
        total_size = model_config.get("model_size", 0)
        memory_per_shard = model_config.get("memory_per_shard", 4000)  # MB
        gpu_required = model_config.get("gpu_required", True)

        # Calculate optimal number of shards based on available nodes
        available_nodes = self.registry.get_available_nodes(
            gpu_required=gpu_required,
            min_memory=memory_per_shard
        )

        if not available_nodes:
            raise ValueError("No suitable nodes available for model distribution")

        optimal_shard_count = min(
            len(available_nodes),
            max(1, total_size // memory_per_shard)
        )

        # Create shards
        shards = []
        for i in range(optimal_shard_count):
            shard = ModelShard(
                shard_id=f"{model_name}_shard_{i}",
                model_name=model_name,
                shard_size=total_size // optimal_shard_count,
                memory_required=memory_per_shard,
                gpu_required=gpu_required
            )
            shards.append(shard)

        self.model_shards[model_name] = shards
        return shards

    async def distribute_model(
        self,
        model_name: str,
        shards: List[ModelShard]
    ) -> Dict[str, Any]:
        """
        Distribute model shards across available nodes
        """
        distribution_plan = {}
        available_nodes = self.registry.get_available_nodes(
            gpu_required=shards[0].gpu_required,
            min_memory=shards[0].memory_required
        )

        if len(available_nodes) < len(shards):
            raise ValueError(
                f"Insufficient nodes ({len(available_nodes)}) "
                f"for shard distribution ({len(shards)})"
            )

        # Sort nodes by available resources
        nodes_by_resources = self._sort_nodes_by_resources(available_nodes)

        # Distribute shards to nodes
        for shard, node in zip(shards, nodes_by_resources):
            distribution_plan[shard.shard_id] = {
                "node_id": node.id,
                "shard": shard.dict(),
                "status": "pending"
            }
            shard.node_id = node.id
            shard.status = "assigned"

        return distribution_plan

    async def execute_distributed(
        self,
        task_id: str,
        model_name: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a task across distributed model shards
        """
        if model_name not in self.model_shards:
            raise ValueError(f"Model {model_name} not distributed")

        shards = self.model_shards[model_name]
        execution_plan = await self._create_execution_plan(task_id, shards, input_data)
        
        # Initialize execution metrics
        self.execution_metrics[task_id] = ExecutionMetrics(
            start_time=datetime.now(),
            input_tokens=len(input_data.get("input", "").split())
        )

        try:
            # Execute shards in parallel
            results = await asyncio.gather(*[
                self._execute_shard(
                    task_id,
                    shard,
                    execution_plan[shard.shard_id]
                )
                for shard in shards
            ])

            # Combine results
            combined_result = await self._combine_shard_results(results)
            
            # Update metrics
            await self._update_execution_metrics(task_id, combined_result)
            
            return combined_result

        except Exception as e:
            logger.error(f"Error in distributed execution: {e}")
            raise

    async def _create_execution_plan(
        self,
        task_id: str,
        shards: List[ModelShard],
        input_data: Dict[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Create execution plan for distributed processing
        """
        plan = {}
        input_text = input_data.get("input", "")
        
        # Simple text-based sharding for demonstration
        # In practice, use more sophisticated sharding based on model architecture
        tokens = input_text.split()
        tokens_per_shard = max(1, len(tokens) // len(shards))

        for i, shard in enumerate(shards):
            start_idx = i * tokens_per_shard
            end_idx = start_idx + tokens_per_shard if i < len(shards) - 1 else len(tokens)
            
            plan[shard.shard_id] = {
                "input_segment": " ".join(tokens[start_idx:end_idx]),
                "position": i,
                "total_shards": len(shards),
                "parameters": input_data.get("parameters", {})
            }

        return plan

    async def _execute_shard(
        self,
        task_id: str,
        shard: ModelShard,
        shard_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a single model shard
        """
        if not shard.node_id:
            raise ValueError(f"Shard {shard.shard_id} not assigned to any node")

        node = self.registry.get_node(shard.node_id)
        if not node:
            raise ValueError(f"Node {shard.node_id} not found")

        # Create shard-specific task
        shard_task = {
            "task_id": f"{task_id}_shard_{shard.shard_id}",
            "model_name": shard.model_name,
            "input_data": shard_plan,
            "shard_info": shard.dict()
        }

        # Schedule task execution on node
        result = await self.scheduler.schedule_task(shard_task, node)
        
        # Monitor execution
        await self._monitor_shard_execution(task_id, shard, result)
        
        return result

    async def _monitor_shard_execution(
        self,
        task_id: str,
        shard: ModelShard,
        result: Dict[str, Any]
    ):
        """
        Monitor and collect metrics for shard execution
        """
        metrics = {
            "shard_id": shard.shard_id,
            "node_id": shard.node_id,
            "execution_time": result.get("execution_time", 0),
            "memory_used": result.get("memory_used", 0),
            "gpu_memory_used": result.get("gpu_memory_used", 0)
        }
        
        self.metrics_collector.record_metrics(shard.node_id, metrics)

    async def _combine_shard_results(
        self,
        shard_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Combine results from all shards
        """
        # Sort results by position to maintain order
        sorted_results = sorted(
            shard_results,
            key=lambda x: x.get("position", 0)
        )

        combined_output = ""
        total_tokens = 0
        max_memory_used = 0
        total_time = 0

        for result in sorted_results:
            combined_output += result.get("output", "")
            total_tokens += result.get("output_tokens", 0)
            max_memory_used = max(
                max_memory_used,
                result.get("memory_used", 0)
            )
            total_time = max(total_time, result.get("execution_time", 0))

        return {
            "output": combined_output.strip(),
            "metrics": {
                "total_tokens": total_tokens,
                "max_memory_used": max_memory_used,
                "total_execution_time": total_time
            }
        }

    async def _update_execution_metrics(
        self,
        task_id: str,
        result: Dict[str, Any]
    ):
        """
        Update execution metrics for the task
        """
        if task_id in self.execution_metrics:
            metrics = self.execution_metrics[task_id]
            metrics.end_time = datetime.now()
            metrics.processing_time = (
                metrics.end_time - metrics.start_time
            ).total_seconds()
            metrics.output_tokens = result["metrics"]["total_tokens"]
            metrics.memory_used = result["metrics"]["max_memory_used"]

    def _sort_nodes_by_resources(self, nodes: List[Node]) -> List[Node]:
        """
        Sort nodes by available resources for optimal distribution
        """
        return sorted(
            nodes,
            key=lambda n: (
                n.capabilities.gpu_memory if n.capabilities else 0,
                n.capabilities.memory if n.capabilities else 0,
                -n.current_load
            ),
            reverse=True
        )
