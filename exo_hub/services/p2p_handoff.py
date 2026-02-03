"""
P2P Handoff Service for distributed inference coordination
"""

import asyncio
import logging
import json
import time
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import aiohttp
from pydantic import BaseModel
from ..models import Node, NodeStatus, TaskStatus

logger = logging.getLogger(__name__)

class HandoffStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class HandoffRequest(BaseModel):
    task_id: str
    source_node_id: str
    target_node_id: str
    model_name: str
    input_data: Dict[str, Any]
    priority: int = 1
    timeout: int = 300  # seconds

class HandoffResponse(BaseModel):
    handoff_id: str
    status: HandoffStatus
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None

@dataclass
class HandoffSession:
    handoff_id: str
    request: HandoffRequest
    status: HandoffStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retries: int = 0
    max_retries: int = 3

class P2PHandoff:
    def __init__(self):
        self.active_sessions: Dict[str, HandoffSession] = {}
        self.node_connections: Dict[str, Set[str]] = {}  # node_id -> connected_nodes
        self.session_locks: Dict[str, asyncio.Lock] = {}
        self._cleanup_task: Optional[asyncio.Task] = None
        self.http_session: Optional[aiohttp.ClientSession] = None

    async def start(self):
        """Initialize P2P handoff service"""
        self.http_session = aiohttp.ClientSession()
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())
        logger.info("P2P Handoff service started")

    async def stop(self):
        """Shutdown P2P handoff service"""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        if self.http_session:
            await self.http_session.close()
        logger.info("P2P Handoff service stopped")

    async def initiate_handoff(
        self,
        request: HandoffRequest
    ) -> HandoffResponse:
        """
        Initiate a P2P handoff between nodes
        """
        handoff_id = f"handoff_{request.task_id}_{int(time.time())}"
        self.session_locks[handoff_id] = asyncio.Lock()

        session = HandoffSession(
            handoff_id=handoff_id,
            request=request,
            status=HandoffStatus.PENDING,
            start_time=datetime.now()
        )

        async with self.session_locks[handoff_id]:
            self.active_sessions[handoff_id] = session

            try:
                # Verify node connectivity
                if not await self._verify_node_connection(
                    request.source_node_id,
                    request.target_node_id
                ):
                    raise ValueError("Nodes are not connected")

                # Start handoff process
                session.status = HandoffStatus.IN_PROGRESS
                result = await self._execute_handoff(session)
                
                return HandoffResponse(
                    handoff_id=handoff_id,
                    status=HandoffStatus.COMPLETED,
                    result=result
                )

            except Exception as e:
                logger.error(f"Handoff {handoff_id} failed: {e}")
                session.status = HandoffStatus.FAILED
                session.error = str(e)
                
                # Attempt fallback
                try:
                    fallback_result = await self._handle_fallback(session)
                    if fallback_result:
                        return HandoffResponse(
                            handoff_id=handoff_id,
                            status=HandoffStatus.COMPLETED,
                            result=fallback_result,
                            metrics={"fallback_used": True}
                        )
                except Exception as fallback_error:
                    logger.error(f"Fallback for {handoff_id} failed: {fallback_error}")

                return HandoffResponse(
                    handoff_id=handoff_id,
                    status=HandoffStatus.FAILED,
                    error=str(e)
                )

    async def _execute_handoff(
        self,
        session: HandoffSession
    ) -> Dict[str, Any]:
        """
        Execute the actual handoff process
        """
        request = session.request
        target_url = f"http://{request.target_node_id}/handoff"

        async with self.http_session.post(
            target_url,
            json=request.dict()
        ) as response:
            if response.status != 200:
                raise ValueError(
                    f"Handoff request failed with status {response.status}"
                )
            
            result = await response.json()
            session.result = result
            session.end_time = datetime.now()
            return result

    async def _handle_fallback(
        self,
        session: HandoffSession
    ) -> Optional[Dict[str, Any]]:
        """
        Implement fallback mechanism for failed handoffs
        """
        if session.retries >= session.max_retries:
            logger.error(f"Max retries exceeded for handoff {session.handoff_id}")
            return None

        session.retries += 1
        logger.info(
            f"Attempting fallback for handoff {session.handoff_id}, "
            f"retry {session.retries}"
        )

        # Try alternative nodes
        alternative_nodes = await self._find_alternative_nodes(
            session.request.model_name,
            exclude_nodes=[
                session.request.source_node_id,
                session.request.target_node_id
            ]
        )

        for node_id in alternative_nodes:
            try:
                modified_request = session.request.copy()
                modified_request.target_node_id = node_id
                
                result = await self._execute_handoff(
                    HandoffSession(
                        handoff_id=f"{session.handoff_id}_fallback_{session.retries}",
                        request=modified_request,
                        status=HandoffStatus.PENDING,
                        start_time=datetime.now()
                    )
                )
                
                return result
            except Exception as e:
                logger.warning(
                    f"Fallback to node {node_id} failed: {e}, trying next node"
                )

        return None

    async def _verify_node_connection(
        self,
        source_node: str,
        target_node: str
    ) -> bool:
        """
        Verify P2P connection between nodes
        """
        if source_node not in self.node_connections:
            self.node_connections[source_node] = set()
        if target_node not in self.node_connections:
            self.node_connections[target_node] = set()

        # Check direct connection
        if target_node in self.node_connections[source_node]:
            return True

        # Attempt to establish connection
        try:
            await self._establish_connection(source_node, target_node)
            return True
        except Exception as e:
            logger.error(f"Failed to establish connection: {e}")
            return False

    async def _establish_connection(
        self,
        source_node: str,
        target_node: str
    ):
        """
        Establish P2P connection between nodes
        """
        # Implement connection establishment protocol
        source_url = f"http://{source_node}/connect"
        target_url = f"http://{target_node}/connect"

        async with self.http_session.post(
            source_url,
            json={"peer_node": target_node}
        ) as response:
            if response.status != 200:
                raise ValueError("Source node connection failed")

        async with self.http_session.post(
            target_url,
            json={"peer_node": source_node}
        ) as response:
            if response.status != 200:
                raise ValueError("Target node connection failed")

        # Update connection registry
        self.node_connections[source_node].add(target_node)
        self.node_connections[target_node].add(source_node)

    async def _find_alternative_nodes(
        self,
        model_name: str,
        exclude_nodes: List[str]
    ) -> List[str]:
        """
        Find alternative nodes for fallback
        """
        # This would typically query a node registry or discovery service
        # For now, returning a simple example
        all_nodes = list(self.node_connections.keys())
        return [
            node for node in all_nodes
            if node not in exclude_nodes
        ]

    async def _cleanup_expired_sessions(self):
        """
        Periodically clean up expired sessions
        """
        while True:
            try:
                current_time = datetime.now()
                expired_sessions = []

                for session_id, session in self.active_sessions.items():
                    if (
                        session.status in [HandoffStatus.COMPLETED, HandoffStatus.FAILED]
                        and (current_time - session.start_time).total_seconds() > 3600
                    ):
                        expired_sessions.append(session_id)

                for session_id in expired_sessions:
                    async with self.session_locks.get(session_id, asyncio.Lock()):
                        self.active_sessions.pop(session_id, None)
                        self.session_locks.pop(session_id, None)

                await asyncio.sleep(300)  # Clean up every 5 minutes
            except Exception as e:
                logger.error(f"Error in session cleanup: {e}")
                await asyncio.sleep(60)  # Retry after 1 minute on error