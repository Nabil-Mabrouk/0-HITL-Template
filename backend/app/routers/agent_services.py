"""
Router FastAPI pour les services agentic IA.

Ce module expose les endpoints pour:
- Lister les services disponibles
- Exécuter des services
- Gérer l'historique des exécutions
- Surveiller l'état des services
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models import User, UserRole
from app.agents.service_registry import get_service_registry, AgentServiceConfig
from app.agents.core.orchestrator import AgentOrchestrator, WorkflowExecution
from app.agents.core.tool_registry import get_tool_registry

# Import des schémas (à créer)
# from app.schemas.agent_services import ...

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/agent-services", tags=["agent-services"])


@router.get("/services", response_model=List[dict])  # À typer avec un schema
async def list_available_services(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[dict]:
    """
    Liste tous les services agentic IA disponibles pour l'utilisateur.

    Retourne les services activés que l'utilisateur peut utiliser,
    en fonction de son rôle et des permissions.
    """
    registry = get_service_registry()
    available_services = registry.get_available_services()

    # Filtrer par permissions utilisateur si nécessaire
    # (ex: certains services réservés aux premium)
    filtered_services = []
    for service in available_services:
        # Vérifier les permissions
        if service.requires_auth and not current_user:
            continue

        # Vérifier le rôle si spécifié dans le service
        # (à implémenter selon les besoins)

        filtered_services.append({
            'slug': service.slug,
            'name': service.name,
            'description': service.description,
            'icon': service.icon,
            'category': service.category,
            'agents_count': len(service.agents),
            'workflows_count': len(service.workflows)
        })

    return filtered_services


@router.get("/services/{service_slug}")
async def get_service_details(
    service_slug: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Récupère les détails d'un service spécifique.

    Inclut la configuration des agents, les workflows disponibles,
    et les schémas d'entrée/sortie.
    """
    registry = get_service_registry()
    service = registry.get_service(service_slug)

    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service_slug}' not found"
        )

    if not service.enabled:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Service '{service_slug}' is disabled"
        )

    # Vérifier les permissions
    if service.requires_auth and not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for this service"
        )

    return {
        'slug': service.slug,
        'name': service.name,
        'description': service.description,
        'icon': service.icon,
        'category': service.category,
        'agents': [
            {
                'name': agent.name,
                'model': agent.model,
                'tools': agent.tools,
                'temperature': agent.temperature
            }
            for agent in service.agents
        ],
        'workflows': [
            {
                'name': workflow.name,
                'description': workflow.description,
                'steps': workflow.steps,
                'default_params': workflow.default_params
            }
            for workflow in service.workflows
        ]
    }


@router.post("/services/{service_slug}/execute")
async def execute_service(
    service_slug: str,
    workflow_name: Optional[str] = None,
    parameters: Optional[dict] = None,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Exécute un service agentic IA.

    Si workflow_name est spécifié, exécute un workflow prédéfini.
    Sinon, exécute le service avec les paramètres personnalisés.
    """
    registry = get_service_registry()
    service = registry.get_service(service_slug)

    # Validation
    if not service or not service.enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service_slug}' not found or disabled"
        )

    if service.requires_auth and not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    parameters = parameters or {}

    # Trouver le workflow si spécifié
    workflow = None
    if workflow_name:
        workflow = next(
            (w for w in service.workflows if w.name == workflow_name),
            None
        )
        if not workflow:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow '{workflow_name}' not found in service '{service_slug}'"
            )

        # Fusionner les paramètres par défaut avec les paramètres fournis
        execution_params = {**workflow.default_params, **parameters}
        steps_to_execute = workflow.steps
    else:
        # Exécution personnalisée - nécessite des paramètres spécifiques
        execution_params = parameters
        steps_to_execute = ["custom_execution"]  # À adapter

    # Initialiser l'orchestrateur
    orchestrator = AgentOrchestrator(
        agent_registry=None,  # À implémenter
        tool_registry=get_tool_registry()
    )

    # Exécuter le workflow
    execution = await orchestrator.execute_workflow(
        service_slug=service_slug,
        workflow_name=workflow_name or "custom",
        user_id=current_user.id,
        input_params=execution_params,
        workflow_steps=steps_to_execute,
        context={'service_slug': service_slug, 'user_id': current_user.id}
    )

    # Enregistrer l'exécution en base de données (à implémenter)
    # db_execution = ServiceExecution(...)
    # db.add(db_execution)
    # db.commit()

    return {
        'execution_id': execution.execution_id,
        'service_slug': service_slug,
        'workflow_name': workflow_name,
        'status': execution.status,
        'created_at': execution.created_at,
        'message': 'Execution started successfully'
    }


@router.get("/executions/{execution_id}")
async def get_execution_status(
    execution_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Récupère le statut d'une exécution spécifique.
    """
    # Récupérer depuis la base de données (à implémenter)
    # execution = db.query(ServiceExecution).filter(...).first()

    # Pour l'instant, utiliser l'orchestrateur en mémoire
    orchestrator = AgentOrchestrator(
        agent_registry=None,
        tool_registry=get_tool_registry()
    )

    execution = orchestrator.get_execution(execution_id)

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution '{execution_id}' not found"
        )

    # Vérifier les permissions
    if execution.user_id != current_user.id and not current_user.has_role(UserRole.admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this execution"
        )

    return {
        'execution_id': execution.execution_id,
        'service_slug': execution.service_slug,
        'workflow_name': execution.workflow_name,
        'status': execution.status,
        'created_at': execution.created_at,
        'completed_at': execution.completed_at,
        'steps': [
            {
                'step_id': step.step_id,
                'agent_name': step.agent_name,
                'status': step.status,
                'execution_time': step.execution_time,
                'error': step.error
            }
            for step in execution.steps
        ],
        'result': execution.result
    }


