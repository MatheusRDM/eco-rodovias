"""
_eco_rast_api.py — Logos Rastreamento API layer for ECO Rodovias.
"""
import sys
import os

_PAGES_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR  = os.path.dirname(_PAGES_DIR)
if _PAGES_DIR not in sys.path: sys.path.insert(0, _PAGES_DIR)
if _ROOT_DIR  not in sys.path: sys.path.insert(0, _ROOT_DIR)

import streamlit as st
import requests
import re as _re
import pandas as pd
from datetime import date

from _eco_shared import (
    COR_PRIMARY, COR_ACCENT, COR_BG, COR_CARD, COR_BORDER,
    COR_TEXT, COR_MUTED, COR_OK, COR_COBRAR, COR_NE, COR_ELAB,
    PLOTLY_LAYOUT, PLOTLY_CONFIG,
    _BASE_DIR, _CACHE_DIR, _Y_BASE, _IS_CLOUD,
)

# =============================================================================
# LOGOS RASTREAMENTO — API
# =============================================================================
_LOGOS_BASE = "https://rastrear.logosrastreamento.com.br"
_CORES_VEICULOS = [
    "#FF6B35","#4CC9F0","#F7B731","#7BED9F","#FF4757",
    "#A29BFE","#FD79A8","#00CEC9","#FDCB6E","#6C5CE7",
]

# Nomes possíveis de campos no historicoposicao (o Logos usa variações)
_HIST_ODO_FIELDS = [
    "pos_odometro", "odometro", "hodometro", "pos_hodometro",
    "km", "quilometragem", "pos_km", "distancia",
]
_HIST_LAT_FIELDS = [
    "pos_coordenada_latitude", "latitude", "lat",
    "coordenada_latitude", "pos_latitude",
]
_HIST_LON_FIELDS = [
    "pos_coordenada_longitude", "longitude", "lon", "lng",
    "coordenada_longitude", "pos_longitude",
]
_HIST_VEL_FIELDS = [
    "pos_velocidade", "velocidade", "speed", "vel",
]
_HIST_IGN_FIELDS = [
    "pos_ignicao", "ignicao", "ignition", "motor",
]
_HIST_DT_FIELDS  = [
    "pos_dt_posicao", "dt_posicao", "data_hora", "dataHora",
    "dt", "data", "datetime", "timestamp",
]
_HIST_CID_FIELDS = [
    "pos_end_cidade", "cidade", "municipio", "city",
]
_HIST_UF_FIELDS  = [
    "pos_end_uf", "uf", "estado", "state",
]


def _logos_login():
    """Autentica no Logos e retorna (sess, idcli) com retry logic."""
    import time
    try:
        usuario = st.secrets["logos_usuario"]
        senha   = st.secrets["logos_senha"]
    except Exception:
        usuario = "matheus.resende@afirmaevias.com.br"
        senha   = "19072019Joaquim*"

    sess = requests.Session()
    sess.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36",
    })

    max_retries = 3
    for attempt in range(max_retries):
        try:
            r = sess.get(f"{_LOGOS_BASE}/Identity/Account/Login", timeout=20)
            m = _re.search(r'name="__RequestVerificationToken"[^>]+value="([^"]+)"', r.text)
            token = m.group(1) if m else ""
            
            sess.post(f"{_LOGOS_BASE}/Identity/Account/Login", data={
                "Input.UserName": usuario,
                "Input.Password": senha,
                "__RequestVerificationToken": token,
            }, timeout=20, allow_redirects=True)
            
            idcli = next((c.value for c in sess.cookies if c.name == "IDCLI"), None)
            if idcli:
                return sess, idcli
            
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError) as e:
            if attempt == max_retries - 1:
                raise ConnectionError(f"Não foi possível conectar ao servidor Logos após {max_retries} tentativas. O servidor pode estar fora do ar.")
            time.sleep(2 ** attempt)
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(1)

    raise ValueError("Login falhou — credenciais inválidas ou sessão expirada.")


def _logos_get_eco(sess, idcli):
    """Retorna lista de veículos com ECO no nome (última posição)."""
    r = sess.post(f"{_LOGOS_BASE}/api/ultimaposicao", json={
        "idcliente": int(idcli), "texto": "", "placa": "", "serial": "",
        "descricao": "", "grupoveiculo": "", "idsVeiculos": [],
    }, timeout=20)
    items = r.json() if isinstance(r.json(), list) else r.json().get("data", [])
    return [v for v in items if "ECO" in str(v.get("descricaovel", "")).upper()]


def _logos_get_rota(sess, idveiculo, d_ini, d_fim):
    """Retorna histórico de posições. d_ini/d_fim: 'YYYY-MM-DD HH:MM'"""
    r = sess.post(f"{_LOGOS_BASE}/api/historicoposicao", json={
        "idveiculo": idveiculo, "datainicio": d_ini, "datafinal": d_fim,
    }, timeout=60)
    d = r.json()
    return d if isinstance(d, list) else d.get("data", [])


def _pick(d, fields, default=None):
    """Retorna o primeiro campo encontrado em d dentre a lista fields."""
    for f in fields:
        v = d.get(f)
        if v is not None:
            return v
    return default


