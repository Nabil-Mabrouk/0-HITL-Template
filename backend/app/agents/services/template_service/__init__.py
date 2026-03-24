"""
Template pour créer un nouveau service agentic IA.

Copiez ce dossier et adaptez-le pour créer votre propre service.
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class TemplateService:
    """
    Classe de base pour un service agentic IA.

    Cette classe sert de template pour créer de nouveaux services.
    Chaque service doit implémenter les méthodes d'exécution appropriées.
    """

    def __init__(self, service_slug: str, config: Dict[str, Any]):
        self.service_slug = service_slug
        self.config = config
        self.logger = logging.getLogger(f"service.{service_slug}")

    async def execute_workflow(
        self,
        workflow_name: str,
        parameters: Dict[str, Any],
        user_id: int,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Exécute un workflow de ce service.

        Args:
            workflow_name: Nom du workflow à exécuter
            parameters: Paramètres d'exécution
            user_id: ID de l'utilisateur
            context: Contexte partagé

        Returns:
            Résultat de l'exécution

        Raises:
            ValueError: Si le workflow n'existe pas
        """
        self.logger.info(
            f"Executing workflow '{workflow_name}' for user {user_id}"
        )

        # Router vers la méthode appropriée
        if workflow_name == "example_workflow":
            return await self._execute_example_workflow(parameters, user_id, context)
        else:
            raise ValueError(f"Unknown workflow: {workflow_name}")

    async def _execute_example_workflow(
        self,
        parameters: Dict[str, Any],
        user_id: int,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Exemple d'implémentation de workflow.

        Remplacez cette méthode par la logique réelle de votre service.
        """
        # Logique d'exemple
        self.logger.info(f"Example workflow executed with params: {parameters}")

        # Simuler un traitement
        import asyncio
        await asyncio.sleep(0.5)

        return {
            "success": True,
            "message": "Example workflow completed successfully",
            "data": {
                "processed_parameters": parameters,
                "user_id": user_id,
                "context_keys": list(context.keys())
            }
        }

    def get_available_workflows(self) -> List[Dict[str, Any]]:
        """
        Retourne la liste des workflows disponibles pour ce service.

        Returns:
            Liste des workflows avec leurs descriptions et paramètres
        """
        return [
            {
                "name": "example_workflow",
                "description": "Workflow d'exemple pour le template",
                "parameters": [
                    {
                        "name": "example_param",
                        "type": "string",
                        "required": False,
                        "default": "default_value",
                        "description": "Paramètre d'exemple"
                    }
                ]
            }
        ]

# Factory function pour créer une instance du service
def create_service(service_slug: str, config: Dict[str, Any]) -> TemplateService:
    """
    Factory function pour créer une instance du service.

    Cette fonction est utilisée par le système de découverte de services.
    """
    return TemplateService(service_slug, config)