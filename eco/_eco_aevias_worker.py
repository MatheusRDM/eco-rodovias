"""
_eco_aevias_worker.py — Worker subprocess para scraping on-demand do AEVIAS CONTROLE.
Usa Playwright com perfil Chrome persistente (login já salvo pelo baixar_ensaios.py).

Usage:
    python _eco_aevias_worker.py OUTPUT_PATH [DATA_INI DATA_FIM]

    OUTPUT_PATH — caminho do JSON de saída (geralmente cache_certificados/ensaios_aevias.json)
    DATA_INI    — opcional, formato DD/MM/YYYY
    DATA_FIM    — opcional, formato DD/MM/YYYY

Saída stdout:
    DONE:N       — N registros gravados com sucesso
    SESSAO_EXPIRADA — login não persistido, precisa rodar baixar_ensaios.py manualmente

Saída stderr:
    ERRO:<mensagem>
"""
import sys
import os
import json
from datetime import datetime
from pathlib import Path

# Perfil Chrome compartilhado com o Selenium (baixar_ensaios.py)
_DESKTOP = Path(os.path.expanduser("~")) / "OneDrive" / "Área de Trabalho"
_PROFILE_DIR = _DESKTOP / "Ensaios AEVIAS" / ".cache_chrome"
import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _eco_shared import AEVIAS_BASE_URL as _BASE_URL
_ENSAIOS_URL = f"{_BASE_URL}/MeusEnsaios"

# JavaScript idêntico ao baixar_ensaios.py (linhas 320-372)
_JS_EXTRACT = """
() => {
    const table = document.querySelector('table');
    if (!table) return [];
    const rows = table.querySelectorAll('tr');
    const result = [];

    rows.forEach(row => {
        const cells = row.querySelectorAll('td');
        if (cells.length > 5) {
            const link = row.querySelector('a[href*="Relatorio"]');

            // Profissional: linha 2 da coluna Tipo ou sub-elemento
            let profissional = 'Sem Profissional';
            let linesTipo = cells[0].innerText.trim().split(/[\\r\\n]+/).map(s => s.trim()).filter(s => s.length > 0);
            if (linesTipo.length > 1) {
                profissional = linesTipo[1];
            } else {
                let subEl = cells[0].querySelector('small, span, i');
                if (subEl && subEl.innerText.trim().length > 2) profissional = subEl.innerText.trim();
            }
            if (profissional === 'Sem Profissional' && cells[3]) {
                let linesLab = cells[3].innerText.trim().split(/[\\r\\n]+/).map(s => s.trim()).filter(s => s.length > 0);
                if (linesLab.length > 1) profissional = linesLab[1];
            }

            let rawObra = cells[2] ? cells[2].innerText.trim() : '';
            let linesObra = rawObra.split(/[\\r\\n]+/).map(s => s.trim()).filter(s => s.length > 0);

            const statusEl = cells[7] ? cells[7].querySelector('[class*="badge"],[class*="status"],[class*="chip"],span,button') : null;
            const statusTxt = statusEl ? statusEl.innerText.trim() : (cells[7] ? cells[7].innerText.trim() : '');

            result.push({
                tipo:         linesTipo[0] || '',
                profissional: profissional,
                data:         cells[1] ? cells[1].innerText.trim().split(/[\\r\\n]+/).pop().trim() : '',
                obra:         linesObra[0] || '',
                contrato:     linesObra[1] || '',
                lab:          cells[3] ? cells[3].innerText.split(/[\\r\\n]+/)[0].trim() : '',
                local:        cells[4] ? cells[4].innerText.split(/[\\r\\n]+/)[0].trim() : '',
                empreiteira:  cells[5] ? cells[5].innerText.split(/[\\r\\n]+/)[0].trim() : '',
                projeto:      cells[6] ? cells[6].innerText.trim() : '',
                status:       statusTxt,
                reportUrl:    link ? link.getAttribute('href') : null
            });
        }
    });
    return result;
}
"""

_JS_NEXT_BTN_DISABLED = """
() => {
    const btn = [...document.querySelectorAll('button')].find(b => b.innerText.includes('Próxima'));
    if (!btn) return true;
    return btn.disabled || btn.classList.contains('disabled');
}
"""

_JS_NEXT_BTN_CLICK = """
() => {
    const btn = [...document.querySelectorAll('button')].find(b => b.innerText.includes('Próxima'));
    if (btn && !btn.disabled) { btn.click(); return true; }
    return false;
}
"""


