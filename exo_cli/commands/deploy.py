"""
Enhanced deployment command with automated deployment, validation, and rollback
"""
import os
import sys
import time
import yaml
import logging
import asyncio
from typing import Optional, Dict, List
from pathlib import Path
import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from kubernetes import client, config
from ..utils import load_config, validate_config, create_deployment_id
from ..deployment import DeploymentManager
from ..validators import ConfigValidator
from ..rollback import RollbackManager

app = typer.Typer()
console = Console()
logger = logging.getLogger(__name__)

class DeploymentError(Exception):
    """Custom exception for deployment errors"""
    pass

@app.command()
def auto(
    config_path: str = typer.Option(
        "deploy.yaml",
        help="Path to deployment configuration file"
    ),
    environment: str = typer.Option(
        "development",
        help="Deployment environment (development/staging/production)"
    ),
    dry_run: bool = typer.Option(
        False,
        help="Validate configuration without actual deployment"
    ),
    force: bool = typer.Option(
        False,
        help="Force deployment without confirmation"
    )
):
    """
    Automated deployment with validation and rollback capabilities
    """
    try:
        # Load and validate configuration
        config_data = load_deployment_config(config_path, environment)
        
        # Validate configuration
        validator = ConfigValidator(config_data)
        validation_result = validator.validate()
        
        if not validation_result.is_valid:
            console.print(
                "[red]Configuration validation failed:[/red]"
            )
            for error in validation_result.errors:
                console.print(f"[red]- {error}[/red]")
            raise typer.Exit(1)

        # Create deployment manager
        deployment_manager = DeploymentManager(
            config_data,
            environment=environment
        )
        
        # Create rollback manager
        rollback_manager = RollbackManager(
            config_data,
            environment=environment
        )

        # Dry run check
        if dry_run:
            console.print(
                "\n[yellow]Dry run - Deployment plan:[/yellow]"
            )
            deployment_manager.print_plan()
            return

        # Deployment confirmation
        if not force and not Confirm.ask(
            "\nProceed with deployment?"
        ):
            console.print("Deployment cancelled")
            return

        # Execute deployment
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            # Backup current state
            progress.add_task(
                "Creating deployment backup...",
                total=None
            )
            rollback_manager.create_backup()

            # Execute pre-deployment checks
            progress.add_task(
                "Running pre-deployment checks...",
                total=None
            )
            deployment_manager.run_pre_deployment_checks()

            # Deploy components
            progress.add_task(
                "Deploying components...",
                total=None
            )
            deployment_result = deployment_manager.deploy()

            # Validate deployment
            progress.add_task(
                "Validating deployment...",
                total=None
            )
            validation_result = deployment_manager.validate_deployment()

            if not validation_result.is_valid:
                console.print(
                    "[red]Deployment validation failed. "
                    "Initiating rollback...[/red]"
                )
                rollback_manager.rollback()
                raise DeploymentError(
                    "Deployment validation failed"
                )

            # Execute post-deployment tasks
            progress.add_task(
                "Running post-deployment tasks...",
                total=None
            )
            deployment_manager.run_post_deployment_tasks()

        console.print(
            "[green]Deployment completed successfully![/green]"
        )

    except Exception as e:
        console.print(f"[red]Deployment failed: {str(e)}[/red]")
        if not dry_run and Confirm.ask(
            "\nWould you like to rollback?"
        ):
            try:
                rollback_manager.rollback()
                console.print(
                    "[green]Rollback completed successfully[/green]"
                )
            except Exception as rollback_error:
                console.print(
                    f"[red]Rollback failed: {str(rollback_error)}[/red]"
                )
        raise typer.Exit(1)

@app.command()
def validate(
    config_path: str = typer.Option(
        "deploy.yaml",
        help="Path to deployment configuration file"
    ),
    environment: str = typer.Option(
        "development",
        help="Deployment environment to validate"
    )
):
    """
    Validate deployment configuration
    """
    try:
        config_data = load_deployment_config(config_path, environment)
        validator = ConfigValidator(config_data)
        validation_result = validator.validate()

        if validation_result.is_valid:
            console.print(
                "[green]Configuration validation successful![/green]"
            )
        else:
            console.print(
                "[red]Configuration validation failed:[/red]"
            )
            for error in validation_result.errors:
                console.print(f"[red]- {error}[/red]")
            raise typer.Exit(1)

    except Exception as e:
        console.print(f"[red]Validation failed: {str(e)}[/red]")
        raise typer.Exit(1)

@app.command()
def rollback(
    deployment_id: Optional[str] = typer.Argument(
        None,
        help="Specific deployment ID to rollback to"
    )
):
    """
    Rollback to previous deployment state
    """
    try:
        rollback_manager = RollbackManager()
        
        if deployment_id:
            # Rollback to specific deployment
            if not rollback_manager.deployment_exists(deployment_id):
                console.print(
                    f"[red]Deployment {deployment_id} not found[/red]"
                )
                raise typer.Exit(1)
        else:
            # List available deployments
            deployments = rollback_manager.list_deployments()
            if not deployments:
                console.print(
                    "[yellow]No previous deployments found[/yellow]"
                )
                raise typer.Exit(1)

            console.print("\nAvailable deployments:")
            for dep in deployments:
                console.print(
                    f"- {dep['id']} "
                    f"({dep['timestamp']}) "
                    f"[{dep['environment']}]"
                )

            deployment_id = typer.prompt(
                "\nEnter deployment ID to rollback to"
            )

        if not force and not Confirm.ask(
            f"\nRollback to deployment {deployment_id}?"
        ):
            console.print("Rollback cancelled")
            return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            progress.add_task(
                "Initiating rollback...",
                total=None
            )
            rollback_manager.rollback(deployment_id)

        console.print(
            "[green]Rollback completed successfully![/green]"
        )

    except Exception as e:
        console.print(f"[red]Rollback failed: {str(e)}[/red]")
        raise typer.Exit(1)

def load_deployment_config(
    config_path: str,
    environment: str
) -> Dict:
    """
    Load and validate deployment configuration
    """
    try:
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)

        if environment not in config_data.get('environments', {}):
            raise ValueError(
                f"Environment '{environment}' not found in configuration"
            )

        return {
            **config_data['common'],
            **config_data['environments'][environment]
        }

    except Exception as e:
        raise ValueError(f"Error loading configuration: {str(e)}")