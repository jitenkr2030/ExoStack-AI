"""
Node Discovery Service for P2P network management
"""
import asyncio
import logging
import json
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
import aiohttp
from pydantic import BaseModel
from ..models import Node, NodeStatus

logger = logging.getLogger(__name__)

class NodeInfo(BaseModel):
    node_id: str
    host: str
    port: int
    capabilities: Dict[str, Any]
    last_seen: datetime
    status: NodeStatus = NodeStatus.OFFLINE

@dataclass
class DiscoveryConfig:
    discovery_interval: int = 30  # seconds
    node_timeout: int = 120  # seconds
    ping_timeout: float = 5.0  # seconds
    max_retries: int = 3

class NodeDiscovery:
    def __init__(self, config: Optional[DiscoveryConfig] = None):
        self.config = config or DiscoveryConfig()
        self.nodes: Dict[str, NodeInfo] = {}
        self.node_connections: Dict[str, Set[str]] = {}
        self._discovery_task: Optional[asyncio.Task] = None
        self.http_session: Optional[aiohttp.ClientSession] = None
        self._lock = asyncio.Lock()

    async def start(self):
        """Start node discovery service"""
        self.http_session = aiohttp.ClientSession()
        self._discovery_task = asyncio.create_task(self._run_discovery())
        logger.info("Node discovery service started")

    async def stop(self):
        """Stop node discovery service"""
        if self._discovery_task:
            self._discovery_task.cancel()
            try:
                await self._discovery_task
            except asyncio.CancelledError:
                pass

        if self.http_session:
            await self.http_session.close()
        logger.info("Node discovery service stopped")

    async def register_node(
        self,
        node_id: str,
        host: str,
        port: int,
        capabilities: Dict[str, Any]
    ) -> NodeInfo:
        """
        Register a new node in the discovery service
        """
        async with self._lock:
            node_info = NodeInfo(
                node_id=node_id,
                host=host,
                port=port,
                capabilities=capabilities,
                last_seen=datetime.now(),
                status=NodeStatus.ONLINE
            )
            self.nodes[node_id] = node_info
            self.node_connections[node_id] = set()
            
            # Initiate connection discovery
            await self._discover_connections(node_info)
            
            return node_info

    async def get_node_info(
        self,
        node_id: str
    ) -> Optional[NodeInfo]:
        """
        Get information about a specific node
        """
        return self.nodes.get(node_id)

    async def get_available_nodes(
        self,
        capabilities: Optional[Dict[str, Any]] = None
    ) -> List[NodeInfo]:
        """
        Get list of available nodes, optionally filtered by capabilities
        """
        available_nodes = [
            node for node in self.nodes.values()
            if node.status == NodeStatus.ONLINE
        ]

        if capabilities:
            return [
                node for node in available_nodes
                if self._matches_capabilities(node, capabilities)
            ]
        
        return available_nodes

    async def update_node_status(
        self,
        node_id: str,
        status: NodeStatus,
        capabilities: Optional[Dict[str, Any]] = None
    ):
        """
        Update node status and capabilities
        """
        async with self._lock:
            if node_id in self.nodes:
                node = self.nodes[node_id]
                node.status = status
                node.last_seen = datetime.now()
                if capabilities:
                    node.capabilities.update(capabilities)

    async def _run_discovery(self):
        """
        Run continuous node discovery process
        """
        while True:
            try:
                await self._discover_all_nodes()
                await self._update_node_statuses()
                await self._cleanup_stale_nodes()
                await asyncio.sleep(self.config.discovery_interval)
            except Exception as e:
                logger.error(f"Error in node discovery: {e}")
                await asyncio.sleep(5)  # Short delay on error

    async def _discover_all_nodes(self):
        """
        Discover and verify all nodes in the network
        """
        async with self._lock:
            for node_id, node in list(self.nodes.items()):
                try:
                    # Ping node
                    if await self._ping_node(node):
                        # Update connections
                        await self._discover_connections(node)
                    else:
                        node.status = NodeStatus.OFFLINE
                except Exception as e:
                    logger.warning(f"Error discovering node {node_id}: {e}")
                    node.status = NodeStatus.ERROR

    async def _discover_connections(
        self,
        node: NodeInfo
    ):
        """
        Discover P2P connections for a node
        """
        try:
            url = f"http://{node.host}:{node.port}/discover"
            async with self.http_session.get(
                url,
                timeout=self.config.ping_timeout
            ) as response:
                if response.status == 200:
                    connections = await response.json()
                    self.node_connections[node.node_id] = set(
                        connections.get("connected_nodes", [])
                    )
        except Exception as e:
            logger.warning(f"Error discovering connections for {node.node_id}: {e}")

    async def _ping_node(
        self,
        node: NodeInfo
    ) -> bool:
        """
        Ping a node to verify its availability
        """
        for _ in range(self.config.max_retries):
            try:
                url = f"http://{node.host}:{node.port}/ping"
                async with self.http_session.get(
                    url,
                    timeout=self.config.ping_timeout
                ) as response:
                    if response.status == 200:
                        node.last_seen = datetime.now()
                        return True
            except Exception as e:
                logger.debug(f"Ping failed for {node.node_id}: {e}")
            await asyncio.sleep(1)
        return False

    async def _update_node_statuses(self):
        """
        Update status of all nodes based on last seen timestamp
        """
        current_time = datetime.now()
        timeout = timedelta(seconds=self.config.node_timeout)

        async with self._lock:
            for node in self.nodes.values():
                if (current_time - node.last_seen) > timeout:
                    node.status = NodeStatus.OFFLINE

    async def _cleanup_stale_nodes(self):
        """
        Remove nodes that have been offline for too long
        """
        current_time = datetime.now()
        stale_timeout = timedelta(hours=24)  # Remove nodes offline for 24 hours
        
        async with self._lock:
            stale_nodes = [
                node_id for node_id, node in self.nodes.items()
                if (
                    node.status == NodeStatus.OFFLINE
                    and (current_time - node.last_seen) > stale_timeout
                )
            ]
            
            for node_id in stale_nodes:
                self.nodes.pop(node_id, None)
                self.node_connections.pop(node_id, None)

    def _matches_capabilities(
        self,
        node: NodeInfo,
        required_capabilities: Dict[str, Any]
    ) -> bool:
        """
        Check if node matches required capabilities
        """
        for key, value in required_capabilities.items():
            if key not in node.capabilities:
                return False
            if isinstance(value, (int, float)):
                if node.capabilities[key] < value:
                    return False
            elif node.capabilities[key] != value:
                return False
        return True
