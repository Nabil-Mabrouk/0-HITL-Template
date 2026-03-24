"""
Système de mémoire pour les agents IA.

Ce module gère la mémoire à court et long terme pour les agents,
permettant la persistance du contexte entre les interactions.
"""

import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta

class MemoryType(str, Enum):
    """Types de mémoire supportés."""
    SHORT_TERM = "short_term"  # Mémoire de session
    LONG_TERM = "long_term"    # Mémoire persistante
    CONTEXTUAL = "contextual"  # Mémoire contextuelle (conversation)

@dataclass
class MemoryEntry:
    """Entrée de mémoire individuelle."""
    id: str
    type: MemoryType
    content: Dict[str, Any]
    user_id: int
    agent_name: Optional[str] = None
    service_slug: Optional[str] = None
    timestamp: float = field(default_factory=time.time)
    expires_at: Optional[float] = None  # Pour la mémoire à court terme
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_expired(self) -> bool:
        """Vérifie si l'entrée de mémoire a expiré."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convertit l'entrée en dictionnaire."""
        return {
            'id': self.id,
            'type': self.type,
            'content': self.content,
            'user_id': self.user_id,
            'agent_name': self.agent_name,
            'service_slug': self.service_slug,
            'timestamp': self.timestamp,
            'expires_at': self.expires_at,
            'metadata': self.metadata
        }

