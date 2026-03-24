"""
Registre des outils disponibles pour les agents IA.

Ce module gère l'enregistrement, la découverte et l'exécution des outils
que les agents peuvent utiliser pour interagir avec le monde externe.
"""

import inspect
import logging
from typing import Dict, List, Any, Optional, Callable, Type
from dataclasses import dataclass, field
from enum import Enum
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class ToolCategory(str, Enum):
    """Catégories d'outils."""
    WEB = "web"
    DATA = "data"
    FILES = "files"
    API = "api"
    ANALYSIS = "analysis"
    CONTENT = "content"
    SYSTEM = "system"

@dataclass
class ToolParameter:
    """Paramètre d'un outil."""
    name: str
    type: Type
    description: str
    required: bool = True
    default: Any = None

@dataclass
class Tool:
    """Définition d'un outil disponible pour les agents."""
    name: str
    function: Callable
    description: str
    category: ToolCategory = ToolCategory.SYSTEM
    parameters: List[ToolParameter] = field(default_factory=list)
    returns_schema: Optional[Dict[str, Any]] = None
    requires_auth: bool = False
    rate_limit: Optional[int] = None  # requêtes par minute

class ToolRegistry:
    """Registre central des outils disponibles."""

    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self._rate_limiters: Dict[str, Any] = {}  # À implémenter si nécessaire

    def register(self, tool: Tool) -> None:
        """Enregistre un nouvel outil."""
        if tool.name in self.tools:
            logger.warning(f"Tool '{tool.name}' is already registered. Overwriting.")

        # Extraire les paramètres de la fonction si non spécifiés
        if not tool.parameters:
            tool.parameters = self._extract_parameters_from_function(tool.function)

        self.tools[tool.name] = tool
        logger.info(f"Tool registered: {tool.name} ({tool.category})")

    def register_function(
        self,
        name: str,
        func: Callable,
        description: str,
        category: ToolCategory = ToolCategory.SYSTEM,
        requires_auth: bool = False
    ) -> None:
        """Enregistre une fonction comme outil."""
        tool = Tool(
            name=name,
            function=func,
            description=description,
            category=category,
            requires_auth=requires_auth
        )
        self.register(tool)

    def get_tool(self, name: str) -> Optional[Tool]:
        """Récupère un outil par son nom."""
        return self.tools.get(name)

    def get_tools_by_category(self, category: ToolCategory) -> List[Tool]:
        """Récupère tous les outils d'une catégorie."""
        return [tool for tool in self.tools.values() if tool.category == category]

    def get_all_tools(self) -> List[Tool]:
        """Récupère tous les outils enregistrés."""
        return list(self.tools.values())

    def execute(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        user_id: Optional[int] = None,
        agent_name: Optional[str] = None
    ) -> Any:
        """
        Exécute un outil avec les paramètres donnés.

        Args:
            tool_name: Nom de l'outil
            parameters: Paramètres pour l'outil
            user_id: ID de l'utilisateur (pour l'authentification)
            agent_name: Nom de l'agent (pour le logging)

        Returns:
            Résultat de l'exécution de l'outil

        Raises:
            ValueError: Si l'outil n'existe pas ou si les paramètres sont invalides
            PermissionError: Si l'outil nécessite une authentification
        """
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool '{tool_name}' not found")

        # Vérifier l'authentification
        if tool.requires_auth and user_id is None:
            raise PermissionError(
                f"Tool '{tool_name}' requires authentication"
            )

        # Valider les paramètres
        validated_params = self._validate_parameters(tool, parameters)

        # Vérifier les limites de taux (à implémenter)
        # self._check_rate_limit(tool_name, user_id)

        # Exécuter l'outil
        logger.info(
            f"Executing tool '{tool_name}' for "
            f"user {user_id}, agent {agent_name}"
        )

        try:
            result = tool.function(**validated_params)
            return result
        except Exception as e:
            logger.error(f"Tool '{tool_name}' execution failed: {e}", exc_info=True)
            raise

    def _extract_parameters_from_function(self, func: Callable) -> List[ToolParameter]:
        """Extrait les paramètres d'une fonction."""
        parameters = []
        sig = inspect.signature(func)

        for param_name, param in sig.parameters.items():
            # Ignorer 'self' pour les méthodes
            if param_name == 'self':
                continue

            # Déterminer si le paramètre est requis
            required = param.default == inspect.Parameter.empty

            # Créer le ToolParameter
            tool_param = ToolParameter(
                name=param_name,
                type=param.annotation if param.annotation != inspect.Parameter.empty else Any,
                description=f"Parameter {param_name}",
                required=required,
                default=param.default if not required else None
            )

            parameters.append(tool_param)

        return parameters

    def _validate_parameters(
        self,
        tool: Tool,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Valide et prépare les paramètres pour l'exécution."""
        validated = {}

        for param in tool.parameters:
            param_name = param.name

            if param_name not in parameters:
                if param.required:
                    raise ValueError(
                        f"Missing required parameter: {param_name}"
                    )
                else:
                    # Utiliser la valeur par défaut
                    validated[param_name] = param.default
                    continue

            value = parameters[param_name]

            # Valider le type (simplifié)
            if param.type != Any:
                try:
                    # Essayer de convertir au type attendu
                    if param.type == str:
                        validated[param_name] = str(value)
                    elif param.type == int:
                        validated[param_name] = int(value)
                    elif param.type == float:
                        validated[param_name] = float(value)
                    elif param.type == bool:
                        validated[param_name] = bool(value)
                    else:
                        # Pour les types complexes, on accepte tel quel
                        validated[param_name] = value
                except (ValueError, TypeError) as e:
                    raise ValueError(
                        f"Invalid type for parameter '{param_name}': {e}"
                    )
            else:
                validated[param_name] = value

        # Ajouter des paramètres supplémentaires non définis (pour flexibilité)
        for key, value in parameters.items():
            if key not in validated:
                validated[key] = value

        return validated

    def _check_rate_limit(self, tool_name: str, user_id: Optional[int]) -> None:
        """Vérifie les limites de taux pour un outil."""
        # À implémenter avec un système de rate limiting
        pass

# Outils prédéfinis (exemples)

def web_search(query: str, num_results: int = 5) -> List[Dict[str, Any]]:
    """
    Recherche sur le web.

    Args:
        query: Termes de recherche
        num_results: Nombre de résultats à retourner

    Returns:
        Liste des résultats de recherche
    """
    # Placeholder - à remplacer par une vraie implémentation
    import time
    time.sleep(0.1)  # Simuler un délai réseau

    return [
        {
            'title': f"Result for: {query}",
            'url': f"https://example.com/result/{i}",
            'snippet': f"This is a search result snippet for '{query}'"
        }
        for i in range(num_results)
    ]

def text_to_speech(text: str, language: str = "fr") -> Dict[str, Any]:
    """
    Convertit du texte en parole.

    Args:
        text: Texte à convertir
        language: Langue de la synthèse vocale

    Returns:
        Informations sur le fichier audio généré
    """
    # Placeholder
    return {
        'audio_url': f"https://example.com/audio/{hash(text)}.mp3",
        'duration_seconds': len(text) / 15,  # Estimation
        'language': language
    }

def generate_chart(data: Dict[str, Any], chart_type: str = "line") -> Dict[str, Any]:
    """
    Génère un graphique à partir de données.

    Args:
        data: Données pour le graphique
        chart_type: Type de graphique (line, bar, pie, etc.)

    Returns:
        Informations sur le graphique généré
    """
    # Placeholder
    return {
        'chart_url': f"https://example.com/chart/{hash(str(data))}.png",
        'chart_type': chart_type,
        'data_points': len(data)
    }

# Registre singleton
_tool_registry_instance: Optional[ToolRegistry] = None

def get_tool_registry() -> ToolRegistry:
    """Retourne l'instance singleton du registre d'outils."""
    global _tool_registry_instance
    if _tool_registry_instance is None:
        _tool_registry_instance = ToolRegistry()
        _register_default_tools(_tool_registry_instance)
    return _tool_registry_instance

def _register_default_tools(registry: ToolRegistry) -> None:
    """Enregistre les outils par défaut."""
    # Outils web
    registry.register_function(
        name="web_search",
        func=web_search,
        description="Recherche sur le web",
        category=ToolCategory.WEB,
        requires_auth=False
    )

    # Outils contenu
    registry.register_function(
        name="text_to_speech",
        func=text_to_speech,
        description="Convertit du texte en parole",
        category=ToolCategory.CONTENT,
        requires_auth=True
    )

    # Outils analyse
    registry.register_function(
        name="generate_chart",
        func=generate_chart,
        description="Génère un graphique à partir de données",
        category=ToolCategory.ANALYSIS,
        requires_auth=True
    )

    # Outils système (exemples)
    registry.register_function(
        name="get_current_time",
        func=lambda: {"time": "2024-01-01T12:00:00Z"},  # Placeholder
        description="Retourne l'heure actuelle",
        category=ToolCategory.SYSTEM,
        requires_auth=False
    )