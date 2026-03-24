"""
Registry pour la gestion des services agentic IA.

Ce module permet d'enregistrer, découvrir et configurer les services
d'agents IA disponibles dans l'application. Chaque service correspond
à une fonctionnalité métier (ex: news scraper, research assistant, etc.)
avec ses propres agents, outils et workflows.
"""

import yaml
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field
from pathlib import Path

class AgentConfig(BaseModel):
    """Configuration d'un agent individuel."""
    name: str
    model: str = "gpt-4"
    tools: List[str] = Field(default_factory=list)
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None

class WorkflowConfig(BaseModel):
    """Configuration d'un workflow prédéfini."""
    name: str
    description: Optional[str] = None
    steps: List[str] = Field(default_factory=list)
    default_params: Dict[str, Any] = Field(default_factory=dict)

class AgentServiceConfig(BaseModel):
    """Configuration complète d'un service agentic IA."""
    slug: str
    name: str
    description: str
    icon: str = "activity"
    category: str = "general"
    enabled: bool = True
    requires_auth: bool = True
    agents: List[AgentConfig] = Field(default_factory=list)
    workflows: List[WorkflowConfig] = Field(default_factory=list)
    config_schema: Optional[Dict[str, Any]] = None  # JSON Schema pour la configuration
    output_schema: Optional[Dict[str, Any]] = None  # JSON Schema pour les résultats

class ServiceRegistry:
    """Registry central pour tous les services agentic IA."""

    def __init__(self, config_path: Optional[Path] = None):
        self.services: Dict[str, AgentServiceConfig] = {}
        self.config_path = config_path

        if config_path and config_path.exists():
            self.load_from_config(config_path)

    def register(self, service: AgentServiceConfig) -> None:
        """Enregistre un nouveau service."""
        self.services[service.slug] = service

    def get_service(self, slug: str) -> Optional[AgentServiceConfig]:
        """Récupère un service par son slug."""
        return self.services.get(slug)

    def get_available_services(self) -> List[AgentServiceConfig]:
        """Retourne tous les services activés."""
        return [s for s in self.services.values() if s.enabled]

    def load_from_config(self, config_path: Path) -> None:
        """Charge les services depuis un fichier YAML de configuration."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)

            services_data = config_data.get('services', {})
            for slug, service_data in services_data.items():
                service_data['slug'] = slug
                service = AgentServiceConfig(**service_data)
                self.register(service)

        except Exception as e:
            raise RuntimeError(f"Failed to load services config from {config_path}: {e}")

    def get_service_names_by_category(self) -> Dict[str, List[str]]:
        """Retourne les services groupés par catégorie."""
        categories: Dict[str, List[str]] = {}
        for service in self.get_available_services():
            categories.setdefault(service.category, []).append(service.slug)
        return categories

# Instance singleton du registry
_registry_instance: Optional[ServiceRegistry] = None

def get_service_registry(config_path: Optional[Path] = None) -> ServiceRegistry:
    """Retourne l'instance singleton du registry."""
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ServiceRegistry(config_path)
    return _registry_instance