def _km_from_hist(hist):
    """
    Calcula km percorridos no histórico — 3 métodos em cascata:
    1) Odômetro (max-min): detecta campo automaticamente.
    2) Velocidade × tempo: Σ(vel_km/h × intervalo_min/60).
    3) Fallback Haversine sobre coordenadas GPS.
    """
    import math

    # ── Método 1: Odômetro (max - min) ────────────────────────────────────────
    odos = []
    for p in hist:
        v = _pick(p, _HIST_ODO_FIELDS)
        try:
            iv = int(float(v or 0))
            if iv > 0:
                odos.append(iv)
        except Exception:
            pass
    if odos and (max(odos) - min(odos)) > 0:
        delta = max(odos) - min(odos)
        # Logos API retorna pos_odometro em metros quando max > 1.000.000
        # (ex: 50.176.923 m = 50.177 km). Converte automaticamente.
        if max(odos) > 1_000_000:
            return round(delta / 1000, 1)
        return round(delta, 1)

    # ── Método 2: Velocidade × tempo ─────────────────────────────────────────
    # Ordena por timestamp, calcula intervalo real entre pontos
    pontos_vt = []
    for p in hist:
        try:
            dt_str = str(_pick(p, _HIST_DT_FIELDS) or "")
            vel    = float(_pick(p, _HIST_VEL_FIELDS) or 0)
            if dt_str and vel >= 0:
                dt = pd.to_datetime(dt_str)
                pontos_vt.append((dt, vel))
        except Exception:
            pass

    if len(pontos_vt) >= 2:
        pontos_vt.sort(key=lambda x: x[0])
        km_vel = 0.0
        for i in range(1, len(pontos_vt)):
            dt_prev, vel_prev = pontos_vt[i-1]
            dt_curr, _        = pontos_vt[i]
            delta_h = (dt_curr - dt_prev).total_seconds() / 3600.0
            # Limita a 15 min entre pontos (ignora gaps longos = veículo parado)
            delta_h = min(delta_h, 0.25)
            km_vel += vel_prev * delta_h
        if km_vel > 1:
            return round(km_vel)

    # ── Método 3: Haversine sobre GPS ────────────────────────────────────────
    def _hav(lat1, lon1, lat2, lon2):
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat/2)**2
             + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2))
             * math.sin(dlon/2)**2)
        return R * 2 * math.asin(math.sqrt(a))

    coords = []
    for p in hist:
        try:
            lt = float(_pick(p, _HIST_LAT_FIELDS) or 0)
            ln = float(_pick(p, _HIST_LON_FIELDS) or 0)
            if lt and ln:
                coords.append((lt, ln))
        except Exception:
            pass

    if len(coords) < 2:
        return 0
    total = sum(_hav(coords[i][0], coords[i][1], coords[i+1][0], coords[i+1][1])
                for i in range(len(coords) - 1))
    return round(total)


def _normalizar_contrato(s: str) -> str:
    """
    Canonicaliza nomes de contrato com variações de separador.
    ECO 050/CERRADO | ECO-050/CERRADO | ECO050/CERRADO → ECO-050/CERRADO
    ECO 135 | ECO-135 | ECO135 → ECO-135
    """
    s = s.strip().upper()
    # ECO[espaço|-|nada]NNN → ECO-NNN
    s = _re.sub(r"ECO[\s\-]?(\d+)", r"ECO-\1", s)
    # remove espaços ao redor da barra
    s = _re.sub(r"\s*/\s*", "/", s)
    return s


def _parse_eco(v, i):
    """Normaliza um veículo ECO para dict de analytics."""
    desc  = v.get("descricaovel", f"V{i}")
    parts = desc.split(" - ", 1)
    contrato  = _normalizar_contrato(parts[0].strip() if len(parts) > 1 else desc)
    motorista = parts[1].strip() if len(parts) > 1 else desc
    dt = str(v.get("pos_dt_posicao", ""))[:10]
    try:
        from datetime import date as _d
        sugest = _d.fromisoformat(dt) if dt else date.today()
    except Exception:
        sugest = date.today()
    return {
        "contrato":       contrato,
        "motorista":      motorista,
        "desc":           desc,
        "placa":          v.get("placavel", "—"),
        "odometro":       int(v.get("pos_odometro") or 0),
        "velocidade":     v.get("pos_velocidade", 0),
        "ignicao":        bool(v.get("pos_ignicao")),
        "uf":             v.get("pos_end_uf", "—"),
        "cidade":         v.get("pos_end_cidade", "—"),
        "localizacao":    v.get("localizacao", "—"),
        "dt_posicao":     str(v.get("pos_dt_posicao", ""))[:16].replace("T", " "),
        "ultima_data":    sugest,
        "tempo_dir_h":    round((v.get("pos_tempo_dirigindo") or 0) / 3600, 1),
        "tempo_par_min":  round((v.get("pos_tempo_parado") or 0) / 60, 1),
        "horimetro":      v.get("pos_horimetro", 0),
        "bateria":        v.get("pos_bateria_externa", 0),
        "lat":            v.get("pos_coordenada_latitude"),
        "lon":            v.get("pos_coordenada_longitude"),
        "idvei":          v.get("pos_idvei"),
        "cor":            _CORES_VEICULOS[i % len(_CORES_VEICULOS)],
    }
