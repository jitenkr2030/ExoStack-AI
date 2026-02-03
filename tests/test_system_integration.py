"""
System Integration Tests for ExoStack
"""
import pytest
import asyncio
from typing import Dict, Any
from exo_agent.health_monitor import HealthMonitor
from exo_hub.services.distributed_executor import DistributedExecutor
from exo_hub.services.p2p_handoff import P2PHandoff
from exo_hub.services.metrics_collector import MetricsCollector

class TestSystemIntegration:
    @pytest.fixture
    async def setup_system(self):
        """Setup test environment"""
        # Initialize components
        health_monitor = HealthMonitor()
        distributed_executor = DistributedExecutor()
        p2p_handoff = P2PHandoff()
        metrics_collector = MetricsCollector()

        # Start services
        await health_monitor.start_collection()
        await p2p_handoff.start()

        yield {
            'health_monitor': health_monitor,
            'distributed_executor': distributed_executor,
            'p2p_handoff': p2p_handoff,
            'metrics_collector': metrics_collector
        }

        # Cleanup
        await health_monitor.stop_collection()
        await p2p_handoff.stop()

    @pytest.mark.asyncio
    async def test_health_monitoring(self, setup_system):
        """Test health monitoring functionality"""
        health_monitor = setup_system['health_monitor']
        
        # Get health metrics
        health_data = await health_monitor.get_detailed_health()
        
        # Verify metrics
        assert 'system' in health_data
        assert 'resources' in health_data
        assert 'status' in health_data
        assert health_data['status'] in ['healthy', 'warning', 'critical']

    @pytest.mark.asyncio
    async def test_distributed_execution(self, setup_system):
        """Test distributed model execution"""
        executor = setup_system['distributed_executor']
        
        # Test model distribution
        model_config = {
            'model_name': 'test-model',
            'model_size': 1000,
            'memory_per_shard': 100
        }
        
        shards = await executor.prepare_model_distribution(
            'test-model',
            model_config
        )
        
        assert len(shards) > 0
        assert all(shard.model_name == 'test-model' for shard in shards)

    @pytest.mark.asyncio
    async def test_p2p_handoff(self, setup_system):
        """Test P2P handoff functionality"""
        p2p_handoff = setup_system['p2p_handoff']
        
        # Test handoff request
        request = {
            'task_id': 'test-task',
            'source_node_id': 'node-1',
            'target_node_id': 'node-2',
            'model_name': 'test-model',
            'input_data': {'text': 'test'}
        }
        
        response = await p2p_handoff.initiate_handoff(request)
        assert response.handoff_id is not None

    @pytest.mark.asyncio
    async def test_metrics_collection(self, setup_system):
        """Test metrics collection"""
        metrics_collector = setup_system['metrics_collector']
        
        # Record test metrics
        await metrics_collector.record_metrics('test-node', {
            'cpu_usage': 50.0,
            'memory_usage': 60.0,
            'gpu_usage': 30.0
        })
        
        # Get metrics
        metrics = await metrics_collector.get_node_metrics('test-node')
        assert metrics is not None
        assert 'current' in metrics

