"""
Modèles SQLAlchemy pour la gestion des utilisateurs, authentification et logs.

Ce module définit les entités principales :
- User : Utilisateurs enregistrés avec rôles et permissions
- WaitlistEntry : Liste d'attente avec système d'invitation
- RefreshToken : Gestion des sessions (JWT refresh tokens)
- ActivityLog : Journal d'activité pour audit et sécurité
"""

import enum
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Enum,
    ForeignKey, Text, Float, JSON, UniqueConstraint
)
from sqlalchemy.orm import relationship, backref
from sqlalchemy.sql import func
from .database import Base

class UserRole(str, enum.Enum):
    """
    Énumération des rôles utilisateur disponibles dans le système.
    
    Les rôles sont hiérarchisés du plus restrictif au plus permissif :
    - anonymous : Utilisateur non connecté
    - waitlist : Inscrit à la liste d'attente, accès limité
    - user : Utilisateur standard vérifié
    - premium : Utilisateur avec fonctionnalités payantes
    - admin : Administrateur avec accès complet
    """
    anonymous = "anonymous"
    waitlist = "waitlist"
    user = "user"
    premium = "premium"
    admin = "admin"


class User(Base):
    """
    Modèle représentant un utilisateur enregistré dans le système.
    
    Gère l'authentification, les permissions via rôles, et les relations
    avec les tokens de rafraîchissement et les logs d'activité.
    
    Attributes:
        id: Identifiant unique
        email: Adresse email unique (utilisée pour l'authentification)
        hashed_password: Mot de passe hashé (bcrypt/argon2)
        full_name: Nom complet affiché (optionnel)
        role: Niveau de permissions dans le système
        is_active: Compte actif ou désactivé (bannissement/soft delete)
        is_verified: Email confirmé via lien de vérification
        created_at: Date de création du compte (immutable)
        updated_at: Date de dernière modification (auto-update)
    """
    
    __tablename__ = "users"
    
    # Identification et authentification
    id = Column(
        Integer, 
        primary_key=True, 
        index=True,
    )
    email = Column(
        String, 
        unique=True, 
        nullable=False, 
        index=True,
    )
    hashed_password = Column(
        String, 
        nullable=False,
    )
    
    # Profil
    full_name = Column(
        String, 
        nullable=True,
    )
    
    # Permissions et état
    role = Column(
        Enum(UserRole), 
        default=UserRole.user,
        nullable=False,
    )
    is_active = Column(
        Boolean, 
        default=True, 
        nullable=False,
    )
    is_verified = Column(
        Boolean, 
        default=False, 
        nullable=False,
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(), 
        onupdate=func.now(),
    )
    
    # Relations
    refresh_tokens = relationship(
        "RefreshToken", 
        back_populates="user",
        cascade="all, delete-orphan",
    )
    activity_logs = relationship(
        "ActivityLog", 
        back_populates="user",
        cascade="all, delete-orphan",
    )
    
    def __repr__(self) -> str:
        """Représentation concise pour le débogage."""
        return f"<User(id={self.id}, email='{self.email}', role={self.role})>"
    
    def has_role(self, role: UserRole) -> bool:
        """
        Vérifie si l'utilisateur possède au moins le rôle spécifié.
        
        Args:
            role: Rôle minimum requis
            
        Returns:
            True si l'utilisateur a le rôle ou un rôle supérieur
        """
        role_hierarchy = {
            UserRole.anonymous: 0,
            UserRole.waitlist: 1,
            UserRole.user: 2,
            UserRole.premium: 3,
            UserRole.admin: 4,
        }
        return role_hierarchy.get(self.role, 0) >= role_hierarchy.get(role, 0)


