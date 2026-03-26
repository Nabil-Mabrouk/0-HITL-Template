"""
Module de gestion de l'envoi d'emails asynchrones.

Ce module fournit une abstraction pour l'envoi d'emails via SMTP avec :
- Support asynchrone (aiosmtplib) pour ne pas bloquer l'event loop
- Templates Jinja2 pour les emails HTML
- Mode développement qui logue les emails au lieu de les envoyer
- Gestion des différents types d'emails transactionnels
"""

import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

import aiosmtplib
from jinja2 import Environment, FileSystemLoader

from app.config import get_settings

# Logger pour ce module
logger = logging.getLogger(__name__)

# Chargement de la configuration
settings = get_settings()

# Configuration de l'environnement Jinja2 pour les templates d'emails
# Les templates sont stockés dans le dossier 'templates' à côté de ce fichier
template_env = Environment(
    loader=FileSystemLoader(Path(__file__).parent / "templates"),
    autoescape=True,  # Sécurité : échappement automatique du HTML
    trim_blocks=True,  # Supprime les lignes vides dans le rendu
    lstrip_blocks=True  # Supprime l'indentation des blocs
)


async def send_email(to: str, subject: str, html: str) -> bool:
    """
    Envoie un email HTML de manière asynchrone.
    
    En environnement de développement sans SMTP configuré, l'email est
    simplement logué au lieu d'être envoyé (pratique pour le debugging).
    
    Args:
        to: Adresse email du destinataire
        subject: Sujet de l'email
        html: Contenu HTML de l'email
        
    Returns:
        bool: True si l'email est envoyé (ou logué en dev), False en cas d'erreur
        
    Note:
        Utilise STARTTLS pour sécuriser la connexion SMTP.
        Le port 587 est utilisé par défaut (port standard TLS).
    """
    # Mode développement : loguer l'email au lieu de l'envoyer
    if settings.environment == "development" and not settings.smtp_user:
        logger.info("[DEV EMAIL] Mode simulation activé (SMTP non configuré)")
        logger.info(f"[DEV EMAIL] Destinataire: {to}")
        logger.info(f"[DEV EMAIL] Sujet: {subject}")
        logger.info(f"[DEV EMAIL] Contenu (tronqué): {html[:200]}...")
        return True

    # Construction du message MIME multipart
    # "alternative" permet au client mail de choisir entre HTML et texte brut
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{settings.email_from_name} <{settings.email_from}>"
    msg["To"] = to
    
    # Attachement du contenu HTML
    # Note: On pourrait ajouter une version texte brut pour les clients anciens
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        validate = settings.environment != "development"
        # Envoi asynchrone via SMTP avec STARTTLS
        await aiosmtplib.send(
            msg,
            hostname=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            start_tls=True,# Active TLS pour sécuriser la connexion
            validate_certs=validate,
        )
        logger.info(f"email.sent.success to={to} subject={subject}")
        return True
        
    except aiosmtplib.SMTPAuthenticationError as e:
        logger.error(f"email.send.auth_error to={to}: {e}")
        return False
    except aiosmtplib.SMTPRecipientsRefused as e:
        logger.error(f"email.send.recipient_refused to={to}: {e}")
        return False
    except Exception as e:
        # Capture générique pour les erreurs réseau/serveur
        logger.error(f"email.send.error to={to}: {type(e).__name__}: {e}")
        return False


async def send_verification_email(email: str, full_name: str, token: str) -> bool:
    """
    Envoie l'email de vérification d'adresse email.
    
    Cet email contient un lien unique permettant à l'utilisateur de
    confirmer son adresse email et d'activer son compte.
    
    Args:
        email: Adresse email du destinataire
        full_name: Nom complet de l'utilisateur (pour personnalisation)
        token: Token JWT signé pour la vérification
        
    Returns:
        bool: True si l'email est envoyé avec succès
        
    Template:
        verify_email.html : Doit contenir {{ full_name }} et {{ verify_url }}
    """
    # Construction de l'URL de vérification
    verify_url = f"{settings.frontend_url}/verify-email?token={token}"
    
    # Rendu du template avec les variables
    html = template_env.get_template("verify_email.html").render(
        full_name=full_name,
        verify_url=verify_url
    )
    
    return await send_email(
        to=email,
        subject="Confirmez votre adresse email",
        html=html
    )


async def send_reset_password_email(email: str, token: str) -> bool:
    """
    Envoie l'email de réinitialisation de mot de passe.
    
    Cet email contient un lien sécurisé permettant à l'utilisateur de
    définir un nouveau mot de passe. Le lien expire après 24h.
    
    Args:
        email: Adresse email du compte à réinitialiser
        token: Token JWT signé pour l'autorisation du reset
        
    Returns:
        bool: True si l'email est envoyé avec succès
        
    Security:
        Le token expire après 24h (configuré dans security.py).
        L'email ne révèle pas si le compte existe (privacy).
        
    Template:
        reset_password.html : Doit contenir {{ reset_url }}
    """
    reset_url = f"{settings.frontend_url}/reset-password?token={token}"
    
    html = template_env.get_template("reset_password.html").render(
        reset_url=reset_url
    )
    
    return await send_email(
        to=email,
        subject="Réinitialisation de votre mot de passe",
        html=html
    )


async def send_invitation_email(
    email: str, 
    token: str, 
    app_name: str = "0-HITL"
) -> bool:
    """
    Envoie une invitation à rejoindre la plateforme.
    
    Utilisé pour convertir les inscrits de la waitlist en utilisateurs
    actifs via un lien d'inscription privilégié.
    
    Args:
        email: Adresse email invitée
        token: Token d'invitation unique (stocké en base)
        app_name: Nom de l'application (pour personnalisation)
        
    Returns:
        bool: True si l'email est envoyé avec succès
        
    Template:
        invitation.html : Doit contenir {{ invite_url }} et {{ app_name }}
    """
    invite_url = f"{settings.frontend_url}/register?invitation={token}"
    
    html = template_env.get_template("invitation.html").render(
        invite_url=invite_url,
        app_name=app_name
    )
    
    return await send_email(
        to=email,
        subject=f"Votre invitation à rejoindre {app_name} !",
        html=html
    )

async def send_purchase_confirmation(
    email:          str,
    product_name:   str,
    download_token: str,
    expires_at,
) -> bool:
    """
    Envoie la confirmation d'achat avec le lien de téléchargement sécurisé.

    Args:
        email:          Email de l'acheteur
        product_name:   Nom du produit acheté
        download_token: Token pour le lien de téléchargement
        expires_at:     Datetime d'expiration du lien
    """
    download_url = f"{settings.frontend_url}/api/shop/download/{download_token}"
    html = template_env.get_template("purchase_confirmation.html").render(
        product_name=product_name,
        download_url=download_url,
        expires_at=expires_at.strftime("%d/%m/%Y à %H:%M UTC") if expires_at else "48h",
        app_name=settings.email_from_name,
    )
    return await send_email(
        to=email,
        subject=f"Votre achat : {product_name}",
        html=html,
    )


async def send_admin_welcome_email(email: str, full_name: str,
                                   token: str) -> bool:
    url  = f"{settings.frontend_url}/reset-password?token={token}"
    html = template_env.get_template("admin_welcome.html").render(
        full_name = full_name,
        email     = email,
        app_name  = settings.email_from_name,
        reset_url = url,
    )
    return await send_email(
        email,
        f"Votre compte administrateur {settings.email_from_name}",
        html,
    )