@router.get("/executions")
async def list_user_executions(
    service_slug: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Liste les exécutions de l'utilisateur.

    Peut être filtré par service et paginé.
    """
    # Récupérer depuis la base de données (à implémenter)
    # query = db.query(ServiceExecution).filter(
    #     ServiceExecution.user_id == current_user.id
    # )
    #
    # if service_slug:
    #     query = query.filter(ServiceExecution.service_slug == service_slug)
    #
    # total = query.count()
    # executions = query.order_by(
    #     ServiceExecution.created_at.desc()
    # ).offset(offset).limit(limit).all()

    # Pour l'instant, utiliser l'orchestrateur en mémoire
    orchestrator = AgentOrchestrator(
        agent_registry=None,
        tool_registry=get_tool_registry()
    )

    executions = orchestrator.get_user_executions(
        user_id=current_user.id,
        limit=limit + offset
    )

    # Filtrer par service si nécessaire
    if service_slug:
        executions = [
            e for e in executions
            if e.service_slug == service_slug
        ]

    # Pagination manuelle
    total = len(executions)
    paginated_executions = executions[offset:offset + limit]

    return {
        'total': total,
        'offset': offset,
        'limit': limit,
        'executions': [
            {
                'execution_id': e.execution_id,
                'service_slug': e.service_slug,
                'workflow_name': e.workflow_name,
                'status': e.status,
                'created_at': e.created_at,
                'completed_at': e.completed_at
            }
            for e in paginated_executions
        ]
    }


@router.post("/executions/{execution_id}/cancel")
async def cancel_execution(
    execution_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> dict:
    """
    Annule une exécution en cours.
    """
    orchestrator = AgentOrchestrator(
        agent_registry=None,
        tool_registry=get_tool_registry()
    )

    execution = orchestrator.get_execution(execution_id)

    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution '{execution_id}' not found"
        )

    # Vérifier les permissions
    if execution.user_id != current_user.id and not current_user.has_role(UserRole.admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel this execution"
        )

    if execution.status != "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel execution with status '{execution.status}'"
        )

    success = await orchestrator.cancel_execution(execution_id)

    return {
        'success': success,
        'execution_id': execution_id,
        'message': 'Execution cancelled successfully' if success else 'Failed to cancel execution'
    }


@router.get("/tools")
async def list_available_tools(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[dict]:
    """
    Liste les outils disponibles pour les agents.

    Utile pour la documentation et le debugging.
    """
    registry = get_tool_registry()

    if category:
        # Convertir la catégorie string en enum
        from app.agents.core.tool_registry import ToolCategory
        try:
            tool_category = ToolCategory(category)
            tools = registry.get_tools_by_category(tool_category)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category: {category}. Valid categories: {[c.value for c in ToolCategory]}"
            )
    else:
        tools = registry.get_all_tools()

    return [
        {
            'name': tool.name,
            'description': tool.description,
            'category': tool.category.value,
            'requires_auth': tool.requires_auth,
            'parameters': [
                {
                    'name': param.name,
                    'type': param.type.__name__ if hasattr(param.type, '__name__') else str(param.type),
                    'required': param.required,
                    'description': param.description
                }
                for param in tool.parameters
            ]
        }
        for tool in tools
    ]