class WaitlistEntry(Base):
    """
    Modèle pour la liste d'attente avec système d'invitation.
    
    Permet de gérer les inscriptions avant l'ouverture complète
    du service, avec conversion éventuelle en compte utilisateur.
    
    Attributes:
        id: Identifiant unique
        email: Email inscrit (unique pour éviter les doublons)
        created_at: Date d'inscription initiale
        invited_at: Date d'envoi de l'invitation (null si pas encore invité)
        invitation_token: Token unique pour le lien d'invitation
    """
    
    __tablename__ = "waitlist"
    
    id = Column(
        Integer, 
        primary_key=True, 
        index=True,
    )
    email = Column(
        String, 
        unique=True, 
        nullable=False, 
        index=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    invited_at = Column(
        DateTime(timezone=True), 
        nullable=True,
    )
    invitation_token = Column(
        String, 
        unique=True, 
        nullable=True, 
        index=True,
    )
    
    def __repr__(self) -> str:
        status = "invited" if self.invited_at else "pending"
        return f"<WaitlistEntry(id={self.id}, email='{self.email}', status={status})>"
    
    def is_invited(self) -> bool:
        """Vérifie si l'entrée a déjà reçu une invitation."""
        return self.invited_at is not None and self.invitation_token is not None


class RefreshToken(Base):
    """
    Modèle pour la gestion des tokens de rafraîchissement JWT.
    
    Permet l'invalidation côté serveur des sessions et la détection
    de vol de tokens (rotation sécurisée).
    
    Attributes:
        id: Identifiant interne
        user_id: Référence vers l'utilisateur propriétaire
        token: Hash du token (stocké et non le token en clair)
        expires_at: Date d'expiration du token
        created_at: Date de création du token
        revoked: Indique si le token a été révoqué manuellement
    """
    
    __tablename__ = "refresh_tokens"
    
    id = Column(
        Integer, 
        primary_key=True, 
        index=True,
    )
    user_id = Column(
        Integer, 
        ForeignKey("users.id", ondelete="CASCADE"), 
        nullable=False,
    )
    token = Column(
        String, 
        unique=True, 
        nullable=False, 
        index=True,
    )
    expires_at = Column(
        DateTime(timezone=True), 
        nullable=False,
    )
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
    )
    revoked = Column(
        Boolean, 
        default=False, 
        nullable=False,
    )
    
    # Relation inverse vers User
    user = relationship(
        "User", 
        back_populates="refresh_tokens",
    )
    
    def __repr__(self) -> str:
        status = "revoked" if self.revoked else "active"
        return f"<RefreshToken(id={self.id}, user_id={self.user_id}, status={status})>"
    
    def is_valid(self) -> bool:
        """
        Vérifie si le token est encore valide (non expiré et non révoqué).
        
        Returns:
            True si le token peut être utilisé pour rafraîchir l'accès
        """
        from datetime import datetime, timezone
        return not self.revoked and self.expires_at > datetime.now(timezone.utc)


class ActivityLog(Base):
    """
    Modèle pour le journal d'activité et d'audit.
    
    Enregistre les actions importantes pour la sécurité et le debugging :
    connexions, modifications de profil, actions administratives, etc.
    
    Attributes:
        id: Identifiant unique du log
        user_id: Référence vers l'utilisateur (null pour actions anonymes)
        action: Type d'action effectuée (ex: 'login', 'password_change')
        ip_address: Adresse IP source (pour détection d'anomalies)
        user_agent: Navigateur/client utilisé
        details: Informations supplémentaires en JSON/texte
        created_at: Date exacte de l'action
    """
    
    __tablename__ = "activity_logs"
    
    id = Column(
        Integer, 
        primary_key=True, 
        index=True,
    )
    user_id = Column(
        Integer, 
        ForeignKey("users.id", ondelete="SET NULL"), 
        nullable=True,
    )
    action = Column(
        String, 
        nullable=False,
    )
    ip_address = Column(
        String, 
        nullable=True,
    )
    user_agent = Column(
        Text, 
        nullable=True,
    )
    details = Column(
        Text, 
        nullable=True,
    )
    created_at = Column(
        DateTime(timezone=True), 
        server_default=func.now(),
    )
    
    # Relation inverse vers User
    user = relationship(
        "User", 
        back_populates="activity_logs",
    )
    
    def __repr__(self) -> str:
        user_info = f"user_id={self.user_id}" if self.user_id else "anonymous"
        return f"<ActivityLog(id={self.id}, action='{self.action}', {user_info})>"

# backend/app/models.py — ajouter

class UserProfile(Base):
    """
    Stocke les réponses d'onboarding et le profil calculé.
    Séparé de User pour ne pas alourdir la table principale.
    """
    __tablename__ = "user_profiles"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),
                        unique=True, nullable=False)
    flow_id    = Column(String, nullable=False)
    answers    = Column(Text, nullable=True)   # JSON sérialisé
    profile    = Column(String, nullable=True)  # tag calculé
    score      = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(),
                        onupdate=func.now())

    user = relationship("User", backref=backref("profile", uselist=False))

