"""
Service de géolocalisation IP via MaxMind GeoLite2-City.

La résolution est locale (fichier .mmdb) — aucune requête externe,
latence < 1ms, RGPD friendly.
"""

import hashlib
import logging
import maxminddb
from pathlib import Path
from app.config import get_settings

logger   = logging.getLogger(__name__)
settings = get_settings()

# Chargement unique au démarrage — le reader est thread-safe
_reader: maxminddb.Reader | None = None


def get_reader() -> maxminddb.Reader | None:
    global _reader
    if _reader is None:
        path = Path(settings.geoip_db_path)
        if not path.exists():
            logger.warning(f"geoip.db_not_found path={path}")
            return None
        try:
            _reader = maxminddb.open_database(str(path))
            logger.info(f"geoip.loaded path={path}")
        except Exception as e:
            logger.error(f"geoip.load_error: {e}")
    return _reader


def hash_ip(ip: str) -> str:
    """Hash l'IP avec un salt secret pour conformité RGPD."""
    salt = settings.secret_key[:16]
    return hashlib.sha256(f"{salt}:{ip}".encode()).hexdigest()


def geolocate(ip: str) -> dict:
    """
    Retourne les informations géographiques pour une IP.

    Returns:
        dict avec country_code, country_name, region, city,
        latitude, longitude — valeurs None si IP non trouvée
        ou base non disponible.
    """
    result = {
        "country_code": None,
        "country_name": None,
        "region":       None,
        "city":         None,
        "latitude":     None,
        "longitude":    None,
    }

    # Ignorer les IPs locales
    if ip in ("127.0.0.1", "::1") or ip.startswith("172.") \
            or ip.startswith("192.168.") or ip.startswith("10."):
        return result

    reader = get_reader()
    if not reader:
        return result

    try:
        data = reader.get(ip)
        if not data:
            return result

        result["country_code"] = data.get("country", {}).get("iso_code")
        result["country_name"] = (
            data.get("country", {})
                .get("names", {})
                .get("fr") or
            data.get("country", {})
                .get("names", {})
                .get("en")
        )
        result["region"] = (
            data.get("subdivisions", [{}])[0]
                .get("names", {})
                .get("fr") or
            data.get("subdivisions", [{}])[0]
                .get("names", {})
                .get("en")
        )
        result["city"] = (
            data.get("city", {})
                .get("names", {})
                .get("fr") or
            data.get("city", {})
                .get("names", {})
                .get("en")
        )
        location = data.get("location", {})
        result["latitude"]  = location.get("latitude")
        result["longitude"] = location.get("longitude")

    except Exception as e:
        logger.debug(f"geoip.lookup_error ip={ip}: {e}")

    return result