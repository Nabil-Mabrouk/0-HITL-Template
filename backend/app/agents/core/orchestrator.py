"""
Orchestrateur pour la coordination des agents IA.

Ce module gère l'exécution des workflows impliquant plusieurs agents,
la coordination des handoffs, et la gestion du contexte partagé.
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ExecutionStatus(str, Enum):
    """Statut d'exécution d'un workflow."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class ExecutionStep:
    """Étape d'exécution dans un workflow."""
    step_id: str
    agent_name: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    status: ExecutionStatus = ExecutionStatus.PENDING
    error: Optional[str] = None
    execution_time: Optional[float] = None  # en secondes

@dataclass
class WorkflowExecution:
    """Exécution d'un workflow complet."""
    execution_id: str
    service_slug: str
    workflow_name: str
    user_id: int
    steps: List[ExecutionStep]
    context: Dict[str, Any]  # Contexte partagé entre les étapes
    created_at: float
    status: ExecutionStatus = ExecutionStatus.PENDING
    completed_at: Optional[float] = None
    result: Optional[Dict[str, Any]] = None

class AgentOrchestrator:
    """Orchestrateur pour la coordination d'agents IA."""

    def __init__(self, agent_registry: Any, tool_registry: Any):
        self.agent_registry = agent_registry
        self.tool_registry = tool_registry
        self.executions: Dict[str, WorkflowExecution] = {}
        self._execution_lock = asyncio.Lock()

    async def execute_workflow(
        self,
        service_slug: str,
        workflow_name: str,
        user_id: int,
        input_params: Dict[str, Any],
        workflow_steps: List[str],
        context: Optional[Dict[str, Any]] = None
    ) -> WorkflowExecution:
        """
        Exécute un workflow composé de plusieurs étapes.

        Args:
            service_slug: Slug du service
            workflow_name: Nom du workflow
            user_id: ID de l'utilisateur
            input_params: Paramètres d'entrée
            workflow_steps: Liste des étapes à exécuter
            context: Contexte initial (optionnel)

        Returns:
            WorkflowExecution: L'exécution du workflow
        """
        execution_id = self._generate_execution_id()

        # Préparer les étapes
        steps = []
        for step_id in workflow_steps:
            # Déterminer quel agent exécute cette étape
            agent_name = self._map_step_to_agent(step_id, service_slug)
            step = ExecutionStep(
                step_id=step_id,
                agent_name=agent_name,
                input_data={}
            )
            steps.append(step)

        execution = WorkflowExecution(
            execution_id=execution_id,
            service_slug=service_slug,
            workflow_name=workflow_name,
            user_id=user_id,
            steps=steps,
            context=context or {},
            created_at=time.time()
        )

        # Enregistrer l'exécution
        async with self._execution_lock:
            self.executions[execution_id] = execution

        # Exécuter en arrière-plan
        asyncio.create_task(self._execute_workflow_background(execution))

        return execution

    async def _execute_workflow_background(self, execution: WorkflowExecution):
        """Exécute un workflow en arrière-plan."""
        execution.status = ExecutionStatus.RUNNING

        try:
            for step in execution.steps:
                if execution.status == ExecutionStatus.CANCELLED:
                    break

                step.status = ExecutionStatus.RUNNING
                start_time = time.time()

                try:
                    # Exécuter l'étape
                    result = await self._execute_step(
                        step,
                        execution.context,
                        execution.user_id
                    )

                    step.output_data = result
                    step.status = ExecutionStatus.COMPLETED

                    # Mettre à jour le contexte partagé
                    if result:
                        execution.context.update(result.get('context_updates', {}))

                except Exception as e:
                    logger.error(f"Step {step.step_id} failed: {e}", exc_info=True)
                    step.status = ExecutionStatus.FAILED
                    step.error = str(e)
                    execution.status = ExecutionStatus.FAILED
                    break

                finally:
                    step.execution_time = time.time() - start_time

            if execution.status == ExecutionStatus.RUNNING:
                execution.status = ExecutionStatus.COMPLETED
                execution.result = {
                    'context': execution.context,
                    'steps': [
                        {
                            'step_id': s.step_id,
                            'status': s.status,
                            'execution_time': s.execution_time
                        }
                        for s in execution.steps
                    ]
                }

        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)
            execution.status = ExecutionStatus.FAILED

        finally:
            execution.completed_at = asyncio.get_event_loop().time()

    async def _execute_step(
        self,
        step: ExecutionStep,
        context: Dict[str, Any],
        user_id: int
    ) -> Dict[str, Any]:
        """
        Exécute une étape individuelle avec l'agent approprié.

        À implémenter selon l'infrastructure d'agents spécifique.
        """
        # Placeholder - à remplacer par l'intégration réelle avec les agents
        logger.info(
            f"Executing step {step.step_id} with agent {step.agent_name} "
            f"for user {user_id}"
        )

        # Simuler un délai d'exécution
        await asyncio.sleep(0.5)

        # Retourner un résultat simulé
        return {
            'result': f"Step {step.step_id} completed by {step.agent_name}",
            'context_updates': {
                f'step_{step.step_id}_completed': True
            }
        }

    def _generate_execution_id(self) -> str:
        """Génère un ID unique pour une exécution."""
        import uuid
        return str(uuid.uuid4())

    def _map_step_to_agent(self, step_id: str, service_slug: str) -> str:
        """
        Mappe une étape à un agent.

        À implémenter avec la logique de mapping spécifique au service.
        """
        # Logique simplifiée: utiliser le premier agent du service
        # Dans une implémentation réelle, cette logique serait configurable
        return f"{service_slug}_agent_1"

    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """Récupère une exécution par son ID."""
        return self.executions.get(execution_id)

    async def cancel_execution(self, execution_id: str) -> bool:
        """Annule une exécution en cours."""
        execution = self.get_execution(execution_id)
        if execution and execution.status == ExecutionStatus.RUNNING:
            execution.status = ExecutionStatus.CANCELLED
            return True
        return False

    def get_user_executions(
        self,
        user_id: int,
        limit: int = 50
    ) -> List[WorkflowExecution]:
        """Récupère les exécutions d'un utilisateur."""
        user_executions = [
            exec for exec in self.executions.values()
            if exec.user_id == user_id
        ]
        user_executions.sort(key=lambda x: x.created_at, reverse=True)
        return user_executions[:limit]