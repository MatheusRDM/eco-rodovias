# -*- coding: utf-8 -*-
"""
baixar_ensaios_api.py
=====================
Substituto do Selenium para baixar PDFs do AEVIAS CONTROLE.

Diferença em relação ao baixar_ensaios.py antigo:
  - LISTA via API Base44 (sem Chrome, instantâneo)
  - BAIXA PDFs via Chrome CDP só para os registros desejados
  - 3-5x mais rápido (sem scraping de tabela)

Uso:
  python baixar_ensaios_api.py
  python baixar_ensaios_api.py --ini 01/04/2026 --fim 30/04/2026
  python baixar_ensaios_api.py --apenas-eco        (filtra só ECO Rodovias)
"""
import os, sys, re, json, base64, socket, time, argparse, threading
from pathlib import Path
from datetime import datetime, timedelta

import requests
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Alignment, Font, Border, Side
from openpyxl.utils import get_column_letter

# ── Encoding Windows ──────────────────────────────────────────────────────────
if sys.stdout:
    try: sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception: pass

# ── Selenium ──────────────────────────────────────────────────────────────────
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================
BASE_URL  = "https://aevias-controle.base44.app"
_APP_ID   = "68a7599ee3fb9205cfb852ec"
_API_BASE = f"{BASE_URL}/api/apps/{_APP_ID}/entities"

# Token JWT — atualize quando expirar (~16/07/2026)
TOKEN = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9"
    ".eyJzdWIiOiJtYXRoZXVzLnJlc2VuZGVAYWZpcm1hZXZpYXMuY29tLmJyIiwiZXhwIjoxNzg0MjAxNzQzLCJpYXQiOjE3NzY0MjU3NDN9"
    ".nkIJL99iRM3asFuS3hv1XQMqK0aCUWr7CupxElwM15o"
)

BASE_DIR = Path(__file__).parent
OUTPUT_DIR  = BASE_DIR / "0.1-Resultados"
BACKEND_DIR = BASE_DIR / "0.2-BACKEND" / "Configuracoes_Internas"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
BACKEND_DIR.mkdir(parents=True, exist_ok=True)

# obra_ids do contrato ECO Rodovias 6771
_ECO_OBRA_IDS = {
    "699da9fb4170261d53e9320a", "699da97a36d65eee07b96921",
    "699b641719e8e991e14a52f4", "699b632616a416fa863ecfe5",
    "699b62303974495c9f0578f6", "699b60512757145586da2f94",
    "6970fdd37a246fdd60b2a559", "6970fd863a898f0289208528",
    "6970fd71a784398388307d40", "6970fd14fa691bebb07f1d26",
    "6970fcdcfe7f2ea500779545", "6970fc889fd059eb9dcc2221",
    "696106dfbb2b8b6a8f49282d", "696106991705079464a565c1",
}
_ECO_RODOVIAS = {"BR-050", "BR-365", "BR-364"}

