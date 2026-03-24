"""
Garde-fous (guardrails) pour les agents IA.

Ce module implémente des contrôles de sécurité pour prévenir:
- Les prompt injections
- Les sorties inappropriées
- L'utilisation abusive des outils
- Les fuites de données sensibles
"""

import re
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ViolationSeverity(str, Enum):
    """Niveau de sévérité d'une violation."""
    LOW = "low"        # Avertissement
    MEDIUM = "medium"  # Action restreinte
    HIGH = "high"      # Blocage complet

class ViolationType(str, Enum):
    """Type de violation détectée."""
    PROMPT_INJECTION = "prompt_injection"
    TOXIC_CONTENT = "toxic_content"
    SENSITIVE_DATA = "sensitive_data"
    UNAUTHORIZED_TOOL = "unauthorized_tool"
    RATE_LIMIT = "rate_limit"
    CONTEXT_LENGTH = "context_length"

@dataclass
class GuardrailViolation:
    """Violation d'un garde-fou détectée."""
    type: ViolationType
    severity: ViolationSeverity
    message: str
    details: Optional[Dict[str, Any]] = None
    detected_at: float = 0.0

class GuardrailResult:
    """Résultat de l'application des garde-fous."""

    def __init__(self, allowed: bool = True):
        self.allowed = allowed
        self.violations: List[GuardrailViolation] = []
        self.filtered_output: Optional[str] = None
        self.metadata: Dict[str, Any] = {}

    def add_violation(
        self,
        violation_type: ViolationType,
        severity: ViolationSeverity,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Ajoute une violation au résultat."""
        import time
        violation = GuardrailViolation(
            type=violation_type,
            severity=severity,
            message=message,
            details=details,
            detected_at=time.time()
        )
        self.violations.append(violation)

        # Mettre à jour l'état allowed basé sur la sévérité
        if severity == ViolationSeverity.HIGH:
            self.allowed = False
        elif severity == ViolationSeverity.MEDIUM and self.allowed:
            # Medium violations don't automatically block, but can be configured to
            pass

    def has_violations(self) -> bool:
        """Vérifie s'il y a des violations."""
        return len(self.violations) > 0

    def has_high_severity_violations(self) -> bool:
        """Vérifie s'il y a des violations de haute sévérité."""
        return any(
            v.severity == ViolationSeverity.HIGH
            for v in self.violations
        )

class GuardrailSystem:
    """Système de garde-fous pour les agents IA."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._default_config()

        # Modèles de détection (à étendre)
        self.prompt_injection_patterns = [
            r"(?i)ignore.*(previous|above|instructions)",
            r"(?i)system.*prompt",
            r"(?i)role.*play",
            r"(?i)you are now",
            r"(?i)forget.*instructions",
            r"(?i)important.*secret",
            r"(?i)disregard.*previous",
        ]

        self.sensitive_data_patterns = [
            # Emails
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            # Numéros de carte de crédit (simplifié)
            r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            # Numéros de sécurité sociale (US)
            r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b',
        ]

        self.toxic_keywords = [
            # Liste simplifiée - à remplacer par une liste complète
            "hate", "violence", "harassment", "discrimination",
            "illegal", "harmful", "dangerous"
        ]

    def _default_config(self) -> Dict[str, Any]:
        """Retourne la configuration par défaut."""
        return {
            'enable_prompt_injection_detection': True,
            'enable_toxic_content_filter': True,
            'enable_sensitive_data_detection': True,
            'enable_tool_authorization': True,
            'block_on_high_severity': True,
            'log_all_violations': True,
            'max_context_length': 8000,  # tokens
            'rate_limit_requests_per_minute': 60,
        }

    def check_input(
        self,
        input_text: str,
        user_id: int,
        agent_name: str,
        service_slug: str
    ) -> GuardrailResult:
        """
        Vérifie une entrée utilisateur avant traitement.

        Args:
            input_text: Texte d'entrée
            user_id: ID de l'utilisateur
            agent_name: Nom de l'agent
            service_slug: Slug du service

        Returns:
            GuardrailResult: Résultat de la vérification
        """
        result = GuardrailResult(allowed=True)

        # Vérifier les injections de prompt
        if self.config.get('enable_prompt_injection_detection', True):
            self._check_prompt_injection(input_text, result)

        # Vérifier le contenu toxique
        if self.config.get('enable_toxic_content_filter', True):
            self._check_toxic_content(input_text, result)

        # Vérifier les données sensibles
        if self.config.get('enable_sensitive_data_detection', True):
            self._check_sensitive_data(input_text, result)

        # Vérifier la longueur du contexte
        self._check_context_length(input_text, result)

        # Bloquer si configuration activée et violation haute sévérité
        if (self.config.get('block_on_high_severity', True) and
                result.has_high_severity_violations()):
            result.allowed = False

        # Loguer les violations si configuré
        if self.config.get('log_all_violations', True) and result.has_violations():
            self._log_violations(result, user_id, agent_name, service_slug)

        return result

    def check_output(
        self,
        output_text: str,
        user_id: int,
        agent_name: str,
        service_slug: str
    ) -> GuardrailResult:
        """
        Vérifie une sortie d'agent avant de la retourner à l'utilisateur.

        Args:
            output_text: Texte de sortie
            user_id: ID de l'utilisateur
            agent_name: Nom de l'agent
            service_slug: Slug du service

        Returns:
            GuardrailResult: Résultat de la vérification
        """
        result = GuardrailResult(allowed=True)

        # Vérifier le contenu toxique dans la sortie
        if self.config.get('enable_toxic_content_filter', True):
            self._check_toxic_content(output_text, result)

        # Vérifier les données sensibles dans la sortie
        if self.config.get('enable_sensitive_data_detection', True):
            self._check_sensitive_data(output_text, result)

        # Bloquer si configuration activée et violation haute sévérité
        if (self.config.get('block_on_high_severity', True) and
                result.has_high_severity_violations()):
            result.allowed = False
            # Filtrer la sortie
            result.filtered_output = self._filter_output(output_text)

        return result

    def check_tool_usage(
        self,
        tool_name: str,
        user_id: int,
        agent_name: str,
        service_slug: str,
        tool_params: Dict[str, Any]
    ) -> GuardrailResult:
        """
        Vérifie l'utilisation d'un outil par un agent.

        Args:
            tool_name: Nom de l'outil
            user_id: ID de l'utilisateur
            agent_name: Nom de l'agent
            service_slug: Slug du service
            tool_params: Paramètres de l'outil

        Returns:
            GuardrailResult: Résultat de la vérification
        """
        result = GuardrailResult(allowed=True)

        if self.config.get('enable_tool_authorization', True):
            # Vérifier si l'agent est autorisé à utiliser cet outil
            # (À implémenter selon la configuration des agents)
            authorized = self._is_tool_authorized(tool_name, agent_name, service_slug)
            if not authorized:
                result.add_violation(
                    ViolationType.UNAUTHORIZED_TOOL,
                    ViolationSeverity.HIGH,
                    f"Agent '{agent_name}' is not authorized to use tool '{tool_name}'",
                    {'tool_name': tool_name, 'agent_name': agent_name}
                )

        # Vérifier les paramètres sensibles
        self._check_tool_parameters(tool_params, result)

        # Bloquer si configuration activée et violation haute sévérité
        if (self.config.get('block_on_high_severity', True) and
                result.has_high_severity_violations()):
            result.allowed = False

        return result

    def _check_prompt_injection(self, text: str, result: GuardrailResult) -> None:
        """Vérifie les tentatives d'injection de prompt."""
        for pattern in self.prompt_injection_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                result.add_violation(
                    ViolationType.PROMPT_INJECTION,
                    ViolationSeverity.HIGH,
                    "Potential prompt injection detected",
                    {'pattern': pattern, 'text_snippet': text[:100]}
                )
                break  # Une détection suffit

    def _check_toxic_content(self, text: str, result: GuardrailResult) -> None:
        """Vérifie le contenu toxique."""
        text_lower = text.lower()
        for keyword in self.toxic_keywords:
            if keyword in text_lower:
                result.add_violation(
                    ViolationType.TOXIC_CONTENT,
                    ViolationSeverity.MEDIUM,
                    f"Potential toxic content detected with keyword: {keyword}",
                    {'keyword': keyword, 'text_snippet': text[:100]}
                )
                break

    def _check_sensitive_data(self, text: str, result: GuardrailResult) -> None:
        """Vérifie les données sensibles."""
        for pattern in self.sensitive_data_patterns:
            matches = re.findall(pattern, text)
            if matches:
                # Masquer les données sensibles dans les logs
                masked_matches = [self._mask_sensitive_data(m) for m in matches[:3]]
                result.add_violation(
                    ViolationType.SENSITIVE_DATA,
                    ViolationSeverity.MEDIUM,
                    f"Sensitive data detected: {len(matches)} occurrence(s)",
                    {
                        'pattern': pattern,
                        'match_count': len(matches),
                        'sample_matches': masked_matches
                    }
                )
                break

    def _check_context_length(self, text: str, result: GuardrailResult) -> None:
        """Vérifie la longueur du contexte."""
        max_length = self.config.get('max_context_length', 8000)
        # Estimation simplifiée: 4 caractères ≈ 1 token
        estimated_tokens = len(text) / 4

        if estimated_tokens > max_length:
            result.add_violation(
                ViolationType.CONTEXT_LENGTH,
                ViolationSeverity.LOW,
                f"Context length exceeds limit: {estimated_tokens:.0f} tokens > {max_length}",
                {'estimated_tokens': estimated_tokens, 'max_tokens': max_length}
            )

    def _check_tool_parameters(
        self,
        params: Dict[str, Any],
        result: GuardrailResult
    ) -> None:
        """Vérifie les paramètres des outils pour les données sensibles."""
        # Convertir les paramètres en texte pour la vérification
        import json
        params_text = json.dumps(params)

        self._check_sensitive_data(params_text, result)

    def _is_tool_authorized(
        self,
        tool_name: str,
        agent_name: str,
        service_slug: str
    ) -> bool:
        """
        Vérifie si un agent est autorisé à utiliser un outil.

        À implémenter avec la configuration réelle des agents.
        """
        # Placeholder: tous les outils sont autorisés
        # Dans l'implémentation réelle, vérifier la configuration du service
        return True

    def _filter_output(self, output_text: str) -> str:
        """Filtre une sortie contenant des violations."""
        # Remplacer les données sensibles
        filtered_text = output_text
        for pattern in self.sensitive_data_patterns:
            filtered_text = re.sub(
                pattern,
                '[SENSITIVE_DATA_REDACTED]',
                filtered_text
            )

        return filtered_text

    def _mask_sensitive_data(self, data: str) -> str:
        """Masque les données sensibles pour les logs."""
        if len(data) <= 4:
            return "***"
        return data[:2] + "***" + data[-2:]

    def _log_violations(
        self,
        result: GuardrailResult,
        user_id: int,
        agent_name: str,
        service_slug: str
    ) -> None:
        """Logue les violations détectées."""
        for violation in result.violations:
            logger.warning(
                f"Guardrail violation detected - "
                f"User: {user_id}, Agent: {agent_name}, Service: {service_slug}, "
                f"Type: {violation.type}, Severity: {violation.severity}, "
                f"Message: {violation.message}"
            )