"""
=========================================================================
CLOUD CONFIG — ECO RODOVIAS (standalone)
=========================================================================
Detecta ambiente (local com Y: drive vs cloud) e fornece credenciais.
=========================================================================
"""
import os
import logging
import pandas as pd
import streamlit as st

logger = logging.getLogger(__name__)

# =============================================================================
# DETECÇÃO DE AMBIENTE
# =============================================================================

_GDRIVE_PROBE = r"G:\.shortcut-targets-by-id\1NUJ7pNAqedohSrLjiwFErFrtVqVZkrjk"
IS_CLOUD = not os.path.isdir(_GDRIVE_PROBE)

_PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR     = os.path.join(_PROJECT_ROOT, "cache_certificados")
IMAGENS_DIR   = os.path.join(_PROJECT_ROOT, "Imagens")

# =============================================================================
# IMAGENS
# =============================================================================

LOGO_HORIZONTAL = os.path.join(IMAGENS_DIR, "AE - Logo Hor Principal_2.png")
_SELO_ICON      = os.path.join(IMAGENS_DIR, "logo_icon.png")
LOGO_SELO       = _SELO_ICON
LOGO_PADRONAGEM = os.path.join(IMAGENS_DIR, "Padronagem_2.png")


def get_logo_path(tipo: str = "horizontal") -> str | None:
    _LOCAL = {
        "horizontal": LOGO_HORIZONTAL,
        "selo":       LOGO_SELO,
        "padronagem": LOGO_PADRONAGEM,
    }
    local = _LOCAL.get(tipo, LOGO_HORIZONTAL)
    return local if os.path.exists(local) else None


# =============================================================================
# CACHE DE DADOS (parquet genérico — mantido para compatibilidade)
# =============================================================================

@st.cache_data(ttl=3600, show_spinner=False)
def carregar_parquet_cache(nome: str) -> pd.DataFrame:
    path = os.path.join(CACHE_DIR, f"{nome}.parquet")
    if os.path.exists(path):
        return pd.read_parquet(path)
    logger.warning(f"[cloud_config] Cache não encontrado: {path}")
    return pd.DataFrame()


# =============================================================================
# CREDENCIAIS
# =============================================================================

def get_usuarios() -> dict:
    """
    Retorna usuários permitidos no app ECO standalone.
    Produção: lê de st.secrets['usuarios'].
    Dev local: fallback hardcoded (apenas Eco e Dev).
    """
    try:
        if hasattr(st, "secrets") and "usuarios" in st.secrets:
            return dict(st.secrets["usuarios"])
    except Exception:
        pass

    return {
        "Eco": {
            "senha":   "Afirmaevias",
            "paginas": ["Eco Rodovias"],
        },
        "Dev": {
            "senha":   "Afirmaevias",
            "paginas": ["Eco Rodovias"],
        },
    }


# =============================================================================
# INFO DE AMBIENTE
# =============================================================================

def mostrar_info_ambiente():
    modo = "☁️ Cloud" if IS_CLOUD else "💻 Local"
    st.sidebar.caption(f"Ambiente: {modo}")
