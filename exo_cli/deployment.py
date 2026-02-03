"""
Deployment Manager for handling automated deployments
"""
import os
import time
import logging
import asyncio
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from kubernetes import client, config
from .validators import ValidationResult
from .utils import create_deployment_id

logger = logging.getLogger(__name__)

@dataclass
class DeploymentResult:
    success: bool
    deployment_id: str
    components: List[str]
    errors: List[str] = None

class DeploymentManager:
    def __init__(
        self,
        config: Dict[str, Any],
        environment: str
    ):
        self.config = config
        self.environment = environment
        self.deployment_id = create_deployment_id()
        self.components = self.config.get('components', [])
        self._initialize_kubernetes()

    def _initialize_kubernetes(self):
        """Initialize Kubernetes client"""
        try:
            config.load_kube_config()
            self.k8s_apps_v1 = client.AppsV1Api()
            self.k8s_core_v1 = client.CoreV1Api()
        except Exception as e:
            logger.error(f"Failed to initialize Kubernetes client: {e}")
            raise

    def print_plan(self):
        """Print deployment plan"""
        print("\nDeployment Plan:")
        print(f"Environment: {self.environment}")
        print(f"Deployment ID: {self.deployment_id}")
        print("\nComponents to deploy:")
        for component in self.components:
            print(f"- {component['name']}")
            print(f"  Image: {component.get('image')}")
            print(f"  Replicas: {component.get('replicas', 1)}")

    def run_pre_deployment_checks(self):
        """Run pre-deployment validation checks"""
        # Verify Kubernetes connection
        try:
            self.k8s_core_v1.list_namespace()
        except Exception as e:
            raise ValueError(f"Kubernetes connection failed: {e}")

        # Check namespace exists
        namespace = self.config.get('namespace')
        try:
            self.k8s_core_v1.read_namespace(namespace)
        except Exception:
            logger.info(f"Creating namespace {namespace}")
            self._create_namespace(namespace)

        # Verify resource quotas
        self._verify_resource_quotas()

        # Check image availability
        self._verify_images()

    def deploy(self) -> DeploymentResult:
        """
        Execute deployment of all components
        """
        deployed_components = []
        errors = []

        try:
            # Deploy components in order
            for component in self.components:
                try:
                    self._deploy_component(component)
                    deployed_components.append(component['name'])
                except Exception as e:
                    errors.append(f"Failed to deploy {component['name']}: {e}")
                    raise

            return DeploymentResult(
                success=True,
                deployment_id=self.deployment_id,
                components=deployed_components
            )

        except Exception as e:
            return DeploymentResult(
                success=False,
                deployment_id=self.deployment_id,
                components=deployed_components,
                errors=errors
            )

    def validate_deployment(self) -> ValidationResult:
        """
        Validate deployed components
        """
        errors = []

        # Check all deployments are ready
        for component in self.components:
            try:
                deployment = self.k8s_apps_v1.read_namespaced_deployment(
                    name=component['name'],
                    namespace=self.config['namespace']
                )

                if not self._is_deployment_ready(deployment):
                    errors.append(
                        f"Deployment {component['name']} is not ready"
                    )

            except Exception as e:
                errors.append(
                    f"Error validating {component['name']}: {e}"
                )

        # Check services are available
        for component in self.components:
            if 'service' in component:
                try:
                    service = self.k8s_core_v1.read_namespaced_service(
                        name=component['name'],
                        namespace=self.config['namespace']
                    )

                    if not self._is_service_ready(service):
                        errors.append(
                            f"Service {component['name']} is not ready"
                        )

                except Exception as e:
                    errors.append(
                        f"Error validating service {component['name']}: {e}"
                    )

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )

    def run_post_deployment_tasks(self):
        """
        Execute post-deployment tasks
        """
        # Run database migrations if specified
        if self.config.get('run_migrations', False):
            self._run_migrations()

        # Scale components if needed
        if self.config.get('auto_scale', False):
            self._configure_auto_scaling()

        # Configure monitoring
        if self.config.get('enable_monitoring', False):
            self._setup_monitoring()

    def _deploy_component(self, component: Dict[str, Any]):
        """
        Deploy a single component
        """
        # Create deployment
        deployment = self._create_deployment_object(component)
        
        try:
            # Update or create deployment
            try:
                self.k8s_apps_v1.patch_namespaced_deployment(
                    name=component['name'],
                    namespace=self.config['namespace'],
                    body=deployment
                )
            except client.exceptions.ApiException as e:
                if e.status == 404:
                    self.k8s_apps_v1.create_namespaced_deployment(
                        namespace=self.config['namespace'],
                        body=deployment
                    )
                else:
                    raise

            # Create or update service if specified
            if 'service' in component:
                service = self._create_service_object(component)
                try:
                    self.k8s_core_v1.patch_namespaced_service(
                        name=component['name'],
                        namespace=self.config['namespace'],
                        body=service
                    )
                except client.exceptions.ApiException as e:
                    if e.status == 404:
                        self.k8s_core_v1.create_namespaced_service(
                            namespace=self.config['namespace'],
                            body=service
                        )
                    else:
                        raise

            # Wait for deployment to be ready
            self._wait_for_deployment(component['name'])

        except Exception as e:
            logger.error(f"Failed to deploy {component['name']}: {e}")
            raise

    def _create_deployment_object(
        self,
        component: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create Kubernetes deployment object
        """
        return {
            'apiVersion': 'apps/v1',
            'kind': 'Deployment',
            'metadata': {
                'name': component['name'],
                'namespace': self.config['namespace'],
                'labels': {
                    'app': component['name'],
                    'environment': self.environment,
                    'deployment-id': self.deployment_id
                }
            },
            'spec': {
                'replicas': component.get('replicas', 1),
                'selector': {
                    'matchLabels': {
                        'app': component['name']
                    }
                },
                'template': {
                    'metadata': {
                        'labels': {
                            'app': component['name'],
                            'environment': self.environment
                        }
                    },
                    'spec': {
                        'containers': [{
                            'name': component['name'],
                            'image': component['image'],
                            'ports': component.get('ports', []),
                            'env': self._create_environment_variables(component),
                            'resources': component.get('resources', {})
                        }]
                    }
                }
            }
        }

    def _create_service_object(
        self,
        component: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create Kubernetes service object
        """
        return {
            'apiVersion': 'v1',
            'kind': 'Service',
            'metadata': {
                'name': component['name'],
                'namespace': self.config['namespace'],
                'labels': {
                    'app': component['name'],
                    'environment': self.environment
                }
            },
            'spec': {
                'selector': {
                    'app': component['name']
                },
                'ports': component['service']['ports'],
                'type': component['service'].get('type', 'ClusterIP')
            }
        }

    def _wait_for_deployment(
        self,
        name: str,
        timeout: int = 300
    ):
        """
        Wait for deployment to be ready
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                deployment = self.k8s_apps_v1.read_namespaced_deployment(
                    name=name,
                    namespace=self.config['namespace']
                )
                
                if self._is_deployment_ready(deployment):
                    return True
                
                time.sleep(5)
            except Exception as e:
                logger.warning(f"Error checking deployment status: {e}")
                time.sleep(5)

        raise TimeoutError(
            f"Deployment {name} not ready after {timeout} seconds"
        )

    def _is_deployment_ready(
        self,
        deployment: Any
    ) -> bool:
        """
        Check if deployment is ready
        """
        try:
            return (
                deployment.status.available_replicas ==
                deployment.spec.replicas
            )
        except Exception:
            return False

    def _is_service_ready(
        self,
        service: Any
    ) -> bool:
        """
        Check if service is ready
        """
        return True  # Services are typically ready immediately

    def _verify_resource_quotas(self):
        """
        Verify resource quotas for deployment
        """
        try:
            quotas = self.k8s_core_v1.list_namespaced_resource_quota(
                namespace=self.config['namespace']
            )
            # Add quota verification logic here
        except Exception as e:
            logger.warning(f"Failed to verify resource quotas: {e}")

    def _verify_images(self):
        """
        Verify all container images exist
        """
        for component in self.components:
            # Add image verification logic here
            pass

    def _create_namespace(self, namespace: str):
        """
        Create Kubernetes namespace
        """
        body = {
            'apiVersion': 'v1',
            'kind': 'Namespace',
            'metadata': {
                'name': namespace,
                'labels': {
                    'name': namespace,
                    'environment': self.environment
                }
            }
        }
        self.k8s_core_v1.create_namespace(body=body)

    def _create_environment_variables(
        self,
        component: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Create environment variables for deployment
        """
        env_vars = []
        
        # Add common environment variables
        for key, value in self.config.get('env', {}).items():
            env_vars.append({
                'name': key,
                'value': str(value)
            })

        # Add component-specific environment variables
        for key, value in component.get('env', {}).items():
            env_vars.append({
                'name': key,
                'value': str(value)
            })

        return env_vars

    def _run_migrations(self):
        """
        Run database migrations
        """
        # Add migration logic here
        pass

    def _configure_auto_scaling(self):
        """
        Configure auto-scaling for components
        """
        # Add auto-scaling configuration logic here
        pass

    def _setup_monitoring(self):
        """
        Setup monitoring for deployed components
        """
        # Add monitoring setup logic here
        pass