class Visit(Base):
    """
    Enregistre chaque visite avec géolocalisation.

    L'IP est hashée (SHA256 + salt) avant stockage pour
    conformité RGPD. On conserve la géolocalisation mais
    pas l'IP en clair.
    """
    __tablename__ = "visits"

    id           = Column(Integer, primary_key=True, index=True)
    ip_hash      = Column(String, nullable=True, index=True)
    country_code = Column(String(2), nullable=True, index=True)
    country_name = Column(String, nullable=True)
    region       = Column(String, nullable=True)
    city         = Column(String, nullable=True)
    latitude     = Column(Float, nullable=True)
    longitude    = Column(Float, nullable=True)
    path         = Column(String, nullable=True)
    user_id      = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"),
                          nullable=True, index=True)
    user_role    = Column(String, nullable=True)  # snapshot du rôle au moment
    created_at   = Column(DateTime(timezone=True),
                          server_default=func.now(), index=True)

class AccessRole(str, enum.Enum):
    user    = "user"
    premium = "premium"
    admin   = "admin"


class Tutorial(Base):
    """
    Tutorial — conteneur de leçons ordonnées.
    Un tutorial peut être libre (user) ou premium.
    """
    __tablename__ = "tutorials"

    id           = Column(Integer, primary_key=True, index=True)
    title        = Column(String, nullable=False)
    slug         = Column(String, unique=True, nullable=False, index=True)
    description  = Column(Text, nullable=True)
    cover_image  = Column(String, nullable=True)
    access_role  = Column(Enum(AccessRole), default=AccessRole.user,
                          nullable=False)
    is_published = Column(Boolean, default=False, nullable=False)
    lang         = Column(String(5), default="fr", nullable=False, index=True)
    tags        = Column(JSON,    default=list,  nullable=False, server_default="[]")
    is_featured = Column(Boolean, default=False, nullable=False, server_default="false")
    views_count = Column(Integer, default=0,     nullable=False, server_default="0")
    author_id    = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"),
                          nullable=True)
    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), server_default=func.now(),
                          onupdate=func.now())

    lessons = relationship("Lesson", back_populates="tutorial",
                           order_by="Lesson.order",
                           cascade="all, delete-orphan")
    author  = relationship("User")


class Lesson(Base):
    """
    Leçon — unité de contenu Markdown d'un tutorial.
    """
    __tablename__ = "lessons"

    id                = Column(Integer, primary_key=True, index=True)
    tutorial_id       = Column(Integer, ForeignKey("tutorials.id",
                                ondelete="CASCADE"), nullable=False,
                                index=True)
    title             = Column(String, nullable=False)
    slug              = Column(String, nullable=False, index=True)
    order             = Column(Integer, nullable=False, default=0)
    content           = Column(Text, nullable=True)   # Markdown
    duration_minutes  = Column(Integer, nullable=True)
    is_published      = Column(Boolean, default=False, nullable=False)
    created_at        = Column(DateTime(timezone=True),
                               server_default=func.now())
    updated_at        = Column(DateTime(timezone=True),
                               server_default=func.now(),
                               onupdate=func.now())

    tutorial = relationship("Tutorial", back_populates="lessons")

class DbSettings(Base):
    """
    Paramètres de maintenance de la base de données.
    Un seul enregistrement (id=1) mis à jour par l'admin.
    """
    __tablename__ = "db_settings"

    id = Column(Integer, primary_key=True, default=1)

    # Durées de rétention en jours
    tokens_retention_days  = Column(Integer, default=30,  nullable=False)
    visits_retention_days  = Column(Integer, default=90,  nullable=False)
    logs_retention_days    = Column(Integer, default=180, nullable=False)

    # Fréquence du nettoyage automatique
    # "daily" | "weekly" | "monthly" | "disabled"
    cleanup_frequency      = Column(String, default="weekly", nullable=False)

    # Dernière exécution
    last_cleanup_at        = Column(DateTime(timezone=True), nullable=True)

    updated_at = Column(DateTime(timezone=True),
                        server_default=func.now(), onupdate=func.now())


# ==================== Agentic AI Services ====================