# =============================================================================
# ENTIDADES
# =============================================================================
ENTIDADES = {
    "DiarioObra":                  ("Diário de Obra",         "/diario-de-obra",             "Pavimento"),
    "EnsaioCAUQ":                  ("Ensaio de CAUQ",         "/ensaio-cauq",                "Pavimento"),
    "ChecklistUsina":              ("Checklist de Usina",     "/checklist",                  "Pavimento"),
    "ChecklistAplicacao":          ("Checklist de Aplicação", "/checklist-aplicacao",        "Pavimento"),
    "ChecklistMRAF":               ("Checklist de MRAF",      "/checklist-mraf",             "Pavimento"),
    "ChecklistTerraplanagem":      ("Checklist Terraplanagem","/checklist-terraplanagem",    "OAE / Terraplenos"),
    "ChecklistConcretagem":        ("Checklist Concretagem",  "/checklist-concretagem",      "OAE / Terraplenos"),
    "ChecklistReciclagem":         ("Checklist Reciclagem",   "/checklist-reciclagem",       "Pavimento"),
    "AcompanhamentoUsinagem":      ("Acomp. Usinagem",        "/acompanhamento-usinagem",    "Pavimento"),
    "AcompanhamentoCarga":         ("Acomp. Carga",           "/acompanhamento-carga",       "Pavimento"),
    "EnsaioDensidadeInSitu":       ("Ensaio Densidade",       "/ensaio-densidade",           "Pavimento"),
    "EnsaioGranulometriaIndividual":("Ensaio Granulometria",  "/ensaio-granulometria",       "Pavimento"),
    "EnsaioManchaPendulo":         ("Ensaio Mancha/Pêndulo",  "/ensaio-mancha-pendulo",      "Pavimento"),
    "EnsaioVigaBenkelman":         ("Ensaio Viga Benkelman",  "/ensaio-viga-benkelman",      "Pavimento"),
    "EnsaioProctor":               ("Ensaio Proctor",         "/EnsaioProctor",              "OAE / Terraplenos"),
    "EnsaioTaxaMRAF":              ("Ensaio Taxa MRAF",       "/ensaio-taxa-mraf",           "Pavimento"),
    "EnsaioTaxaPinturaImprimacao": ("Ensaio Taxa Pintura",    "/ensaio-taxa-pintura",        "Pavimento"),
    "EnsaioSondagem":              ("Ensaio Sondagem",        "/ensaio-sondagem",            "OAE / Terraplenos"),
}

# =============================================================================
# HELPERS
# =============================================================================

def _headers():
    return {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}


def sanitize(name: str) -> str:
    name = name.replace("/", "-").replace("\\", "-")
    return re.sub(r'[<>:"|?*]', '', name).strip(". ")


def _get_lab(rec: dict) -> str:
    nome = rec.get("laboratorista_name", "")
    if nome: return nome
    cb = rec.get("created_by")
    if isinstance(cb, dict): return cb.get("full_name", "—")
    return str(cb or "—")


def _data(rec: dict) -> str:
    raw = rec.get("data") or rec.get("data_ensaio") or rec.get("created_date", "")
    try:
        return datetime.fromisoformat(str(raw)[:10]).strftime("%d/%m/%Y")
    except Exception:
        return str(raw)[:10]


def _status(rec: dict) -> str:
    if rec.get("was_rejected"): return "Reprovado"
    if rec.get("approved"):     return "Aprovado"
    return "Pendente"


def _is_eco(rec: dict, apenas_eco: bool) -> bool:
    if not apenas_eco:
        return True
    rod = str(rec.get("rodovia") or "").strip()
    if rod:
        return any(e in rod for e in _ECO_RODOVIAS)
    oid = rec.get("obra_id") or rec.get("project_id") or ""
    return oid in _ECO_OBRA_IDS if oid else True

# =============================================================================
# MAPA DE OBRAS (API)
# =============================================================================

def _carregar_mapa_obras() -> dict:
    """Retorna {obra_id: grupo_nome}"""
    print("  Carregando mapa de obras...")
    try:
        r = requests.get(f"{_API_BASE}/Obra", headers=_headers(), timeout=30)
        obras = r.json() if r.status_code == 200 else []
    except Exception:
        return {}

    def _grupo(nome):
        n = (nome or "").upper()
        if "SST" in n or "SEGURANÇA" in n: return "SST"
        if "TOPO" in n: return "TOPOGRAFIA"
        if "ESCRIT" in n: return "ESCRITÓRIO"
        if "OAE" in n or "TERRAPLAN" in n: return "OAE - Terraplenos"
        if "CONSERVA" in n: return "Conserva"
        if "AMPLIA" in n: return "Ampliações"
        return "Pavimento"

    return {o["id"]: _grupo(o.get("name", "")) for o in obras if o.get("id")}

# =============================================================================
# LISTAGEM VIA API
# =============================================================================

