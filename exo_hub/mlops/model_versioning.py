"""
Model Versioning and A/B Testing
"""
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional

class ModelVersioning:
    def __init__(self):
        self.versions = {}
        self.experiments = {}

    async def register_version(
        self,
        model_name: str,
        model_path: str,
        metadata: Dict[str, Any]
    ) -> str:
        """Register new model version"""
        try:
            # Generate version hash
            version_hash = self._generate_version_hash(model_path)
            
            # Store version info
            self.versions[version_hash] = {
                'model_name': model_name,
                'model_path': model_path,
                'metadata': metadata,
                'created_at': datetime.now(),
                'metrics': {},
                'status': 'registered'
            }
            
            return version_hash

        except Exception as e:
            logger.error(f"Version registration failed: {e}")
            raise

    async def create_experiment(
        self,
        name: str,
        versions: List[str],
        traffic_split: Dict[str, float]
    ) -> str:
        """Create A/B testing experiment"""
        try:
            experiment_id = hashlib.sha256(
                f"{name}_{datetime.now()}".encode()
            ).hexdigest()
            
            self.experiments[experiment_id] = {
                'name': name,
                'versions': versions,
                'traffic_split': traffic_split,
                'status': 'active',
                'created_at': datetime.now(),
                'metrics': {}
            }
            
            return experiment_id

        except Exception as e:
            logger.error(f"Experiment creation failed: {e}")
            raise

    async def record_inference_metrics(
        self,
        version: str,
        metrics: Dict[str, Any]
    ):
        """Record inference metrics for version"""
        try:
            if version not in self.versions:
                raise ValueError(f"Version {version} not found")
            
            # Update metrics
            current_metrics = self.versions[version]['metrics']
            for metric_name, value in metrics.items():
                if metric_name not in current_metrics:
                    current_metrics[metric_name] = []
                current_metrics[metric_name].append({
                    'value': value,
                    'timestamp': datetime.now()
                })

        except Exception as e:
            logger.error(f"Failed to record metrics: {e}")
            raise