class AgentMemory:
    """Système de mémoire pour les agents IA."""

    def __init__(self, storage_backend: Optional[Any] = None):
        """
        Initialise le système de mémoire.

        Args:
            storage_backend: Backend de stockage (ex: base de données, Redis).
                            Si None, utilise une mémoire en RAM.
        """
        self.storage_backend = storage_backend
        self._memory_store: Dict[str, MemoryEntry] = {}

        # Configuration par défaut
        self.default_ttl = {
            MemoryType.SHORT_TERM: 3600,  # 1 heure
            MemoryType.LONG_TERM: None,    # Pas d'expiration
            MemoryType.CONTEXTUAL: 1800,   # 30 minutes
        }

    def store(
        self,
        content: Dict[str, Any],
        user_id: int,
        memory_type: MemoryType = MemoryType.SHORT_TERM,
        agent_name: Optional[str] = None,
        service_slug: Optional[str] = None,
        ttl: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Stocke une entrée de mémoire.

        Args:
            content: Contenu à stocker
            user_id: ID de l'utilisateur
            memory_type: Type de mémoire
            agent_name: Nom de l'agent (optionnel)
            service_slug: Slug du service (optionnel)
            ttl: Time-to-live en secondes (optionnel)
            metadata: Métadonnées supplémentaires (optionnel)

        Returns:
            ID de l'entrée stockée
        """
        import uuid

        entry_id = str(uuid.uuid4())

        # Déterminer la date d'expiration
        expires_at = None
        if ttl is not None:
            expires_at = time.time() + ttl
        elif memory_type in self.default_ttl:
            default_ttl = self.default_ttl[memory_type]
            if default_ttl is not None:
                expires_at = time.time() + default_ttl

        entry = MemoryEntry(
            id=entry_id,
            type=memory_type,
            content=content,
            user_id=user_id,
            agent_name=agent_name,
            service_slug=service_slug,
            expires_at=expires_at,
            metadata=metadata or {}
        )

        # Stocker dans le backend ou en mémoire
        if self.storage_backend:
            # À implémenter selon le backend
            pass
        else:
            self._memory_store[entry_id] = entry

        return entry_id

    def retrieve(
        self,
        user_id: int,
        memory_type: Optional[MemoryType] = None,
        agent_name: Optional[str] = None,
        service_slug: Optional[str] = None,
        limit: int = 20,
        min_relevance: float = 0.0
    ) -> List[MemoryEntry]:
        """
        Récupère des entrées de mémoire.

        Args:
            user_id: ID de l'utilisateur
            memory_type: Filtrer par type (optionnel)
            agent_name: Filtrer par agent (optionnel)
            service_slug: Filtrer par service (optionnel)
            limit: Nombre maximum d'entrées à retourner
            min_relevance: Score de pertinence minimum (pour recherche sémantique)

        Returns:
            Liste des entrées de mémoire correspondantes
        """
        entries = []

        # Récupérer depuis le backend ou la mémoire
        if self.storage_backend:
            # À implémenter selon le backend
            pass
        else:
            for entry in self._memory_store.values():
                # Filtrer les entrées expirées
                if entry.is_expired():
                    continue

                # Appliquer les filtres
                if entry.user_id != user_id:
                    continue

                if memory_type and entry.type != memory_type:
                    continue

                if agent_name and entry.agent_name != agent_name:
                    continue

                if service_slug and entry.service_slug != service_slug:
                    continue

                entries.append(entry)

        # Trier par timestamp (plus récent d'abord)
        entries.sort(key=lambda x: x.timestamp, reverse=True)

        # Limiter le nombre de résultats
        return entries[:limit]

    def retrieve_relevant(
        self,
        query: str,
        user_id: int,
        memory_type: Optional[MemoryType] = None,
        limit: int = 10
    ) -> List[MemoryEntry]:
        """
        Récupère les entrées de mémoire pertinentes pour une requête.

        Args:
            query: Requête textuelle
            user_id: ID de l'utilisateur
            memory_type: Filtrer par type (optionnel)
            limit: Nombre maximum d'entrées à retourner

        Returns:
            Liste des entrées de mémoire pertinentes
        """
        # Dans une implémentation complète, on utiliserait des embeddings
        # et une recherche vectorielle. Pour l'instant, on fait une simple
        # recherche textuelle.

        entries = self.retrieve(
            user_id=user_id,
            memory_type=memory_type,
            limit=100  # Récupérer plus d'entrées pour la recherche
        )

        # Recherche textuelle simple
        query_lower = query.lower()
        relevant_entries = []

        for entry in entries:
            # Convertir le contenu en texte pour la recherche
            content_text = json.dumps(entry.content, ensure_ascii=False).lower()

            # Vérifier si la requête apparaît dans le contenu
            if query_lower in content_text:
                relevant_entries.append(entry)

        return relevant_entries[:limit]

    def delete(self, entry_id: str) -> bool:
        """Supprime une entrée de mémoire."""
        if self.storage_backend:
            # À implémenter selon le backend
            pass
        else:
            if entry_id in self._memory_store:
                del self._memory_store[entry_id]
                return True
        return False

    def delete_expired(self) -> int:
        """Supprime toutes les entrées expirées et retourne le nombre supprimé."""
        deleted_count = 0

        if self.storage_backend:
            # À implémenter selon le backend
            pass
        else:
            expired_ids = [
                entry_id for entry_id, entry in self._memory_store.items()
                if entry.is_expired()
            ]

            for entry_id in expired_ids:
                del self._memory_store[entry_id]
                deleted_count += 1

        return deleted_count

    def clear_user_memory(
        self,
        user_id: int,
        memory_type: Optional[MemoryType] = None
    ) -> int:
        """
        Supprime toutes les mémoires d'un utilisateur.

        Args:
            user_id: ID de l'utilisateur
            memory_type: Type de mémoire à supprimer (optionnel)

        Returns:
            Nombre d'entrées supprimées
        """
        deleted_count = 0

        if self.storage_backend:
            # À implémenter selon le backend
            pass
        else:
            entries_to_delete = []

            for entry_id, entry in self._memory_store.items():
                if entry.user_id == user_id:
                    if memory_type is None or entry.type == memory_type:
                        entries_to_delete.append(entry_id)

            for entry_id in entries_to_delete:
                del self._memory_store[entry_id]
                deleted_count += 1

        return deleted_count

    def get_memory_summary(self, user_id: int) -> Dict[str, Any]:
        """
        Retourne un résumé des mémoires d'un utilisateur.

        Args:
            user_id: ID de l'utilisateur

        Returns:
            Dictionnaire avec les statistiques de mémoire
        """
        entries = self.retrieve(user_id=user_id, limit=1000)

        summary = {
            'total_entries': len(entries),
            'by_type': {},
            'by_service': {},
            'by_agent': {},
            'oldest_timestamp': None,
            'newest_timestamp': None
        }

        if entries:
            timestamps = [entry.timestamp for entry in entries]
            summary['oldest_timestamp'] = min(timestamps)
            summary['newest_timestamp'] = max(timestamps)

            # Compter par type
            for entry in entries:
                # Type
                summary['by_type'][entry.type] = summary['by_type'].get(entry.type, 0) + 1

                # Service
                if entry.service_slug:
                    summary['by_service'][entry.service_slug] = summary['by_service'].get(entry.service_slug, 0) + 1

                # Agent
                if entry.agent_name:
                    summary['by_agent'][entry.agent_name] = summary['by_agent'].get(entry.agent_name, 0) + 1

        return summary