class ServiceExecution(Base):
    """
    Exécution d'un service agentic IA.

    Stocke l'historique des exécutions de services pour l'audit,
    la reprise sur erreur, et l'analyse des performances.
    """
    __tablename__ = "service_executions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    service_slug = Column(String, nullable=False, index=True)
    workflow_name = Column(String, nullable=True)
    execution_id = Column(String, unique=True, nullable=False, index=True)  # ID interne pour l'orchestrateur
    input_params = Column(JSON, nullable=True)     # Paramètres d'entrée JSON
    status = Column(String, nullable=False)        # pending, running, completed, failed, cancelled
    result = Column(JSON, nullable=True)           # Résultat JSON
    error_message = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)  # Temps d'exécution total en ms
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Relations
    user = relationship("User", backref="service_executions")
    steps = relationship("ServiceExecutionStep", back_populates="execution",
                         cascade="all, delete-orphan")
    results = relationship("ServiceResult", back_populates="execution",
                           cascade="all, delete-orphan")

class ServiceExecutionStep(Base):
    """
    Étape individuelle dans l'exécution d'un service.

    Permet de tracer l'exécution pas à pas pour le debugging
    et l'analyse des performances.
    """
    __tablename__ = "service_execution_steps"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("service_executions.id"), nullable=False, index=True)
    step_id = Column(String, nullable=False)           # Identifiant de l'étape dans le workflow
    agent_name = Column(String, nullable=True)         # Agent qui a exécuté l'étape
    input_data = Column(JSON, nullable=True)          # Données d'entrée de l'étape
    output_data = Column(JSON, nullable=True)         # Données de sortie de l'étape
    status = Column(String, nullable=False)           # pending, running, completed, failed
    error_message = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)  # Temps d'exécution en ms
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relations
    execution = relationship("ServiceExecution", back_populates="steps")

class ServiceResult(Base):
    """
    Résultat détaillé d'une exécution de service.

    Peut contenir des fichiers, des médias, ou des données structurées
    générées par le service.
    """
    __tablename__ = "service_results"

    id = Column(Integer, primary_key=True, index=True)
    execution_id = Column(Integer, ForeignKey("service_executions.id"), nullable=False, index=True)
    result_type = Column(String, nullable=False)      # text, json, pdf, audio, video, image
    content = Column(Text, nullable=True)            # Contenu textuel ou JSON
    file_path = Column(String, nullable=True)        # Chemin vers le fichier sur le serveur
    file_url = Column(String, nullable=True)         # URL publique du fichier
    file_size = Column(Integer, nullable=True)       # Taille en octets
    mime_type = Column(String, nullable=True)        # Type MIME
    result_metadata = Column(JSON, nullable=True)    # Métadonnées supplémentaires
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relations
    execution = relationship("ServiceExecution", back_populates="results")

class UserServicePreference(Base):
    """
    Préférences utilisateur pour les services agentic IA.

    Stocke les configurations personnalisées, les favoris,
    et les paramètres par défaut pour chaque utilisateur.
    """
    __tablename__ = "user_service_preferences"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    service_slug = Column(String, nullable=False, index=True)
    preferences = Column(JSON, nullable=True)        # Préférences JSON
    is_favorite = Column(Boolean, default=False, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    usage_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(),
                        onupdate=func.now())

    # Contrainte d'unicité
    __table_args__ = (
        UniqueConstraint('user_id', 'service_slug', name='uq_user_service'),
    )

    # Relations
    user = relationship("User", backref="service_preferences")


class SecurityEventType(str, enum.Enum):
    path_scan         = "path_scan"
    brute_force       = "brute_force"
    injection_attempt = "injection_attempt"
    scanner_detected  = "scanner_detected"
    rate_limit        = "rate_limit"
    suspicious_payload = "suspicious_payload"

class SecuritySeverity(str, enum.Enum):
    low      = "low"
    medium   = "medium"
    high     = "high"
    critical = "critical"

class SecurityEvent(Base):
    """
    Événement de sécurité détecté par le middleware ou les routers.

    Capture les tentatives d'intrusion, de scan, d'injection,
    et les dépassements de rate limit.
    """
    __tablename__ = "security_events"

    id          = Column(Integer, primary_key=True, index=True)
    event_type  = Column(String, nullable=False, index=True)
    severity    = Column(String, nullable=False, index=True)
    ip_address  = Column(String, nullable=True,  index=True)
    path        = Column(String, nullable=True)
    method      = Column(String, nullable=True)
    user_agent  = Column(String, nullable=True)
    details     = Column(JSON, nullable=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User", backref="security_events", foreign_keys=[user_id])


# Après le champ lang
