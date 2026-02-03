"""
P2P Handoff Manager for coordinating distributed inference
"""
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from .p2p_handoff import P2PHandoff, HandoffRequest, HandoffStatus
from .node_discovery import NodeDiscovery, NodeInfo
from ..models import Node, NodeStatus, TaskStatus

logger = logging.getLogger(__name__)

class HandoffManager:
    def __init__(self):
        self.p2p_handoff = P2PHandoff()
        self.node_discovery = NodeDiscovery()
        self._active_handoffs: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def start(self):
        """Start the handoff manager services"""
        await self.p2p_handoff.start()
        await self.node_discovery.start()
        logger.info("Handoff manager started")

    async def stop(self):
        """Stop the handoff manager services"""
        await self.p2p_handoff.stop()
        await self.node_discovery.stop()
        logger.info("Handoff manager stopped")

    async def handle_overload(
        self,
        node_id: str,
        task_id: str,
        model_name: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle node overload by redistributing task
        """
        try:
            # Find suitable target node
            target_node = await self._find_best_target_node(
                source_node_id=node_id,
                model_name=model_name
            )

            if not target_node:
                raise ValueError("No suitable target node found for handoff")

            # Create handoff request
            request = HandoffRequest(
                task_id=task_id,
                source_node_id=node_id,
                target_node_id=target_node.node_id,
                model_name=model_name,
                input_data=input_data,
                priority=2  # Higher priority for overload handling
            )

            # Initiate handoff
            response = await self.p2p_handoff.initiate_handoff(request)
            
            async with self._lock:
                self._active_handoffs[task_id] = {
                    "handoff_id": response.handoff_id,
                    "status": response.status,
                    "timestamp": datetime.now(),
                    "source_node": node_id,
                    "target_node": target_node.node_id
                }

            return {
                "status": response.status,
                "handoff_id": response.handoff_id,
                "target_node": target_node.node_id,
                "result": response.result if response.status == HandoffStatus.COMPLETED else None
            }

        except Exception as e:
            logger.error(f"Error handling overload for task {task_id}: {e}")
            raise

    async def coordinate_handoff(
        self,
        task_id: str,
        model_name: str,
        input_data: Dict[str, Any],
        source_node_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Coordinate task handoff between nodes
        """
        try:
            # Find source and target nodes
            source_node, target_node = await self._find_handoff_pair(
                model_name,
                source_node_id
            )

            if not source_node or not target_node:
                raise ValueError("Could not find suitable nodes for handoff")

            # Create and initiate handoff
            request = HandoffRequest(
                task_id=task_id,
                source_node_id=source_node.node_id,
                target_node_id=target_node.node_id,
                model_name=model_name,
                input_data=input_data
            )

            response = await self.p2p_handoff.initiate_handoff(request)
            
            # Track handoff
            async with self._lock:
                self._active_handoffs[task_id] = {
                    "handoff_id": response.handoff_id,
                    "status": response.status,
                    "timestamp": datetime.now(),
                    "source_node": source_node.node_id,
                    "target_node": target_node.node_id
                }

            return {
                "status": response.status,
                "handoff_id": response.handoff_id,
                "source_node": source_node.node_id,
                "target_node": target_node.node_id,
                "result": response.result if response.status == HandoffStatus.COMPLETED else None
            }

        except Exception as e:
            logger.error(f"Error coordinating handoff for task {task_id}: {e}")
            raise

    async def get_handoff_status(
        self,
        task_id: str
    ) -> Dict[str, Any]:
        """
        Get status of an active handoff
        """
        async with self._lock:
            if task_id not in self._active_handoffs:
                raise ValueError(f"No active handoff found for task {task_id}")
            return self._active_handoffs[task_id]

    async def _find_best_target_node(
        self,
        source_node_id: str,
        model_name: str
    ) -> Optional[NodeInfo]:
        """
        Find the best target node for handoff
        """
        # Get available nodes
        available_nodes = await self.node_discovery.get_available_nodes({
            "model_support": model_name,
            "status": NodeStatus.ONLINE
        })

        if not available_nodes:
            return None

        # Filter out source node and sort by capacity
        candidates = [
            node for node in available_nodes
            if node.node_id != source_node_id
        ]

        if not candidates:
            return None

        # Sort by available capacity and connection quality
        sorted_candidates = sorted(
            candidates,
            key=lambda n: (
                n.capabilities.get("available_memory", 0),
                -len(self.p2p_handoff.node_connections.get(n.node_id, set())),
                n.capabilities.get("gpu_memory", 0) if n.capabilities.get("gpu_available", False) else 0
            ),
            reverse=True
        )

        return sorted_candidates[0] if sorted_candidates else None

    async def _find_handoff_pair(
        self,
        model_name: str,
        preferred_source: Optional[str] = None
    ) -> Tuple[Optional[NodeInfo], Optional[NodeInfo]]:
        """
        Find suitable source and target nodes for handoff
        """
        available_nodes = await self.node_discovery.get_available_nodes({
            "model_support": model_name,
            "status": NodeStatus.ONLINE
        })

        if len(available_nodes) < 2:
            return None, None

        # Find source node
        source_node = None
        if preferred_source:
            source_node = next(
                (n for n in available_nodes if n.node_id == preferred_source),
                None
            )

        if not source_node:
            # Select node with highest capacity as source
            source_node = max(
                available_nodes,
                key=lambda n: n.capabilities.get("available_memory", 0)
            )

        # Find target node
        target_candidates = [
            n for n in available_nodes
            if n.node_id != source_node.node_id
        ]

        if not target_candidates:
            return None, None

        # Select best target based on capacity and connection quality
        target_node = max(
            target_candidates,
            key=lambda n: (
                n.capabilities.get("available_memory", 0),
                -len(self.p2p_handoff.node_connections.get(n.node_id, set())),
                n.capabilities.get("gpu_memory", 0) if n.capabilities.get("gpu_available", False) else 0
            )
        )

        return source_node, target_node

    async def cleanup_handoff(
        self,
        task_id: str
    ):
        """
        Clean up completed or failed handoff
        """
        async with self._lock:
            if task_id in self._active_handoffs:
                handoff_info = self._active_handoffs[task_id]
                if handoff_info["status"] in [
                    HandoffStatus.COMPLETED,
                    HandoffStatus.FAILED,
                    HandoffStatus.CANCELLED
                ]:
                    del self._active_handoffs[task_id]