def listar_todos(data_ini: datetime, data_fim: datetime, apenas_eco: bool) -> list[dict]:
    mapa_obras = _carregar_mapa_obras()
    resultado  = []

    print(f"\n  Listando ensaios via API ({data_ini.strftime('%d/%m/%Y')} → {data_fim.strftime('%d/%m/%Y')})...")

    for entidade, (tipo_nome, path, obra_default) in ENTIDADES.items():
        try:
            r = requests.get(f"{_API_BASE}/{entidade}", headers=_headers(), timeout=30)
            if r.status_code != 200:
                print(f"    [WARN] {entidade}: HTTP {r.status_code}")
                continue
            recs = r.json()
            if not isinstance(recs, list):
                continue
        except Exception as e:
            print(f"    [ERR] {entidade}: {e}")
            continue

        count = 0
        for rec in recs:
            if not _is_eco(rec, apenas_eco):
                continue

            # Filtro de data
            data_str = _data(rec)
            try:
                dt = datetime.strptime(data_str, "%d/%m/%Y")
                if not (data_ini <= dt <= data_fim):
                    continue
            except Exception:
                continue

            lab = _get_lab(rec)
            rec_id = rec.get("id", "")

            # Grupo real pelo obra_id
            oid = rec.get("obra_id") or rec.get("project_id") or ""
            obra = mapa_obras.get(oid, obra_default)

            resultado.append({
                "tipo":        tipo_nome,
                "lab":         lab,
                "profissional": lab,
                "data":        data_str,
                "obra":        obra,
                "status":      _status(rec),
                "reportUrl":   f"{path}/{rec_id}" if rec_id else path,
                "id":          rec_id,
            })
            count += 1

        if count:
            print(f"    ✓ {entidade}: {count} registros")

    print(f"\n  Total via API: {len(resultado)} registros")
    return resultado

# =============================================================================
# CHROME / CDP
# =============================================================================

def setup_driver():
    options = Options()
    machine_id = re.sub(r'[^a-zA-Z0-9_-]', '_', socket.gethostname())
    profile_dir = BACKEND_DIR / ".chrome_cache" / machine_id
    profile_dir.mkdir(parents=True, exist_ok=True)
    options.add_argument(f"--user-data-dir={profile_dir}")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--start-maximized")
    prefs = {
        "printing.print_preview_sticky_settings.appState": json.dumps({
            "recentDestinations": [{"id": "Save as PDF", "origin": "local", "account": ""}],
            "selectedDestinationId": "Save as PDF",
            "version": 2
        }),
        "download.default_directory": str(OUTPUT_DIR),
        "download.prompt_for_download": False,
    }
    options.add_experimental_option("prefs", prefs)
    options.add_argument("--kiosk-printing")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)


def gerar_pdf(driver, url: str, output_path: Path, timeout: int = 45) -> bool:
    result_holder: dict = {"data": None, "error": None}

    def do_pdf():
        try:
            driver.set_page_load_timeout(timeout)
            driver.get(url)
            time.sleep(3)
            # Aguarda conteúdo relevante
            try:
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                from selenium.webdriver.common.by import By
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.XPATH,
                        "//*[contains(text(),'GERAIS') or contains(text(),'Relat') or "
                        "contains(text(),'Checklist') or contains(text(),'Ensaio')]"
                    ))
                )
            except Exception:
                pass
            # Aguarda "Otimizando imagens"
            try:
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                from selenium.webdriver.common.by import By
                ot = "//*[contains(text(),'Otimizando imagens')]"
                WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.XPATH, ot)))
                WebDriverWait(driver, 60).until_not(EC.presence_of_element_located((By.XPATH, ot)))
            except Exception:
                pass
            time.sleep(2)
            result = driver.execute_cdp_cmd("Page.printToPDF", {
                "printBackground": True, "preferCSSPageSize": True,
                "marginTop": 0.4, "marginBottom": 0.4,
                "marginLeft": 0.4, "marginRight": 0.4,
                "paperWidth": 8.27, "paperHeight": 11.69,
            })
            result_holder["data"] = result["data"]
        except Exception as e:
            result_holder["error"] = str(e)

    t = threading.Thread(target=do_pdf)
    t.start()
    t.join(timeout + 5)

    if t.is_alive():
        try: driver.execute_script("window.stop();")
        except Exception: pass
        return False

    if result_holder.get("error") or not result_holder.get("data"):
        return False

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(base64.b64decode(result_holder["data"]))
    return True