def _filtrar_por_data(dados: list, data_ini: str, data_fim: str) -> list:
    """Filtra registros por intervalo de datas (formato DD/MM/YYYY)."""
    try:
        d_ini = datetime.strptime(data_ini.strip(), "%d/%m/%Y")
        d_fim = datetime.strptime(data_fim.strip(), "%d/%m/%Y")
    except ValueError:
        return dados

    filtrados = []
    for r in dados:
        raw = (r.get("data") or "").strip()
        try:
            # data pode vir como "DD/MM/YYYY HH:MM" ou "DD/MM/YYYY"
            d = datetime.strptime(raw.split()[0], "%d/%m/%Y")
            if d_ini <= d <= d_fim:
                filtrados.append(r)
        except ValueError:
            filtrados.append(r)  # mantém se não conseguir parsear
    return filtrados


def raspar_aevias(output_path: str, data_ini: str = "", data_fim: str = "") -> int:
    """
    Scrapa todos os ensaios do AEVIAS CONTROLE via Playwright.
    Retorna quantidade de registros gravados.
    Lança RuntimeError se sessão expirada ou página não carregou.
    """
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    print("Iniciando Playwright...", flush=True)

    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            user_data_dir=str(_PROFILE_DIR),
            channel="chrome",
            headless=True,
            args=["--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage"],
        )
        page = ctx.new_page()

        print(f"Navegando para {_ENSAIOS_URL} ...", flush=True)
        page.goto(_ENSAIOS_URL, timeout=60_000)

        # Aguarda tabela OU tela de login
        try:
            page.wait_for_selector("table, input[type='email'], input[type='password']",
                                   timeout=20_000)
        except PWTimeout:
            ctx.close()
            raise RuntimeError("SESSAO_EXPIRADA")

        # Verifica se caiu em tela de login
        if page.query_selector("input[type='email']") or page.query_selector("input[type='password']"):
            ctx.close()
            raise RuntimeError("SESSAO_EXPIRADA")

        # Aguarda células com texto (SPA pode demorar a popular)
        try:
            page.wait_for_function(
                """() => {
                    const cells = document.querySelectorAll('table tr td');
                    if (cells.length === 0) return false;
                    let found = 0;
                    for (let i = 0; i < Math.min(cells.length, 10); i++) {
                        if (cells[i].innerText.trim().length > 2) found++;
                    }
                    return found > 0;
                }""",
                timeout=20_000,
            )
        except PWTimeout:
            print("Aviso: células demoraram — tentando extrair assim mesmo.", flush=True)

        all_data = []
        page_num = 1

        while True:
            print(f"  Extraindo página {page_num}...", flush=True)

            # Aguarda células estabilizarem antes de extrair
            page.wait_for_timeout(1_500)

            rows = page.evaluate(_JS_EXTRACT)
            if rows:
                all_data.extend(rows)
                profs = set(r["profissional"] for r in rows if r["profissional"] != "Sem Profissional")
                print(f"    {len(rows)} registros | Profissionais: {', '.join(list(profs)[:3])}", flush=True)

            # Tenta próxima página
            is_last = page.evaluate(_JS_NEXT_BTN_DISABLED)
            if is_last:
                print("  Fim das páginas.", flush=True)
                break

            clicked = page.evaluate(_JS_NEXT_BTN_CLICK)
            if not clicked:
                break
            page_num += 1
            # Aguarda re-renderização da tabela (novo conjunto de linhas)
            page.wait_for_timeout(2_000)

        ctx.close()

    # Aplica filtro de data se fornecido
    if data_ini and data_fim:
        before = len(all_data)
        all_data = _filtrar_por_data(all_data, data_ini, data_fim)
        print(f"  Filtro de data: {before} → {len(all_data)} registros.", flush=True)

    print(f"\nTotal extraído: {len(all_data)} registros", flush=True)

    # Grava JSON
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    return len(all_data)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python _eco_aevias_worker.py OUTPUT_PATH [DATA_INI DATA_FIM]", file=sys.stderr)
        sys.exit(1)

    output_path = sys.argv[1]
    data_ini = sys.argv[2] if len(sys.argv) >= 4 else ""
    data_fim = sys.argv[3] if len(sys.argv) >= 4 else ""

    try:
        n = raspar_aevias(output_path, data_ini, data_fim)
        print(f"DONE:{n}", flush=True)
        sys.exit(0)
    except RuntimeError as e:
        if "SESSAO_EXPIRADA" in str(e):
            print("SESSAO_EXPIRADA", flush=True)
            sys.exit(2)
        print(f"ERRO:{e}", file=sys.stderr, flush=True)
        sys.exit(1)
    except Exception as e:
        print(f"ERRO:{e}", file=sys.stderr, flush=True)
        sys.exit(1)
