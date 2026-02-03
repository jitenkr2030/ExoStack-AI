"""
CLI Functionality Tests
"""
import pytest
from typer.testing import CliRunner
from exo_cli.main import app
from exo_cli.deployment import DeploymentManager
from exo_cli.rollback import RollbackManager

runner = CliRunner()

class TestCLIFunctionality:
    def test_deploy_command(self):
        """Test deployment command"""
        result = runner.invoke(app, [
            'deploy',
            'auto',
            '--config-path=test_config.yaml',
            '--dry-run'
        ])
        assert result.exit_code == 0
        assert "Deployment plan" in result.stdout

    def test_validate_command(self):
        """Test configuration validation"""
        result = runner.invoke(app, [
            'deploy',
            'validate',
            '--config-path=test_config.yaml'
        ])
        assert result.exit_code == 0

    def test_rollback_command(self):
        """Test rollback functionality"""
        result = runner.invoke(app, [
            'deploy',
            'rollback',
            '--deployment-id=test-deployment'
        ])
        assert result.exit_code == 0