def aguardar_login(driver):
    """Abre o site e aguarda o usuário fazer login se necessário."""
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.common.by import By

    driver.get(f"{BASE_URL}/MeusEnsaios")
    time.sleep(4)
    try:
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Ensaios Realizados')]"))
        )
        print("  Já logado!")
        return True
    except Exception:
        pass

    print("\n" + "="*50)
    print("  FAÇA LOGIN NO CHROME QUE ABRIU")
    print("  O script continuará automaticamente...")
    print("="*50)

    for _ in range(60):
        time.sleep(5)
        try:
            WebDriverWait(driver, 3).until(
                EC.presence_of_element_located((By.XPATH, "//*[contains(text(),'Ensaios Realizados')]"))
            )
            print("  Login confirmado!")
            return True
        except Exception:
            pass
    return False

# =============================================================================
# EXCEL DE PRESENÇA
# =============================================================================

def gerar_excel(ensaios: list[dict], data_ini: datetime, data_fim: datetime, path: Path):
    print(f"\n  Gerando Excel: {path.name}...")
    df = pd.DataFrame(ensaios)
    if df.empty: return

    df['dt'] = df['data'].apply(lambda x: datetime.strptime(x.split()[0], "%d/%m/%Y"))

    def cat(tipo):
        t = tipo.upper()
        if "CHECKLIST" in t: return "Checklist"
        if "DIÁRIO" in t or "DIARIO" in t: return "Diário de Obra"
        return "Ensaio"
    df['categoria'] = df['tipo'].apply(cat)

    dias = []
    curr = data_ini
    while curr <= data_fim:
        dias.append(curr)
        curr += timedelta(days=1)

    fill_g  = PatternFill("solid", fgColor="C6EFCE")
    fill_gr = PatternFill("solid", fgColor="F2F2F2")
    fill_hdr= PatternFill("solid", fgColor="1A3A5C")
    fill_sub= PatternFill("solid", fgColor="2E6DA4")
    fill_col= PatternFill("solid", fgColor="4472C4")
    fill_cl = PatternFill("solid", fgColor="EBF3FB")
    f_ok    = Font(color="006100", bold=True)
    f_mut   = Font(color="808080")
    f_wht   = Font(color="FFFFFF", bold=True)
    f_wht10 = Font(color="FFFFFF", size=10)
    alc     = Alignment(horizontal="center", vertical="center")
    brd     = Border(*[Side(style='thin')]*4)

    wb = Workbook()
    del wb['Sheet']
    n_dias = len(dias)
    n_cols = 2 + n_dias
    cats   = ["Checklist", "Diário de Obra", "Ensaio"]
    collabs= sorted(df['lab'].unique())

    # Aba Resumão
    ws = wb.create_sheet("Resumão", 0)
    ws.merge_cells(1, 1, 1, n_cols)
    c = ws.cell(1, 1, "RESUMÃO — ENSAIOS AEVIAS")
    c.font = Font(bold=True, size=14, color="FFFFFF"); c.fill = fill_hdr; c.alignment = alc
    ws.row_dimensions[1].height = 30
    ws.merge_cells(2, 1, 2, n_cols)
    c = ws.cell(2, 1, f"Período: {data_ini.strftime('%d/%m/%Y')} → {data_fim.strftime('%d/%m/%Y')}  |  Total: {len(df)}")
    c.font = f_wht10; c.fill = fill_sub; c.alignment = alc
    r = 4
    for ci, h in enumerate(["COLABORADOR", "CATEGORIA"], 1):
        c = ws.cell(r, ci, h); c.font = f_wht; c.fill = fill_col; c.alignment = alc; c.border = brd
    for i, d in enumerate(dias, 3):
        c = ws.cell(r, i, d.strftime("%d/%m")); c.font = f_wht; c.fill = fill_col; c.alignment = alc; c.border = brd
        ws.column_dimensions[get_column_letter(i)].width = 6
    ws.row_dimensions[r].height = 18; r += 1

    for collab in collabs:
        df_c = df[df['lab'] == collab]; first = r
        for ci, cat in enumerate(cats):
            c = ws.cell(r, 2, cat)
            c.font = Font(bold=(ci == 0)); c.alignment = Alignment(horizontal="left", vertical="center"); c.border = brd
            if ci == 0: c.fill = fill_cl
            for col_i, d in enumerate(dias, 3):
                dom = (d.weekday() == 6)
                teve = not df_c[(df_c['dt'] == d) & (df_c['categoria'] == cat)].empty
                cel = ws.cell(r, col_i); cel.alignment = alc; cel.border = brd
                if teve:
                    cel.value = "OK"; cel.fill = fill_g; cel.font = f_ok
                else:
                    cel.value = "-"; cel.font = f_mut
                    if dom: cel.fill = fill_gr
                    elif ci == 0: cel.fill = fill_cl
            ws.row_dimensions[r].height = 15; r += 1
        ws.merge_cells(first, 1, r-1, 1)
        c = ws.cell(first, 1, collab)
        c.font = Font(bold=True, size=10); c.fill = fill_cl
        c.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True); c.border = brd
    ws.column_dimensions['A'].width = 24; ws.column_dimensions['B'].width = 18

    # Abas individuais
    for collab in collabs:
        sn = re.sub(r'[\\*?:/\[\]]', '', collab)[:31]
        ws2 = wb.create_sheet(sn)
        df_c = df[df['lab'] == collab]
        ws2.cell(1, 1, "CATEGORIA").font = f_wht; ws2.cell(1, 1).fill = fill_col; ws2.cell(1, 1).alignment = alc
        for i, d in enumerate(dias, 2):
            c = ws2.cell(1, i, d.strftime("%d/%m")); c.font = f_wht; c.fill = fill_col; c.alignment = alc
            ws2.column_dimensions[get_column_letter(i)].width = 6
        ws2.column_dimensions['A'].width = 20
        for ri, cat in enumerate(cats, 2):
            ws2.cell(ri, 1, cat).font = Font(bold=True); ws2.cell(ri, 1).border = brd
            for ci, d in enumerate(dias, 2):
                dom = (d.weekday() == 6)
                teve = not df_c[(df_c['dt'] == d) & (df_c['categoria'] == cat)].empty
                cel = ws2.cell(ri, ci); cel.border = brd; cel.alignment = alc
                if teve:
                    cel.value = "OK"; cel.fill = fill_g; cel.font = f_ok
                else:
                    cel.value = "-"; cel.font = f_mut
                    if dom: cel.fill = fill_gr

    wb.save(path)
    print(f"  Excel salvo: {path}")

