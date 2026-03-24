"""
Moteur d'évaluation des flows d'onboarding.

Charge un flow JSON, évalue les règles de scoring sur les réponses
d'un utilisateur, et retourne le résultat calculé.
"""

import json
import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

FLOWS_DIR = Path(__file__).parent / "flows"


def load_flow(flow_id: str) -> dict:
    """
    Charge un flow depuis son fichier JSON.
    Sécurité : empêche la traversée de répertoire.
    """
    # Validation basique du flow_id pour éviter la traversée de répertoire
    if not flow_id or ".." in flow_id or "/" in flow_id or "\\" in flow_id:
        raise ValueError(f"ID de flow invalide : {flow_id}")

    path = FLOWS_DIR / f"{flow_id}.json"
    if not path.exists():
        raise FileNotFoundError(f"Flow introuvable : {flow_id}")
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def evaluate_scoring(flow: dict, answers: dict[str, str]) -> dict:
    """
    Évalue les règles de scoring et retourne le résultat correspondant.

    Les règles sont évaluées dans l'ordre — la première qui correspond
    gagne. Si aucune règle ne correspond, le résultat par défaut est
    retourné.

    Args:
        flow:    Configuration du flow chargée depuis JSON
        answers: Dictionnaire {step_id: valeur_choisie}

    Returns:
        Dictionnaire contenant profile, score, role, label
    """
    scoring = flow.get("scoring", {})
    rules   = scoring.get("rules", [])
    default = scoring.get("default", {
        "profile": "standard", "score": 0,
        "role": "user", "label": "Utilisateur"
    })

    for rule in rules:
        conditions = rule.get("conditions", {})
        # Toutes les conditions de la règle doivent être satisfaites
        if all(answers.get(key) == value
               for key, value in conditions.items()):
            logger.debug(f"onboarding.scoring.match rule={rule}")
            return rule["result"]

    logger.debug("onboarding.scoring.default")
    return default


def render_result_screen(flow: dict, scoring_result: dict) -> dict:
    """
    Prépare l'écran de résultat en substituant les variables.

    Les variables {{ label }}, {{ score }}, {{ profile }} sont
    remplacées par les valeurs du scoring.
    """
    screen = flow.get("result_screen", {})
    label  = scoring_result.get("label", "")
    score  = scoring_result.get("score", 0)

    def substitute(text: str | None) -> str | None:
        if not text:
            return text
        return (text
                .replace("{{ label }}", label)
                .replace("{{ score }}", str(score))
                .replace("{{ profile }}", scoring_result.get("profile", "")))

    return {
        "title":          substitute(screen.get("title", "")),
        "description":    substitute(screen.get("description", "")),
        "show_score":     screen.get("show_score", False),
        "score":          score,
        "label":          label,
        "cta_primary":    screen.get("cta_primary", "S'inscrire"),
        "cta_secondary":  screen.get("cta_secondary"),
    }