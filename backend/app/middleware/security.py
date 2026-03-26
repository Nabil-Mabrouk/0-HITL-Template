"""
Middleware de sécurité pour détecter et journaliser les tentatives d'intrusion.

Détecte :
- Scans de chemins sensibles (/.git, /.env, /wp-*, /phpinfo, etc.)
- User-agents de scanners connus (nmap, sqlmap, nikto, masscan…)
- Tentatives d'injection (SQL, path traversal, template injection)
- Payloads suspects dans les query strings
"""

import re
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ..database import SessionLocal
from ..models import SecurityEvent, SecurityEventType, SecuritySeverity

logger = logging.getLogger(__name__)

# ── Patterns de chemins suspects ──────────────────────────────────────────────
SUSPICIOUS_PATHS: list[tuple[re.Pattern, SecuritySeverity]] = [
    # Fuites de dépôt Git
    (re.compile(r"^/\.git/",                    re.I), SecuritySeverity.critical),
    (re.compile(r"^/\.gitignore$",              re.I), SecuritySeverity.medium),
    # Fichiers d'environnement
    (re.compile(r"^/\.env",                     re.I), SecuritySeverity.critical),
    (re.compile(r"^/\.aws/",                    re.I), SecuritySeverity.critical),
    (re.compile(r"^/\.ssh/",                    re.I), SecuritySeverity.critical),
    # WordPress
    (re.compile(r"^/wp-",                       re.I), SecuritySeverity.medium),
    (re.compile(r"^/wordpress/",                re.I), SecuritySeverity.medium),
    # PHP commun
    (re.compile(r"phpinfo",                     re.I), SecuritySeverity.high),
    (re.compile(r"^/admin\.php",                re.I), SecuritySeverity.high),
    (re.compile(r"^/xmlrpc\.php",               re.I), SecuritySeverity.high),
    (re.compile(r"\.php$",                      re.I), SecuritySeverity.medium),
    # Panneaux d'admin connus
    (re.compile(r"^/(phpmyadmin|pma|adminer)",  re.I), SecuritySeverity.high),
    (re.compile(r"^/(panel|cpanel|webmail)",    re.I), SecuritySeverity.medium),
    # Fichiers de config et secrets
    (re.compile(r"(config|secret|credential|password|passwd|shadow|htpasswd)", re.I), SecuritySeverity.high),
    (re.compile(r"\.(bak|old|backup|save|swp|orig)$", re.I), SecuritySeverity.medium),
    # Stripe et clés de paiement
    (re.compile(r"stripe",                      re.I), SecuritySeverity.high),
    # Traversée de répertoire
    (re.compile(r"\.\./",                            ), SecuritySeverity.critical),
]

# ── User-agents de scanners ────────────────────────────────────────────────────
SCANNER_UA_PATTERN = re.compile(
    r"(sqlmap|nikto|nmap|masscan|zgrab|nuclei|dirsearch|gobuster|"
    r"ffuf|wfuzz|hydra|medusa|burpsuite|acunetix|nessus|openvas|"
    r"python-requests/|go-http-client|curl/[0-9])",
    re.I,
)

# ── Patterns d'injection ───────────────────────────────────────────────────────
INJECTION_PATTERNS = [
    (re.compile(r"(union\s+select|drop\s+table|insert\s+into|delete\s+from|"
                r"exec\s*\(|xp_cmdshell|information_schema)", re.I), "sql_injection"),
    (re.compile(r"(<script|javascript:|onerror=|onload=|<iframe)", re.I),  "xss"),
    (re.compile(r"(\{\{|\}\}|{%|%}|\$\{)",                               ), "template_injection"),
    (re.compile(r"(;.*whoami|;.*cat\s+/etc|;.*id\s*$|\|.*bash)",  re.I), "command_injection"),
]

# Chemins à ignorer (bruit normal)
IGNORED_PATHS = {"/health", "/api/track", "/sitemap.xml", "/robots.txt", "/llms.txt"}


def _get_ip(request: Request) -> str:
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _log_event(
    ip: str,
    path: str,
    method: str,
    user_agent: str,
    event_type: SecurityEventType,
    severity: SecuritySeverity,
    details: dict,
) -> None:
    try:
        db = SessionLocal()
        event = SecurityEvent(
            event_type = event_type.value,
            severity   = severity.value,
            ip_address = ip,
            path       = path[:500],
            method     = method,
            user_agent = (user_agent or "")[:300],
            details    = details,
        )
        db.add(event)
        db.commit()
    except Exception as e:
        logger.error(f"security.log_failed: {e}")
    finally:
        db.close()


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Inspecte chaque requête entrante et journalise les événements suspects.
    Ne bloque pas les requêtes — journalise uniquement.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        path       = request.url.path
        method     = request.method
        user_agent = request.headers.get("User-Agent", "")
        ip         = _get_ip(request)
        query      = str(request.url.query)

        if path not in IGNORED_PATHS:
            # 1. Scanner user-agent
            if SCANNER_UA_PATTERN.search(user_agent):
                _log_event(ip, path, method, user_agent,
                           SecurityEventType.scanner_detected,
                           SecuritySeverity.high,
                           {"user_agent": user_agent})

            # 2. Chemin suspect
            else:
                for pattern, severity in SUSPICIOUS_PATHS:
                    if pattern.search(path):
                        _log_event(ip, path, method, user_agent,
                                   SecurityEventType.path_scan,
                                   severity,
                                   {"matched_path": path})
                        break

            # 3. Injection dans le query string
            for inj_pattern, inj_type in INJECTION_PATTERNS:
                target = path + "?" + query
                if inj_pattern.search(target):
                    _log_event(ip, path, method, user_agent,
                               SecurityEventType.injection_attempt,
                               SecuritySeverity.critical,
                               {"injection_type": inj_type, "query": query[:300]})
                    break

        return await call_next(request)