# =============================================================================
# MAIN
# =============================================================================

def parse_args():
    p = argparse.ArgumentParser(description="Baixar ensaios AEVIAS via API + CDP")
    p.add_argument("--ini", default="", help="Data inicial DD/MM/YYYY (padrão: 1º do mês)")
    p.add_argument("--fim", default="", help="Data final DD/MM/YYYY (padrão: hoje)")
    p.add_argument("--apenas-eco", action="store_true", help="Filtrar apenas ECO Rodovias 6771")
    p.add_argument("--sem-pdf",    action="store_true", help="Apenas lista + Excel, sem baixar PDFs")
    return p.parse_args()


def obter_periodo(ini_str: str, fim_str: str):
    hoje = datetime.now()
    try:
        ini = datetime.strptime(ini_str, "%d/%m/%Y") if ini_str else hoje.replace(day=1)
        fim = datetime.strptime(fim_str, "%d/%m/%Y") if fim_str else hoje
    except ValueError:
        print("Formato de data inválido. Use DD/MM/AAAA.")
        sys.exit(1)
    return ini, fim


def main():
    args = parse_args()
    data_ini, data_fim = obter_periodo(args.ini, args.fim)
    apenas_eco = args.apenas_eco
    sem_pdf    = args.sem_pdf

    timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M")
    pasta_raiz = OUTPUT_DIR / f"Ensaios_API_{timestamp}"
    pasta_raiz.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("  AEVIAS — Download via API (sem scraping)")
    print(f"  Período : {data_ini.strftime('%d/%m/%Y')} → {data_fim.strftime('%d/%m/%Y')}")
    print(f"  Filtro  : {'Apenas ECO Rodovias 6771' if apenas_eco else 'Todas as obras'}")
    print(f"  PDFs    : {'NÃO (só lista + Excel)' if sem_pdf else 'SIM'}")
    print("=" * 60)

    # 1. Listar via API
    ensaios = listar_todos(data_ini, data_fim, apenas_eco)
    if not ensaios:
        print("\nNenhum ensaio encontrado no período.")
        return

    # 2. Salvar JSON
    json_path = pasta_raiz / "ensaios_dados.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(ensaios, f, ensure_ascii=False, indent=2)
    print(f"\n  JSON salvo: {json_path}")

    # 3. Gerar Excel
    excel_path = pasta_raiz / f"Relatorio_Atividades_{timestamp}.xlsx"
    try:
        gerar_excel(ensaios, data_ini, data_fim, excel_path)
    except Exception as e:
        print(f"  ERRO Excel: {e}")

    if sem_pdf:
        print(f"\nConcluído! (sem PDFs)\nArquivos em: {pasta_raiz}")
        return

    # 4. Baixar PDFs via Chrome
    print("\n" + "=" * 40)
    print("  BAIXANDO PDFs via Chrome CDP")
    print("=" * 40)

    driver = None
    try:
        driver = setup_driver()
        if not aguardar_login(driver):
            print("ERRO: Login não detectado.")
            return

        total = len(ensaios); ok = 0; erros = []

        for i, ens in enumerate(ensaios, 1):
            obra   = sanitize(ens.get("obra", "Sem Obra"))
            lab    = sanitize(ens.get("lab", "Sem Colaborador"))
            tipo   = ens.get("tipo", "Sem Tipo")
            data   = ens.get("data", "Sem Data").replace("/", "-")
            url_rel = ens.get("reportUrl", "")

            if not url_rel or url_rel == "#":
                erros.append(f"Sem URL: {tipo} | {lab}")
                continue

            full_url = f"{BASE_URL}{url_rel}"
            filename = sanitize(f"{tipo} - {data} - {lab}.pdf")
            dest = pasta_raiz / obra / lab / filename
            dest.parent.mkdir(parents=True, exist_ok=True)

            # Evita duplicata
            counter = 2
            while dest.exists():
                dest = dest.parent / f"{filename.rsplit('.pdf',1)[0]} ({counter}).pdf"
                counter += 1

            print(f"  [{i}/{total}] {obra} > {lab} > {filename[:50]}")
            try:
                if gerar_pdf(driver, full_url, dest):
                    ok += 1
                else:
                    erros.append(f"Falha: {filename}")
            except Exception as e:
                erros.append(f"{filename}: {e}")

        print(f"\n  ✓ PDFs baixados : {ok}")
        print(f"  ✗ Erros         : {len(erros)}")
        if erros:
            for err in erros: print(f"    - {err}")

    finally:
        if driver:
            time.sleep(3)
            driver.quit()

    print(f"\nConcluído! Arquivos em: {pasta_raiz}")


if __name__ == "__main__":
    main()
