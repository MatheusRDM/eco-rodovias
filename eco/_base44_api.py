"""
_base44_api.py — Cliente Python direto para API Base44
=======================================================
Base URL : https://aevias-controle.base44.app/api/apps/{APP_ID}/entities/{Entity}
Auth     : Bearer token (JWT, válido ~3 meses)
Token    : st.secrets["base44_token"]  (produção) ou variável local (dev)

Entidades disponíveis:
  DiarioObra, EnsaioCAUQ, ChecklistUsina, ChecklistAplicacao,
  AcompanhamentoCarga, AcompanhamentoUsinagem, EnsaioDensidadeInSitu,
  EnsaioGranulometriaIndividual, EnsaioManchaPendulo, EnsaioVigaBenkelman,
  EnsaioProctor, EnsaioTaxaMRAF, EnsaioTaxaPinturaImprimacao,
  ChecklistMRAF, ChecklistTerraplanagem, ChecklistConcretagem,
  ChecklistReciclagem, EnsaioSondagem, BoletimSondagem, BoletimSondagemTrado
"""
import requests
import streamlit as st
import logging

logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTES
# =============================================================================
_APP_ID  = "68a7599ee3fb9205cfb852ec"
_BASE_URL = f"https://aevias-controle.base44.app/api/apps/{_APP_ID}/entities"

# Token de fallback local (DEV) — substitua quando expirar em ~16/07/2026
_TOKEN_LOCAL = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJzdWIiOiJtYXRoZXVzLnJlc2VuZGVAYWZpcm1hZXZpYXMuY29tLmJyIiwiZXhwIjoxNzg0MjAxNzQzLCJpYXQiOjE3NzY0MjU3NDN9"
    ".nkIJL99iRM3asFuS3hv1XQMqK0aCUWr7CupxElwM15o"
)


def _get_token() -> str:
    """Retorna token JWT — secrets (cloud) ou fallback local (dev)."""
    try:
        t = st.secrets.get("base44_token", "")
        if t:
            return t
    except Exception:
        pass
    return _TOKEN_LOCAL


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {_get_token()}",
        "Content-Type": "application/json",
        "X-App-Id": _APP_ID,
    }


# =============================================================================
# FUNÇÃO PRINCIPAL
# =============================================================================

@st.cache_data(ttl=300, show_spinner=False)
def listar(entidade: str) -> list[dict]:
    """
    Busca todos os registros de uma entidade Base44.

    Parâmetros
    ----------
    entidade : str
        Nome exato da entidade (ex: "DiarioObra", "EnsaioCAUQ")

    Retorna
    -------
    list[dict] — lista de registros (vazia se erro ou sem dados)
    """
    url = f"{_BASE_URL}/{entidade}"
    try:
        resp = requests.get(url, headers=_headers(), timeout=30)
        if resp.status_code == 401:
            logger.error(f"[Base44] Token expirado ou inválido para {entidade}")
            st.error("⚠️ Token Base44 expirado. Atualize `base44_token` nos secrets.")
            return []
        if resp.status_code != 200:
            logger.error(f"[Base44] HTTP {resp.status_code} para {entidade}: {resp.text[:200]}")
            return []
        data = resp.json()
        return data if isinstance(data, list) else []
    except requests.exceptions.Timeout:
        logger.warning(f"[Base44] Timeout ao buscar {entidade}")
        return []
    except Exception as e:
        logger.error(f"[Base44] Erro ao buscar {entidade}: {e}")
        return []


@st.cache_data(ttl=300, show_spinner=False)
def buscar(entidade: str, id: str) -> dict | None:
    """Busca um registro específico por ID."""
    url = f"{_BASE_URL}/{entidade}/{id}"
    try:
        resp = requests.get(url, headers=_headers(), timeout=15)
        if resp.status_code == 200:
            return resp.json()
    except Exception as e:
        logger.error(f"[Base44] Erro ao buscar {entidade}/{id}: {e}")
    return None


def token_info() -> dict:
    """Retorna informações do token atual (expiração, email)."""
    import base64, json, time
    try:
        token = _get_token()
        parts = token.split(".")
        payload = json.loads(base64.b64decode(parts[1] + "=="))
        exp = payload.get("exp", 0)
        dias_restantes = max(0, int((exp - time.time()) / 86400))
        return {
            "email": payload.get("sub", "?"),
            "expira_em": exp,
            "dias_restantes": dias_restantes,
            "expirado": time.time() > exp,
        }
    except Exception:
        return {"expirado": True, "dias_restantes": 0}
