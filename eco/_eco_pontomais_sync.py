"""
_eco_pontomais_sync.py — PontoMais via API REST (sem Playwright).

Fluxo:
  1. POST /api/auth/sign_in  → token + uid
  2. POST /api/html_reports/work_days (format=xlsx) → url S3
  3. GET <url S3>  → download do arquivo
"""
import io
import os
from datetime import date

import pandas as pd
import requests

_API_BASE = "https://api.pontomais.com.br"


# ─── Autenticação ─────────────────────────────────────────────────────────────

_BROWSER_HEADERS = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36",
    "Origin":          "https://app2.pontomais.com.br",
    "Referer":         "https://app2.pontomais.com.br/login",
    "Content-Type":    "application/json",
    "Accept":          "application/json, text/plain, */*",
    "Accept-Language": "pt-BR,pt;q=0.9",
}


def _login(login: str, senha: str) -> dict:
    """
    Autentica no PontoMais com retry.
    Retorna dict com 'token', 'client_id', 'uid' prontos para usar nos headers.
    """
    import time
    last_err = None
    for attempt in range(3):
        try:
            r = requests.post(
                f"{_API_BASE}/api/auth/sign_in",
                json={"login": login, "password": senha},
                headers=_BROWSER_HEADERS,
                timeout=(10, 30),   # (connect, read)
            )
            if r.status_code not in (200, 201):
                raise RuntimeError(
                    f"Login falhou (HTTP {r.status_code}). "
                    "Verifique pontomais_login / pontomais_senha em secrets.toml."
                )
            data = r.json()
            return {
                "token":     data["token"],
                "client_id": data["client_id"],
                "uid":       data["data"]["login"],
                "uuid":      data.get("uuid", ""),
            }
        except RuntimeError:
            raise
        except Exception as e:
            last_err = e
            if attempt < 2:
                time.sleep(3)
    raise RuntimeError(f"Falha de conexão com PontoMais após 3 tentativas: {last_err}")


def _headers(auth: dict) -> dict:
    h = {
        **_BROWSER_HEADERS,
        "Referer":      "https://app2.pontomais.com.br/relatorios",
        "api-version":  "2",
        "access-token": auth["token"],
        "client":       auth["client_id"],
        "uid":          auth["uid"],
        "token":        auth["token"],
    }
    if auth.get("uuid"):
        h["uuid"] = auth["uuid"]
    return h


# ─── Geração + download ────────────────────────────────────────────────────────

_ECO_TEAM_ID    = 1491658
_ECO_TEAM_VALUE = "ECO050 Concessionária de Rodovias S.A"


def _gerar_relatorio(auth: dict, start_date: str, end_date: str) -> bytes:
    """
    Solicita o relatório Jornada (espelho ponto) em HTML via API PontoMais.
    Retorna os bytes brutos do HTML gerado no S3.
    start_date / end_date: 'YYYY-MM-DD'
    """
    payload = {
        "report": {
            "report_id":              "work_days",
            "start_date":             start_date,
            "end_date":               end_date,
            "columns":                "overnight_time,date,motive,time_cards,time_balance,summary,extra_time",
            "row_filters":            "",
            "additional_row_filters": "",
            "proposal_status":        "",
            "format":                 "html",
            "fabrication_number":     "",
            "initial_nsr":            "",
            "group_columns":          "",
            "team_id":                _ECO_TEAM_ID,
            "filter_by":              "team_id",
            "filter_value":           _ECO_TEAM_VALUE,
        }
    }
    import time
    last_err = None
    for attempt in range(3):
        try:
            r = requests.post(
                f"{_API_BASE}/api/html_reports/work_days",
                json=payload,
                headers=_headers(auth),
                timeout=(10, 180),
            )
            if r.status_code != 200:
                raise RuntimeError(
                    f"Erro ao gerar relatório (HTTP {r.status_code}): {r.text[:300]}"
                )
            resp = r.json()
            url  = resp.get("url")
            if not url:
                raise RuntimeError(f"API não retornou URL do arquivo: {resp}")

            # Download direto do S3
            dl = requests.get(url, timeout=(10, 120))
            if dl.status_code != 200:
                raise RuntimeError(f"Falha ao baixar arquivo S3 (HTTP {dl.status_code})")
            return dl.content
        except RuntimeError:
            raise
        except Exception as e:
            last_err = e
            if attempt < 2:
                time.sleep(5)
    raise RuntimeError(f"Timeout após 3 tentativas: {last_err}")


