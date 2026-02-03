"""
Kubernetes Deployment Tests
"""
import pytest
from kubernetes import client, config
from exo_cli.deployment import DeploymentManager

class TestKubernetesDeployment:
    @pytest.fixture
    def setup_k8s(self):
        """Setup Kubernetes test environment"""
        config.load_kube_config()
        self.k8s_apps_v1 = client.AppsV1Api()
        self.k8s_core_v1 = client.CoreV1Api()

    def test_statefulset_deployment(self, setup_k8s):
        """Test StatefulSet deployment"""
        deployment_manager = DeploymentManager({
            'namespace': 'test-namespace',
            'components': [{
                'name': 'test-model',
                'replicas': 2,
                'image': 'test-image:latest'
            }]
        })

        # Deploy
        result = deployment_manager.deploy()
        assert result.success
        
        # Verify deployment
        statefulset = self.k8s_apps_v1.read_namespaced_stateful_set(
            name='test-model',
            namespace='test-namespace'
        )
        assert statefulset.spec.replicas == 2

    def test_persistent_volume_creation(self, setup_k8s):
        """Test PV and PVC creation"""
        deployment_manager = DeploymentManager({
            'namespace': 'test-namespace',
            'storage': {
                'size': '10Gi',
                'class': 'standard'
            }
        })

        # Deploy
        result = deployment_manager.deploy()
        assert result.success
        
        # Verify PVC
        pvc = self.k8s_core_v1.read_namespaced_persistent_volume_claim(
            name='test-model-pvc',
            namespace='test-namespace'
        )
        assert pvc.spec.resources.requests['storage'] == '10Gi'

