#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
_eco_abast_worker.py — Worker subprocess para scraping do GoodManager
======================================================================
Usa Playwright com perfil Chrome persistente (usuário já logado).
Navega para ConsUltimasTransacoesDet.cfm, extrai tabela e salva JSON.

CLI:
    python _eco_abast_worker.py OUTPUT.json [DATA_INI DATA_FIM]
    DATA_INI / DATA_FIM: DD/MM/YYYY

Saída stdout:
    DONE:N      → sucesso, N registros
    SESSAO_EXPIRADA → precisa logar novamente no Chrome
    ERRO:<msg>  → falha geral (ver stderr)
"""
import sys, os, json, re
from pathlib import Path
from datetime import datetime

# ── Params ────────────────────────────────────────────────────────────────────
args       = sys.argv[1:]
OUTPUT     = Path(args[0]) if args else Path("/tmp/abastecimento.json")
DATA_INI   = args[1] if len(args) > 1 else ""
DATA_FIM   = args[2] if len(args) > 2 else ""

BASE_URL   = "https://www.goodmanager.com.br"
CD_VEICULO = os.environ.get("GM_CD_VEICULO", "25135541")
NR_CARTAO  = os.environ.get(
    "GM_NR_CARTAO",
    "E3ED76A3728933D9E9218801A8EBC78883B908B34BED8A180F0DF5ADC30E5BEC422648986246099B412A50BA828E125A"
)

# Perfil Chrome onde o usuário já está logado
_PROFILE = Path.home() / "OneDrive/Área de Trabalho/Ensaios AEVIAS/.cache_chrome_gm"

# ── Playwright ────────────────────────────────────────────────────────────────
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
except ImportError:
    print("ERRO:playwright não instalado. Execute: pip install playwright && playwright install chromium",
          file=sys.stderr, flush=True)
    sys.exit(1)


def _log(msg: str):
    print(f"[worker] {msg}", file=sys.stderr, flush=True)


def _extrair_tabela(page) -> list[dict]:
    """Extrai todas as linhas de dados da tabela principal."""
    html = page.content()
    # Usa re para encontrar cabeçalhos e linhas
    from html.parser import HTMLParser

    class _TBL(HTMLParser):
        def __init__(self):
            super().__init__()
            self.tabelas = []
            self._cur = []
            self._row = []
            self._cell = ""
            self._in_td = False

        def handle_starttag(self, tag, attrs):
            if tag == "table":
                self._cur = []
            elif tag in ("tr",):
                self._row = []
            elif tag in ("td", "th"):
                self._in_td = True
                self._cell = ""

        def handle_endtag(self, tag):
            if tag in ("td", "th"):
                self._row.append(self._cell.strip())
                self._in_td = False
            elif tag == "tr":
                if self._row:
                    self._cur.append(self._row)
            elif tag == "table":
                if self._cur:
                    self.tabelas.append(self._cur)
                self._cur = []

        def handle_data(self, data):
            if self._in_td:
                self._cell += data

    parser = _TBL()
    parser.feed(html)

    # Encontra a maior tabela
    melhor = []
    for tbl in parser.tabelas:
        if len(tbl) > len(melhor):
            melhor = tbl

    if not melhor or len(melhor) < 2:
        return []

    headers = [h.strip() for h in melhor[0]]
    rows = []
    for row in melhor[1:]:
        if len(row) == len(headers):
            d = dict(zip(headers, row))
            # Ignora linhas totalmente vazias
            if any(v.strip() for v in d.values()):
                rows.append(d)
    return rows


def _filtrar_datas(rows: list[dict], ini: str, fim: str) -> list[dict]:
    if not ini or not fim:
        return rows
    try:
        d_ini = datetime.strptime(ini, "%d/%m/%Y")
        d_fim = datetime.strptime(fim, "%d/%m/%Y")
    except ValueError:
        return rows

    resultado = []
    for r in rows:
        # Procura campo que parece data
        data_val = ""
        for k, v in r.items():
            if re.match(r"\d{2}/\d{2}/\d{4}", str(v)):
                data_val = v[:10]
                break
        if not data_val:
            resultado.append(r)
            continue
        try:
            dt = datetime.strptime(data_val, "%d/%m/%Y")
            if d_ini <= dt <= d_fim:
                resultado.append(r)
        except ValueError:
            resultado.append(r)
    return resultado


def main():
    _PROFILE.mkdir(parents=True, exist_ok=True)
    url_trans = (
        f"{BASE_URL}/GoodManagerSSL/FuelControl/ConsUltimasTransacoesDet.cfm"
        f"?cd_veiculo_cliente={CD_VEICULO}&nr_cartao={NR_CARTAO}"
    )

    with sync_playwright() as p:
        _log("Iniciando browser com perfil persistente...")
        ctx = p.chromium.launch_persistent_context(
            str(_PROFILE),
            channel="chrome",
            headless=True,
            args=["--no-sandbox", "--disable-gpu", "--disable-extensions"],
        )
        page = ctx.new_page()

        _log(f"Navegando para: {url_trans[:80]}...")
        try:
            page.goto(url_trans, wait_until="domcontentloaded", timeout=30_000)
        except PWTimeout:
            _log("Timeout ao navegar")
            ctx.close()
            print("ERRO:Timeout ao acessar GoodManager", file=sys.stderr, flush=True)
            sys.exit(1)

        # Verifica se caiu na tela de login
        cur_url = page.url
        _log(f"URL atual: {cur_url[:80]}")

        if "autenticacao" in cur_url.lower() or "aem-frm-login" in page.content():
            _log("Sessão expirada — precisa logar no Chrome.")
            ctx.close()
            print("SESSAO_EXPIRADA", flush=True)
            sys.exit(0)

        # Aguarda tabela aparecer
        try:
            page.wait_for_selector("table", timeout=15_000)
        except PWTimeout:
            _log("Tabela não encontrada na página")

        _log("Extraindo dados da tabela...")
        rows = _extrair_tabela(page)
        ctx.close()

        if not rows:
            _log("Nenhuma linha extraída")
            print("ERRO:Nenhum dado encontrado — verifique se a sessão está ativa",
                  file=sys.stderr, flush=True)
            sys.exit(1)

        # Filtro de datas
        if DATA_INI and DATA_FIM:
            _log(f"Filtrando {DATA_INI} → {DATA_FIM}...")
            rows = _filtrar_datas(rows, DATA_INI, DATA_FIM)

        # Salva JSON
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)

        _log(f"Salvo: {OUTPUT} ({len(rows)} registros)")
        print(f"DONE:{len(rows)}", flush=True)


if __name__ == "__main__":
    main()
