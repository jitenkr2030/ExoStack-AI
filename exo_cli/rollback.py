"""
Rollback Manager for handling deployment rollbacks
"""
import os
import json
import logging
import shutil
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from kubernetes import client, config

logger = logging.getLogger(__name__)

class RollbackManager:
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        environment: str = "development"
    ):
        self.config = config
        self.environment = environment
        self.backup_dir = Path(".exostack/backups")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
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

    def create_backup(self):
        """
        Create backup of current deployment state
        """
        try:
            # Get current state
            current_state = self._get_current_state()

            # Create backup file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"backup_{timestamp}.json"

            with open(backup_file, 'w') as f:
                json.dump({
                    'timestamp': timestamp,
                    'environment': self.environment,
                    'state': current_state
                }, f, indent=2)

            logger.info(f"Created backup: {backup_file}")
            return backup_file

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise

    def rollback(
        self,
        deployment_id: Optional[str] = None
    ):
        """
        Rollback to previous deployment state
        """
        try:
            # Get backup state
            backup_state = self._get_backup_state(deployment_id)
            if not backup_state:
                raise ValueError("No backup state found")

            # Perform rollback
            self._rollback_deployments(backup_state['deployments'])
            self._rollback_services(backup_state['services'])
            self._rollback_config_maps(backup_state['config_maps'])
            self._rollback_secrets(backup_state['secrets'])

            logger.info("Rollback completed successfully")

        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            raise

    def list_deployments(self) -> List[Dict[str, Any]]:
        """
        List available deployment backups
        """
        deployments = []
        for backup_file in self.backup_dir.glob("backup_*.json"):
            try:
                with open(backup_file, 'r') as f:
                    backup_data = json.load(f)
                    deployments.append({
                        'id': backup_file.stem.replace('backup_', ''),
                        'timestamp': backup_data['timestamp'],
                        'environment': backup_data['environment']
                    })
            except Exception as e:
                logger.warning(f"Error reading backup file {backup_file}: {e}")

        return sorted(
            deployments,
            key=lambda x: x['timestamp'],
            reverse=True
        )

    def deployment_exists(
        self,
        deployment_id: str
    ) -> bool:
        """
        Check if deployment backup exists
        """
        backup_file = self.backup_dir / f"backup_{deployment_id}.json"
        return backup_file.exists()

    def _get_current_state(self) -> Dict[str, Any]:
        """
        Get current deployment state
        """
        namespace = self.config.get('namespace')
        
        return {
            'deployments': self._get_deployments(namespace),
            'services': self._get_services(namespace),
            'config_maps': self._get_config_maps(namespace),
            'secrets': self._get_secrets(namespace)
        }

    def _get_backup_state(
        self,
        deployment_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get backup state for rollback
        """
        if deployment_id:
            backup_file = self.backup_dir / f"backup_{deployment_id}.json"
            if not backup_file.exists():
                raise ValueError(f"Backup {deployment_id} not found")
        else:
            # Get latest backup
            backups = list(self.backup_dir.glob("backup_*.json"))
            if not backups:
                return None
            backup_file = max(backups, key=os.path.getctime)

        try:
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
                return backup_data['state']
        except Exception as e:
            logger.error(f"Error reading backup file: {e}")
            raise

    def _get_deployments(
        self,
        namespace: str
    ) -> List[Dict[str, Any]]:
        """
        Get current deployments
        """
        deployments = []
        try:
            deployment_list = self.k8s_apps_v1.list_namespaced_deployment(
                namespace=namespace
            )
            for deployment in deployment_list.items:
                deployments.append(
                    client.ApiClient().sanitize_for_serialization(deployment)
                )
        except Exception as e:
            logger.warning(f"Error getting deployments: {e}")
        return deployments

    def _get_services(
        self,
        namespace: str
    ) -> List[Dict[str, Any]]:
        """
        Get current services
        """
        services = []
        try:
            service_list = self.k8s_core_v1.list_namespaced_service(
                namespace=namespace
            )
            for service in service_list.items:
                services.append(
                    client.ApiClient().sanitize_for_serialization(service)
                )
        except Exception as e:
            logger.warning(f"Error getting services: {e}")
        return services

    def _get_config_maps(
        self,
        namespace: str
    ) -> List[Dict[str, Any]]:
        """
        Get current config maps
        """
        config_maps = []
        try:
            config_map_list = self.k8s_core_v1.list_namespaced_config_map(
                namespace=namespace
            )
            for config_map in config_map_list.items:
                config_maps.append(
                    client.ApiClient().sanitize_for_serialization(config_map)
                )
        except Exception as e:
            logger.warning(f"Error getting config maps: {e}")
        return config_maps

    def _get_secrets(
        self,
        namespace: str
    ) -> List[Dict[str, Any]]:
        """
        Get current secrets
        """
        secrets = []
        try:
            secret_list = self.k8s_core_v1.list_namespaced_secret(
                namespace=namespace
            )
            for secret in secret_list.items:
                secrets.append(
                    client.ApiClient().sanitize_for_serialization(secret)
                )
        except Exception as e:
            logger.warning(f"Error getting secrets: {e}")
        return secrets

    def _rollback_deployments(
        self,
        deployments: List[Dict[str, Any]]
    ):
        """
        Rollback deployments to previous state
        """
        for deployment in deployments:
            try:
                self.k8s_apps_v1.replace_namespaced_deployment(
                    name=deployment['metadata']['name'],
                    namespace=deployment['metadata']['namespace'],
                    body=deployment
                )
            except Exception as e:
                logger.error(
                    f"Error rolling back deployment "
                    f"{deployment['metadata']['name']}: {e}"
                )
                raise

    def _rollback_services(
        self,
        services: List[Dict[str, Any]]
    ):
        """
        Rollback services to previous state
        """
        for service in services:
            try:
                self.k8s_core_v1.replace_namespaced_service(
                    name=service['metadata']['name'],
                    namespace=service['metadata']['namespace'],
                    body=service
                )
            except Exception as e:
                logger.error(
                    f"Error rolling back service "
                    f"{service['metadata']['name']}: {e}"
                )
                raise

    def _rollback_config_maps(
        self,
        config_maps: List[Dict[str, Any]]
    ):
        """
        Rollback config maps to previous state
        """
        for config_map in config_maps:
            try:
                self.k8s_core_v1.replace_namespaced_config_map(
                    name=config_map['metadata']['name'],
                    namespace=config_map['metadata']['namespace'],
                    body=config_map
                )
            except Exception as e:
                logger.error(
                    f"Error rolling back config map "
                    f"{config_map['metadata']['name']}: {e}"
                )
                raise

    def _rollback_secrets(
        self,
        secrets: List[Dict[str, Any]]
    ):
        """
        Rollback secrets to previous state
        """
        for secret in secrets:
            try:
                self.k8s_core_v1.replace_namespaced_secret(
                    name=secret['metadata']['name'],
                    namespace=secret['metadata']['namespace'],
                    body=secret
                )
            except Exception as e:
                logger.error(
                    f"Error rolling back secret "
                    f"{secret['metadata']['name']}: {e}"
                )
                raise