# ─── Função pública ────────────────────────────────────────────────────────────

def baixar_espelho_ponto(
    login: str,
    senha: str,
    data_ini: str | None = None,
    data_fim: str | None = None,
    progresso_cb=None,
) -> pd.DataFrame:
    """
    Baixa o espelho ponto via API REST do PontoMais.

    Args:
        login:        CNPJ da empresa (ex: "37895496816")
        senha:        senha do portal PontoMais
        data_ini:     "dd/mm/yyyy" — padrão: 1º dia do mês atual
        data_fim:     "dd/mm/yyyy" — padrão: hoje
        progresso_cb: callable(msg: str) para feedback
    Returns:
        pd.DataFrame com todas as colunas do espelho ponto
    Raises:
        RuntimeError em caso de falha
    """
    def _prog(msg: str):
        if progresso_cb:
            progresso_cb(msg)

    hoje = date.today()
    if not data_ini:
        data_ini = date(hoje.year, hoje.month, 1).strftime("%d/%m/%Y")
    if not data_fim:
        data_fim = hoje.strftime("%d/%m/%Y")

    # Converte dd/mm/yyyy → yyyy-mm-dd
    def _fmt(s: str) -> str:
        d, m, y = s.strip().split("/")
        return f"{y}-{m}-{d}"

    start = _fmt(data_ini)
    end   = _fmt(data_fim)

    _prog("Autenticando no PontoMais…")
    auth = _login(login, senha)

    _prog(f"Gerando relatório Jornada ({data_ini} – {data_fim})… pode levar até 2 minutos")
    xlsx_bytes = _gerar_relatorio(auth, start, end)

    _prog("Processando arquivo Excel…")
    raw = pd.read_excel(io.BytesIO(xlsx_bytes), dtype=str, header=None)
    for i, row in raw.iterrows():
        if row.notna().sum() >= 4:
            df = pd.read_excel(io.BytesIO(xlsx_bytes), dtype=str, header=i)
            df.columns = [str(c).strip() for c in df.columns]
            _prog(f"Concluído — {len(df)} registros.")
            return df

    _prog(f"Concluído — {len(raw)} registros.")
    return pd.read_excel(io.BytesIO(xlsx_bytes), dtype=str)


# ─── Justificativas de HE via API ────────────────────────────────────────────

def _buscar_justificativas(auth: dict, start_date: str, end_date: str) -> dict:
    """
    Busca justificativas de HE via endpoint REST /api/work_days.
    Retorna dict keyed por (employee_name_lower, 'dd/mm/yyyy') → justificativa str.
    start_date / end_date: 'YYYY-MM-DD'
    Falha silenciosamente — retorna {} se endpoint não disponível.
    """
    try:
        hdrs = _headers(auth)
        params = {
            "start_date": start_date,
            "end_date":   end_date,
            "per_page":   1000,
            "page":       1,
        }
        r = requests.get(
            f"{_API_BASE}/api/work_days",
            headers=hdrs,
            params=params,
            timeout=(10, 60),
        )
        if r.status_code != 200:
            return {}
        data = r.json()
        # Estrutura esperada: {"work_days": [{employee: {name}, date, justification, ...}]}
        wdays = data.get("work_days") or data.get("data") or []
        result = {}
        for wd in wdays:
            just = (wd.get("justification") or wd.get("approval_note") or "").strip()
            if not just:
                continue
            emp = wd.get("employee") or {}
            nome = (emp.get("name") or emp.get("full_name") or "").strip().lower()
            raw_date = wd.get("date") or wd.get("work_date") or ""
            # normaliza para dd/mm/yyyy
            try:
                import re as _re
                m = _re.search(r"(\d{4})-(\d{2})-(\d{2})", raw_date)
                if m:
                    data_fmt = f"{m.group(3)}/{m.group(2)}/{m.group(1)}"
                    result[(nome, data_fmt)] = just
            except Exception:
                pass
        return result
    except Exception:
        return {}
