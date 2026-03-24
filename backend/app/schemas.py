"""
Schémas Pydantic pour la validation et la sérialisation des données de la liste d'attente.

Ce module définit les modèles de validation pour :
- La création d'une inscription (WaitlistCreate)
- La réponse après inscription (WaitlistResponse)
"""

from datetime import datetime
import re
from pydantic import BaseModel, EmailStr, field_validator


class WaitlistCreate(BaseModel):
    """
    Schéma de validation pour la création d'une inscription à la liste d'attente.
    
    Valide que l'email fourni est valide et n'appartient pas à un domaine 
    jetable (temporaire).
    
    Attributes:
        email (EmailStr): Adresse email validée et normalisée en minuscules
    """
    
    email: EmailStr
    
    @field_validator("email")
    @classmethod
    def email_not_disposable(cls, v: str) -> str:
        """
        Valide que l'email n'utilise pas un domaine jetable connu.
        
        Cette validation permet de :
        - Réduire les inscriptions frauduleuses
        - Assurer une meilleure qualité de la liste d'attente
        - Éviter les abus par adresses temporaires
        
        Args:
            v: L'adresse email à valider
            
        Returns:
            str: L'email en minuscules si valide
            
        Raises:
            ValueError: Si le domaine de l'email est dans la liste noire
            
        Example:
            >>> WaitlistCreate.email_not_disposable(None, "test@mailinator.com")
            ValueError: Les adresses email temporaires ne sont pas acceptées
        """
        # Liste des domaines d'email jetables courants à bloquer
        disposable = [
            "mailinator.com",
            "guerrillamail.com", 
            "tempmail.com",
            "10minutemail.com",
            "yopmail.com",
            "throwawaymail.com"
        ]
        
        # Extraction du domaine (partie après @)
        domain = v.split("@")[1].lower()
        
        # Vérification contre la liste noire
        if domain in disposable:
            raise ValueError("Les adresses email temporaires ne sont pas acceptées")
        
        # Normalisation en minuscules pour la cohérence en base de données
        return v.lower()


class WaitlistResponse(BaseModel):
    """
    Schéma de réponse après une inscription réussie à la liste d'attente.
    
    Utilisé pour standardiser les réponses API de succès.
    
    Attributes:
        message (str): Message de confirmation pour l'utilisateur
    """
    
    message: str
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "message": "Vous êtes inscrit à la liste d'attente avec succès"
                }
            ]
        }
    }