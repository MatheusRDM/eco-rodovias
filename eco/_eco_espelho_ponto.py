"""
_eco_espelho_ponto.py — Espelho de Ponto (Jornada) via VR PontoMais.
Parser de blocos por colaborador com análise de horários e HE.
Segmentado por Grupo (SST / Pavimento / Topografia / Escritório).
"""
import io
import json
import os
import re
import sys
from datetime import date

import pandas as pd
import streamlit as st

_PAGES_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR  = os.path.dirname(_PAGES_DIR)
if _PAGES_DIR not in sys.path: sys.path.insert(0, _PAGES_DIR)
if _ROOT_DIR  not in sys.path: sys.path.insert(0, _ROOT_DIR)

from _eco_shared import _CACHE_DIR
from _eco_bg_loader import start_bg_task, is_loading, render_atualizar_btn

# ─── Caminhos de cache ────────────────────────────────────────────────────────
_CACHE_XLSX = os.path.join(_CACHE_DIR, "ponto_eco_cache.xlsx")
_CACHE_META = os.path.join(_CACHE_DIR, "ponto_eco_cache.json")

_DAY_ABBR = {0:"SEG",1:"TER",2:"QUA",3:"QUI",4:"SEX",5:"SÁB",6:"DOM"}
_GRUPOS   = ["Todos","SST","Pavimento","Topografia","Escritório"]
_COR_GRUPO = {
    "SST":        "#FFB347",
    "Pavimento":  "#4CC9F0",
    "Topografia": "#7BBF6A",
    "Escritório": "#A29BFE",
    "Outros":     "#8FA882",
}

# ─── CSS ─────────────────────────────────────────────────────────────────────
_CSS = """
<style>
.ep-header h2{font-size:1.1rem;font-weight:700;color:#E8EFD8;margin:0}
.ep-header p{font-size:.7rem;color:#6b7f8d;margin:2px 0 0}
.ep-ts{font-size:.62rem;color:#566E3D;margin-top:6px}
.ep-upload-hint{background:rgba(76,201,240,.06);border:1px dashed rgba(76,201,240,.25);
  border-radius:12px;padding:14px 18px;font-size:.75rem;color:#8ECAE6;
  margin-bottom:14px;line-height:1.6}
.ep-upload-hint strong{color:#4CC9F0}
.ep-kpi-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(130px,1fr));
  gap:8px;margin-bottom:14px}
.ep-kpi{background:rgba(18,25,38,.85);border:1px solid rgba(255,255,255,.07);
  border-radius:12px;padding:12px 14px;text-align:center}
.ep-kpi .kv{font-size:1.3rem;font-weight:700;line-height:1.2}
.ep-kpi .kl{font-size:.56rem;color:#6b7f8d;letter-spacing:.04em;margin-top:3px}
.ep-hr{height:1px;background:rgba(255,255,255,.06);margin:12px 0}
.ep-badge{display:inline-block;padding:2px 8px;border-radius:6px;
  font-size:.6rem;font-weight:700;margin-right:4px}

/* tabelas de análise */
.ep-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch;width:100%;margin-bottom:20px}
.ep-tbl{border-collapse:collapse;font-size:.63rem;font-family:Inter,sans-serif;
  width:100%;table-layout:auto}
.ep-tbl th{background:rgba(86,110,61,.2);color:#BFCF99;padding:5px 3px;
  text-align:center;font-weight:600;border:1px solid rgba(86,110,61,.15);
  font-size:.58rem;white-space:nowrap}
.ep-tbl td{padding:4px 3px;border:1px solid rgba(255,255,255,.05);
  text-align:center;white-space:nowrap;font-size:.62rem;vertical-align:middle;
  min-width:32px;transition:filter .15s;cursor:default}
.ep-tbl td:not(.ep-nome):not(.ep-total):hover{filter:brightness(1.4)}
.ep-nome{text-align:left!important;padding-left:8px!important;min-width:110px;
  max-width:170px;vertical-align:middle!important;
  border-right:2px solid rgba(86,110,61,.25)!important}
.ep-nome strong{font-size:.68rem;color:#E8EFD8;display:block;line-height:1.3;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:160px}
.ep-nome small{font-size:.52rem;color:#8FA882;display:block;margin-top:1px}
.ep-total{color:#BFCF99;font-weight:700;border-left:2px solid rgba(86,110,61,.2)!important;
  background:rgba(86,110,61,.08)!important}
.ep-sep td{border-top:2px solid rgba(86,110,61,.2)!important}
.ep-he-pos{background:rgba(247,183,49,.2);color:#F7B731;font-weight:700}
.ep-he-zero{color:#3a4a5e}
.ep-early{background:rgba(76,201,240,.15);color:#4CC9F0;font-weight:600}
.ep-late {background:rgba(230,25,75,.15);color:#FF6B6B;font-weight:600}
.ep-norm {color:#BFCF99}
.ep-ne   {background:rgba(60,180,75,.04);color:#2e5040}

/* tooltip — conteúdo oculto; posicionamento via JS abaixo */
.ep-tip{position:relative;display:inline;cursor:default}
.ep-tip-box{display:none}   /* never show via CSS — JS clones to fixed floater */
.ep-tip-lbl{font-size:.58rem;color:#8FA882;margin-bottom:2px}

/* Floating tooltip global — posicionado por JS */
#ep-float-tip{
  position:fixed;z-index:999999;display:none;pointer-events:none;
  background:#111d2e;border:1px solid rgba(123,191,106,.3);border-radius:8px;
  padding:8px 10px;min-width:140px;max-width:240px;
  box-shadow:0 8px 28px rgba(0,0,0,.7);text-align:left;
  white-space:normal;font-size:.63rem;color:#D8E5C8;line-height:1.45;
}
</style>
<div id="ep-float-tip"></div>
<script>
(function(){
  var ft = document.getElementById('ep-float-tip');
  if(!ft) return;
  function bindAll(){
    document.querySelectorAll('.ep-tip').forEach(function(el){
      if(el._epBound) return;
      el._epBound = true;
      var box = el.querySelector('.ep-tip-box');
      if(!box) return;
      el.addEventListener('mouseenter', function(e){
        ft.innerHTML = box.innerHTML;
        ft.style.display = 'block';
        var r = el.getBoundingClientRect();
        var tw = ft.offsetWidth, th = ft.offsetHeight;
        var cx = r.left + r.width/2;
        var tx = Math.max(6, Math.min(cx - tw/2, window.innerWidth - tw - 6));
        var ty = r.top - th - 8;
        if(ty < 6) ty = r.bottom + 8;
        ft.style.left = tx + 'px';
        ft.style.top  = ty + 'px';
      });
      el.addEventListener('mouseleave', function(){
        ft.style.display = 'none';
      });
    });
  }
  bindAll();
  var obs = new MutationObserver(bindAll);
  obs.observe(document.body, {childList:true, subtree:true});
})();
</script>
"""

# ─── Parser HTML (resposta API PontoMais) ────────────────────────────────────

def _parse_html_report(raw_bytes: bytes) -> pd.DataFrame:
    """
    Lê o HTML do relatório Jornada (espelho ponto) gerado pela API PontoMais.
    Estrutura: div.report-group-name → "Colaborador: Nome" seguido de <table>.
    Retorna DataFrame no mesmo formato de _parse_blocos.
    """
    import re as _re
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(raw_bytes, "html.parser")
    except ImportError:
        # Fallback: usa html.parser nativo via pandas
        import io as _io
        try:
            tables = pd.read_html(_io.BytesIO(raw_bytes))
        except Exception:
            return pd.DataFrame()
        return pd.DataFrame()  # sem nome não conseguimos associar

    # Mapa: posição da coluna → campo normalizado
    _COL_MAP = {
        "data":              "data",
        "1ª entrada":        "entrada",
        "1ª saída":          "saida_almoco",
        "2ª entrada":        "volta_almoco",
        "2ª saída":          "saida",
        "h. intervalo":      "intervalo",
        "horas normais":     "ht",
        "h.e. 1":            "he_50",
        "h.e. 2":            "he_100",
        "motivo":            "motivo",
        "motivo/observação": "motivo",
    }

    def _clean_time(v: str) -> str:
        """Remove sufixos como 'p' (pré-assinalado) e normaliza HH:MM."""
        v = v.strip().rstrip("p").rstrip("P").strip()
        if _re.match(r"^\d{1,2}:\d{2}$", v) and v != "00:00":
            return v
        return ""

    rows = []
    # Cada bloco de colaborador: div.report-group-name seguido por table
    for name_div in soup.find_all("div", class_="report-group-name"):
        raw_name = name_div.get_text(" ", strip=True)
        nome = _re.sub(r"(?i)colaborador\s*:\s*", "", raw_name).strip()
        if not nome:
            continue

        # Primeira tabela após o div de nome
        table = name_div.find_next("table")
        if not table:
            continue

        # Detecta índices de colunas a partir dos <th>
        col_idx = {}
        for th in table.find_all("th"):
            label = th.get_text(" ", strip=True).lower()
            for key, field in _COL_MAP.items():
                if key in label and field not in col_idx.values():
                    col_idx[th.parent.find_all("th").index(th) if th.parent else -1] = field
                    break

        # Linhas de dados
        for tr in table.find_all("tr"):
            tds = tr.find_all("td")
            if len(tds) < 6:
                continue
            cells = [td.get_text(" ", strip=True) for td in tds]

            # Data: "Seg, 20/04/2026" → extrai "20/04/2026"
            raw_data = cells[0] if cells else ""
            m = _re.search(r"(\d{2}/\d{2}/\d{4})", raw_data)
            if not m:
                continue
            data_str = m.group(1)

            rec = {"nome": nome, "data": data_str}
            for idx, field in col_idx.items():
                if field == "data" or idx < 0 or idx >= len(cells):
                    continue
                v = cells[idx]
                if field in ("entrada", "saida_almoco", "volta_almoco", "saida", "intervalo", "ht", "he_50", "he_100"):
                    rec[field] = _clean_time(v)
                else:
                    rec[field] = v
            rows.append(rec)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    # Garante colunas mínimas
    for col in ("entrada", "saida_almoco", "volta_almoco", "saida", "intervalo", "ht", "he_50", "he_100", "motivo", "justificativa_he"):
        if col not in df.columns:
            df[col] = ""
    return df


# ─── Parser de blocos (XLSX upload manual) ───────────────────────────────────

def _col_match(name: str, keywords: list) -> bool:
    n = name.lower()
    return any(k in n for k in keywords)


def _parse_blocos(file_or_path) -> pd.DataFrame:
    """
    Lê o Excel PontoMais (estrutura de blocos por colaborador) e
    retorna DataFrame flat: nome, data, entrada, saida_almoco,
    volta_almoco, saida, intervalo, ht, he_50, he_100, motivo.
    """
    if isinstance(file_or_path, str):
        with open(file_or_path, "rb") as f:
            raw_bytes = f.read()
    elif hasattr(file_or_path, "getvalue"):
        raw_bytes = file_or_path.getvalue()
    else:
        raw_bytes = file_or_path

    raw = pd.read_excel(io.BytesIO(raw_bytes), dtype=str, header=None)

    rows     = []
    col_map  = {}   # col_index → field_name

    _COL_RULES = [
        ("data",          ["data"]),
        ("entrada",       ["1", "entrada"]),        # 1ª Entrada
        ("saida_almoco",  ["1", "sa"]),              # 1ª Saída
        ("volta_almoco",  ["2", "entrada"]),         # 2ª Entrada
        ("saida",         ["2", "sa"]),              # 2ª Saída
        ("intervalo",     ["intervalo"]),
        ("ht",            ["normal"]),               # Horas normais
        ("he_50",         ["extra", "fator 1"]),     # fator 1 (50% ou 70%)
        ("he_100",        ["extra", "fator 2"]),     # fator 2 (100%)
        ("motivo",        ["motivo", "observa"]),
        ("justificativa_he", ["justif", "aprova"]),
    ]

    def _detect_cols(header_row):
        """Mapeia índice → field a partir de uma linha de cabeçalho."""
        mapping = {}
        vals = [str(v).strip().lower() if pd.notna(v) else "" for v in header_row]
        for i, v in enumerate(vals):
            if not v:
                continue
            for field, kws in _COL_RULES:
                if field in mapping.values():
                    continue
                if all(k in v for k in kws if k):
                    mapping[i] = field
                    break
        return mapping

    def _is_date_row(v: str) -> bool:
        return bool(re.match(r"(Seg|Ter|Qua|Qui|Sex|S.b|Dom),?\s+\d", v, re.I))

    def _parse_time(v) -> str:
        """Normaliza valor de hora para 'HH:MM' ou ''."""
        if pd.isna(v):
            return ""
        s = str(v).strip()
        if re.match(r"^\d{1,2}:\d{2}$", s):
            return s if s != "00:00" else ""
        return ""

    # Pré-varredura: monta mapa row_index → nome.
    # O Excel coloca "Colaborador | Nome" ANTES do cabeçalho "Data" de cada bloco —
    # exceto o primeiro bloco, onde não há linha "Colaborador" precedente.
    # Solução: para cada linha "Colaborador", encontrar o próximo bloco "Data" e
    # associar o nome àquele bloco. O primeiro bloco "Data" sem precedente fica
    # sem nome por ora; será resolvido abaixo.
    data_header_rows = []   # índices das linhas de cabeçalho "Data"
    colab_at = {}           # índice da linha "Data" → nome do colaborador
    pending_nome = None

    raw_vals = list(raw.itertuples(index=True))
    for tup in raw_vals:
        i  = tup[0]
        f0 = str(tup[1]).strip() if pd.notna(tup[1]) else ""
        f1 = tup[2] if len(tup) > 2 else None

        if f0 == "Colaborador" and pd.notna(f1):
            pending_nome = str(f1).strip()
        elif f0.lower() in ("data", "date"):
            data_header_rows.append(i)
            if pending_nome is not None:
                colab_at[i] = pending_nome
                pending_nome = None

    # Primeiro bloco: procurar nome no primeiro "Colaborador" após o primeiro TOTAIS
    if data_header_rows and data_header_rows[0] not in colab_at:
        # Tentar encontrar o nome no próximo "Colaborador" logo após o primeiro TOTAIS
        first_totais = None
        for tup in raw_vals:
            f0 = str(tup[1]).strip() if pd.notna(tup[1]) else ""
            if f0.upper().startswith("TOTAL"):
                first_totais = tup[0]
                break
        if first_totais is not None:
            for tup in raw_vals:
                if tup[0] <= first_totais:
                    continue
                f0 = str(tup[1]).strip() if pd.notna(tup[1]) else ""
                f1 = tup[2] if len(tup) > 2 else None
                if f0 == "Colaborador" and pd.notna(f1):
                    # Este nome pertence ao segundo bloco, não ao primeiro —
                    # não podemos recuperar o primeiro. Marcar como desconhecido.
                    break
        colab_at[data_header_rows[0]] = "(Colaborador)"

    # Varredura principal
    cur_nome = "(Colaborador)"

    for _, row in raw.iterrows():
        vals  = list(row.values)
        first = str(vals[0]).strip() if pd.notna(vals[0]) else ""

        # Linha de nome do colaborador
        if first == "Colaborador":
            continue  # já processado na pré-varredura

        # Linha de cabeçalho
        if first.lower() in ("data", "date") and len(vals) >= 4:
            col_map  = _detect_cols(vals)
            row_i    = row.name
            cur_nome = colab_at.get(row_i, cur_nome)
            continue

        # Linha de totais → pula
        if first.upper().startswith("TOTAL"):
            continue

        # Linha de dados: começa com dia da semana
        if _is_date_row(first) and col_map:
            rec = {"nome": cur_nome}
            for idx, field in col_map.items():
                rec[field] = vals[idx] if idx < len(vals) else None
            # Normaliza datas e horas
            data_raw = str(rec.get("data", "")).strip()
            # "Seg, 02/03/2026" → "02/03/2026"
            m = re.search(r"(\d{2}/\d{2}/\d{4})", data_raw)
            if not m:
                continue
            rec["data"] = m.group(1)
            for f in ("entrada","saida_almoco","volta_almoco","saida","intervalo","ht","he_50","he_100"):
                rec[f] = _parse_time(rec.get(f))
            rec["motivo"] = str(rec.get("motivo","")).strip() if pd.notna(rec.get("motivo")) else ""
            rec["justificativa_he"] = str(rec.get("justificativa_he","")).strip() if pd.notna(rec.get("justificativa_he")) else ""
            # Só inclui dias úteis com algum registro
            dt = pd.to_datetime(rec["data"], dayfirst=True, errors="coerce")
            if pd.isna(dt):
                continue
            rec["_dt"]       = dt
            rec["_weekday"]  = dt.weekday()
            rows.append(rec)

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["_dt"] = pd.to_datetime(df["data"], dayfirst=True, errors="coerce")
    return df


# ─── Enriquecimento de grupos ─────────────────────────────────────────────────

def _build_grupo_map() -> dict:
    """Carrega eco_checklist.json e monta {nome_lower: grupo}."""
    chk_path = os.path.join(_CACHE_DIR, "eco_checklist.json")
    if not os.path.exists(chk_path):
        return {}
    try:
        with open(chk_path, encoding="utf-8") as f:
            data = json.load(f)
        from _eco_funcoes import cargo_para_grupo
        mp = {}
        for med_data in data.values():
            for sheet_rows in med_data.get("sheets", {}).values():
                for colab in sheet_rows:
                    nome  = colab.get("colaborador", "")
                    cargo = colab.get("funcao", "")
                    grupo = cargo_para_grupo(cargo) or "Outros"
                    if nome:
                        mp[nome.strip().lower()] = (grupo, cargo)
        return mp
    except Exception:
        return {}


def _enrich_grupos(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adiciona colunas 'grupo' e 'funcao' ao DataFrame via match exato de nome
    com eco_checklist.json. Sem fuzzy matching — evita atribuições incorretas.
    Pessoas fora do checklist → grupo 'Outros'.
    """
    gmap = _build_grupo_map()
    grupos  = []
    funcoes = []
    is_eco  = []
    for nome in df["nome"]:
        key  = str(nome).strip().lower()
        info = gmap.get(key)
        grupos.append(info[0] if info else "Outros")
        funcoes.append(info[1] if info else "")
        # is_eco: True se nome consta no checklist ECO (qualquer cargo/grupo)
        is_eco.append(bool(info))
    df = df.copy()
    df["grupo"]  = grupos
    df["funcao"] = funcoes
    df["is_eco"] = is_eco
    return df


# ─── Helpers de tempo ─────────────────────────────────────────────────────────

def _hhmm_to_min(s: str) -> int | None:
    """'HH:MM' → minutos desde meia-noite. '' ou None → None."""
    if not s or s == "00:00":
        return None
    try:
        h, m = s.split(":")
        return int(h) * 60 + int(m)
    except Exception:
        return None


def _min_to_hhmm(m: float | None) -> str:
    if m is None:
        return "—"
    m = int(round(m))
    return f"{m//60:02d}:{m%60:02d}"


def _he_total_min(he50: str, he100: str) -> int:
    """Soma HE50 + HE100 em minutos."""
    def _p(s):
        if not s:
            return 0
        try:
            h, m = s.split(":")
            return int(h) * 60 + int(m)
        except Exception:
            return 0
    return _p(he50) + _p(he100)


# ─── Cache ───────────────────────────────────────────────────────────────────

def _salvar_cache(raw_bytes: bytes):
    """Salva raw bytes do Excel PontoMais no disco (formato original, não reprocessado)."""
    os.makedirs(_CACHE_DIR, exist_ok=True)
    with open(_CACHE_XLSX, "wb") as f:
        f.write(raw_bytes)
    with open(_CACHE_META, "w", encoding="utf-8") as f:
        json.dump({"ultima_atualizacao": date.today().isoformat()}, f)


def _carregar_cache() -> tuple:
    if not os.path.exists(_CACHE_XLSX):
        return None, ""
    try:
        with open(_CACHE_XLSX, "rb") as f:
            raw_bytes = f.read()
        ts = ""
        if os.path.exists(_CACHE_META):
            with open(_CACHE_META, encoding="utf-8") as f:
                ts = json.load(f).get("ultima_atualizacao", "")
        return raw_bytes, ts
    except Exception:
        return None, ""


@st.cache_data(ttl=3600)
def _processar_dados(raw_bytes: bytes) -> pd.DataFrame:
    """Parse + enrich em cache Streamlit. Detecta HTML vs XLSX automaticamente."""
    is_html = raw_bytes[:100].lstrip().startswith(b"<!") or b"<html" in raw_bytes[:200].lower()
    df = _parse_html_report(raw_bytes) if is_html else _parse_blocos(raw_bytes)
    if df.empty:
        return df
    return _enrich_grupos(df)


def _carregar_dados() -> tuple:
    """Retorna (df, timestamp)."""
    if "ep_raw_bytes" in st.session_state:
        raw_bytes = st.session_state["ep_raw_bytes"]
        ts        = st.session_state.get("ep_ts", "")
        df        = _processar_dados(raw_bytes)
        return df, ts
    raw_bytes, ts = _carregar_cache()
    if raw_bytes is not None:
        st.session_state["ep_raw_bytes"] = raw_bytes
        st.session_state["ep_ts"]        = ts
        df = _processar_dados(raw_bytes)
        return df, ts
    return None, ""


# ─── Sincronização ────────────────────────────────────────────────────────────

def _fetch_espelho_ponto_raw(login: str, senha: str, ini: str, fim: str) -> bytes:
    """
    Baixa os bytes brutos do Excel PontoMais via API REST.
    Retorna os bytes no formato original (bloco por colaborador).
    Executado em segundo plano via _eco_bg_loader.
    """
    from _eco_pontomais_sync import _login, _gerar_relatorio

    def _fmt(s: str) -> str:
        d, m, y = s.strip().split("/")
        return f"{y}-{m}-{d}"

    auth = _login(login, senha)
    return _gerar_relatorio(auth, _fmt(ini), _fmt(fim))


def _iniciar_sync():
    """Inicia a sincronização com PontoMais em segundo plano."""
    try:
        login = st.secrets.get("pontomais_login", "37895496816")
        senha = st.secrets.get("pontomais_senha", "Afirma@03")
    except Exception:
        login, senha = "37895496816", "Afirma@03"

    if not senha:
        st.error("Senha do PontoMais não configurada.")
        return

    hoje = date.today()
    ini  = date(hoje.year, hoje.month, 1).strftime("%d/%m/%Y")
    fim  = hoje.strftime("%d/%m/%Y")
    start_bg_task("espelho_ponto", _fetch_espelho_ponto_raw, login, senha, ini, fim)


def _render_upload():
    st.markdown(
        '<div class="ep-upload-hint">'
        '<strong>Sem dados.</strong> Clique em <strong>↺ Atualizar</strong> '
        'para buscar do PontoMais, ou faça upload manual abaixo ↓'
        '</div>',
        unsafe_allow_html=True,
    )
    uploaded = st.file_uploader("Excel/CSV PontoMais", type=["xlsx","xls","csv"],
                                 key="ep_upload", label_visibility="collapsed")
    if uploaded:
        try:
            raw_bytes = uploaded.getvalue()
            buf2 = io.BytesIO(raw_bytes)
            df_raw = pd.read_excel(buf2, dtype=str, header=None)
            _salvar_cache(df_raw)
            st.session_state["ep_raw_bytes"] = raw_bytes
            st.session_state["ep_ts"]        = date.today().isoformat()
            st.session_state.pop("ep_show_upload", None)
            _processar_dados.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {e}")


# ─── Renderização ─────────────────────────────────────────────────────────────

def _esc(s): return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")


def _render_kpis(df: pd.DataFrame, ts: str):
    n_colab = df["nome"].nunique()

    # HE total (minutos → horas)
    he_min = df.apply(lambda r: _he_total_min(r.get("he_50",""), r.get("he_100","")), axis=1).sum()
    he_h   = he_min / 60

    # Médias de entrada, almoço e saída (apenas dias com registro)
    entradas = df["entrada"].apply(_hhmm_to_min).dropna()
    almoco_s = df["saida_almoco"].apply(_hhmm_to_min).dropna()
    almoco_v = df["volta_almoco"].apply(_hhmm_to_min).dropna()
    saidas   = df["saida"].apply(_hhmm_to_min).dropna()

    avg_entrada = entradas.mean() if len(entradas) else None
    avg_almoco  = almoco_s.mean() if len(almoco_s) else None
    avg_volta   = almoco_v.mean() if len(almoco_v) else None
    avg_saida   = saidas.mean()   if len(saidas)   else None

    # Dias com HE
    dias_he = df[df.apply(lambda r: _he_total_min(r.get("he_50",""), r.get("he_100","")) > 0, axis=1)]["_dt"].nunique()

    kpis = [
        (str(n_colab),                    "#7BBF6A", "Colaboradores"),
        (f"{he_h:.1f}h",                  "#F7B731", "Horas extras total"),
        (str(dias_he),                    "#FFB347", "Dias c/ HE"),
        (_min_to_hhmm(avg_entrada),       "#4CC9F0", "Entrada média"),
        (_min_to_hhmm(avg_almoco),        "#BFCF99", "Saída almoço média"),
        (_min_to_hhmm(avg_volta),         "#BFCF99", "Volta almoço média"),
        (_min_to_hhmm(avg_saida),         "#A29BFE", "Saída média"),
    ]
    parts = ['<div class="ep-kpi-grid">']
    for val, cor, lbl in kpis:
        parts.append(f'<div class="ep-kpi"><div class="kv" style="color:{cor}">{val}</div>'
                     f'<div class="kl">{lbl}</div></div>')
    parts.append('</div>')
    if ts:
        parts.append(f'<div class="ep-ts">Atualizado em: {ts}</div>')
    st.markdown("".join(parts), unsafe_allow_html=True)


def _render_tabela_horarios(df: pd.DataFrame):
    """Grade: Colaborador × Dia — células mostram Entrada / Almoço / Saída."""
    dates = sorted(df["_dt"].dropna().unique())
    if not dates:
        return
    hoje = pd.Timestamp(date.today())
    pessoas = sorted(df["nome"].dropna().unique())
    idx = {(r["nome"], r["_dt"]): r for _, r in df.iterrows()}

    # Referência de entrada normal: 07:57 (15 min tolerância)
    ENT_REF = 7 * 60 + 57
    SAI_REF = 17 * 60 + 57

    html = ['<div class="ep-wrap"><table class="ep-tbl"><thead><tr>',
            '<th style="text-align:left;padding-left:8px">Colaborador</th>']
    for dt in dates:
        wk = dt.weekday()
        sty = 'style="color:#F7B731"' if dt == hoje else ""
        lbl = "HOJE" if dt == hoje else f"{dt.day:02d}"
        html.append(f'<th {sty}>{lbl}<br><span style="font-size:.5rem;opacity:.6">{_DAY_ABBR[wk]}</span></th>')
    html.append('<th>↑ ENT avg</th><th>↓ SAÍ avg</th><th>HE</th></tr></thead><tbody>')

    for pi, pessoa in enumerate(pessoas):
        rows_p = df[df["nome"] == pessoa]
        grupo  = rows_p["grupo"].iloc[0]  if "grupo"  in rows_p.columns else "Outros"
        funcao = rows_p["funcao"].iloc[0] if "funcao" in rows_p.columns else ""
        cor_g  = _COR_GRUPO.get(grupo, "#8FA882")
        sep    = ' class="ep-sep"' if pi > 0 else ""

        ents_p = rows_p["entrada"].apply(_hhmm_to_min).dropna()
        sais_p = rows_p["saida"].apply(_hhmm_to_min).dropna()
        he_p   = rows_p.apply(lambda r: _he_total_min(r.get("he_50",""), r.get("he_100","")), axis=1).sum()
        avg_e  = _min_to_hhmm(ents_p.mean() if len(ents_p) else None)
        avg_s  = _min_to_hhmm(sais_p.mean() if len(sais_p) else None)
        he_str = _min_to_hhmm(he_p) if he_p > 0 else "—"

        html.append(f'<tr{sep}>')
        html.append(f'<td class="ep-nome"><strong>{_esc(pessoa)}</strong>'
                    f'<small style="color:{cor_g}">{_esc(funcao or grupo)}</small></td>')

        for dt in dates:
            hj_sty = "outline:2px solid #F7B731;outline-offset:-1px;" if dt == hoje else ""
            rec    = idx.get((pessoa, dt))
            wk     = dt.weekday()

            if rec is None or wk >= 5:
                html.append(f'<td class="ep-ne" style="{hj_sty}">—</td>')
                continue
            if not rec.get("entrada") and not rec.get("saida"):
                mot = rec.get("motivo","")
                lbl_c = mot[:3].upper() if mot else "F"
                html.append(f'<td class="ep-ne" style="{hj_sty}">{lbl_c}</td>')
                continue

            ent = rec.get("entrada","")
            alm = rec.get("saida_almoco","")
            vlt = rec.get("volta_almoco","")
            sai = rec.get("saida","")

            ent_m = _hhmm_to_min(ent)
            sai_m = _hhmm_to_min(sai)

            # Classe de cor entrada
            if ent_m and ent_m < ENT_REF - 15:
                ent_cls = "ep-early"
            elif ent_m and ent_m > ENT_REF + 15:
                ent_cls = "ep-late"
            else:
                ent_cls = "ep-norm"

            # Almoço (duração)
            alm_dur = ""
            if alm and vlt:
                a, v = _hhmm_to_min(alm), _hhmm_to_min(vlt)
                if a and v:
                    diff = v - a
                    alm_dur = f"{diff//60:01d}:{diff%60:02d}"

            # Tooltip detalhado
            he = _he_total_min(rec.get("he_50",""), rec.get("he_100",""))
            tip_lines = [
                f'<div class="ep-tip-lbl">{dt.strftime("%d/%m/%Y")} ({_DAY_ABBR[wk]})</div>',
                f'<div style="display:flex;justify-content:space-between;gap:10px">'
                f'<span style="color:#6b7f8d">Entrada</span>'
                f'<span style="color:#BFCF99;font-weight:600">{ent or "—"}</span></div>',
                f'<div style="display:flex;justify-content:space-between;gap:10px">'
                f'<span style="color:#6b7f8d">Saída</span>'
                f'<span style="color:#BFCF99">{sai or "—"}</span></div>',
            ]
            if alm:
                tip_lines.append(
                    f'<div style="display:flex;justify-content:space-between;gap:10px">'
                    f'<span style="color:#6b7f8d">Almoço</span>'
                    f'<span style="color:#8FA882">{alm}–{vlt} ({alm_dur})</span></div>'
                )
            if he > 0:
                tip_lines.append(
                    f'<div style="display:flex;justify-content:space-between;gap:10px">'
                    f'<span style="color:#6b7f8d">HE total</span>'
                    f'<span style="color:#F7B731;font-weight:600">{_min_to_hhmm(he)}</span></div>'
                )
                he50  = rec.get("he_50","")
                he100 = rec.get("he_100","")
                if he50:
                    tip_lines.append(f'<div style="color:#A0B090;font-size:.58rem;text-align:right">50%: {he50}  100%: {he100 or "—"}</div>')
            if rec.get("motivo"):
                tip_lines.append(f'<div style="color:#8FA882;margin-top:3px;font-size:.58rem">Motivo: {_esc(rec["motivo"][:40])}</div>')
            if rec.get("justificativa_he"):
                tip_lines.append(f'<div style="color:#A29BFE;margin-top:2px;font-size:.58rem">Justif.: {_esc(rec["justificativa_he"][:50])}</div>')
            tip = f'<div class="ep-tip-box" style="min-width:160px">{"".join(tip_lines)}</div>'

            # Célula: entrada / saída / HE empilhados
            he = _he_total_min(rec.get("he_50",""), rec.get("he_100",""))
            sai_col = "#F7B731" if he > 0 else "#8FA882"
            he_line = (
                f'<div style="color:#F7B731;font-size:.52rem;line-height:1.1">⚡{_min_to_hhmm(he)}</div>'
                if he > 0 else ""
            )
            cell_html = (
                f'<div style="line-height:1.25">'
                f'<div style="font-weight:600;font-size:.63rem">{ent or "—"}</div>'
                f'<div style="color:{sai_col};font-size:.55rem">↓{sai or "—"}</div>'
                f'{he_line}'
                f'</div>'
            )
            html.append(
                f'<td class="{ent_cls}" style="{hj_sty};padding:2px 3px;">'
                f'<span class="ep-tip">{cell_html}{tip}</span></td>'
            )

        he_cls = "ep-he-pos" if he_p > 0 else "ep-he-zero"
        html.append(f'<td class="ep-total">{avg_e}</td>'
                    f'<td class="ep-total">{avg_s}</td>'
                    f'<td class="{he_cls}">{he_str}</td></tr>')

    html.append('</tbody></table></div>')
    st.markdown("".join(html), unsafe_allow_html=True)


def _render_tabela_he(df: pd.DataFrame):
    """
    Lista vertical de dias com HE por colaborador.
    Apenas mostra linhas com HE > 0 — omite dias sem extras.
    """
    hoje    = pd.Timestamp(date.today())
    pessoas = sorted(df["nome"].dropna().unique())

    # ── totais globais para o cabeçalho ──────────────────────────────────────
    he_grand_50  = sum(_hhmm_to_min(v) or 0 for v in df["he_50"])
    he_grand_100 = sum(_hhmm_to_min(v) or 0 for v in df["he_100"])
    he_grand_tot = he_grand_50 + he_grand_100
    n_dias_he    = int((df.apply(
        lambda r: _he_total_min(r.get("he_50",""), r.get("he_100","")), axis=1) > 0).sum())

    # ── banner de totais ──────────────────────────────────────────────────────
    st.markdown(
        f'<div style="display:flex;gap:16px;margin-bottom:12px;flex-wrap:wrap">'
        f'<div class="ep-kpi"><div class="kv" style="color:#F7B731">{_min_to_hhmm(he_grand_tot)}</div>'
        f'<div class="kl">Total HE</div></div>'
        f'<div class="ep-kpi"><div class="kv" style="color:#FFB347">{_min_to_hhmm(he_grand_50)}</div>'
        f'<div class="kl">HE 50%</div></div>'
        f'<div class="ep-kpi"><div class="kv" style="color:#FF6B6B">{_min_to_hhmm(he_grand_100)}</div>'
        f'<div class="kl">HE 100%</div></div>'
        f'<div class="ep-kpi"><div class="kv" style="color:#BFCF99">{n_dias_he}</div>'
        f'<div class="kl">Dias c/ HE</div></div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    html = [
        '<div class="ep-wrap"><table class="ep-tbl"><thead><tr>',
        '<th style="text-align:left;padding-left:8px;min-width:140px">Colaborador</th>',
        '<th style="min-width:54px">Data</th>',
        '<th style="min-width:34px">Dia</th>',
        '<th style="min-width:54px;color:#BFCF99">↑ Entrada</th>',
        '<th style="min-width:54px;color:#BFCF99">↓ Saída</th>',
        '<th style="min-width:54px;color:#F7B731">⚡ HE Total</th>',
        '<th style="min-width:50px">HE 50%</th>',
        '<th style="min-width:50px">HE 100%</th>',
        '<th style="text-align:left;padding-left:6px;min-width:100px">Motivo / Justif.</th>',
        '</tr></thead><tbody>',
    ]

    for pi, pessoa in enumerate(pessoas):
        rows_p = df[df["nome"] == pessoa].sort_values("_dt")
        grupo  = rows_p["grupo"].iloc[0] if "grupo" in rows_p.columns else "Outros"
        funcao = rows_p["funcao"].iloc[0] if "funcao" in rows_p.columns else ""
        cor_g  = _COR_GRUPO.get(grupo, "#8FA882")

        # Só linhas com HE
        he_rows = [
            r for _, r in rows_p.iterrows()
            if _he_total_min(r.get("he_50",""), r.get("he_100","")) > 0
        ]
        if not he_rows:
            continue

        he50_t  = sum(_hhmm_to_min(r.get("he_50",""))  or 0 for r in he_rows)
        he100_t = sum(_hhmm_to_min(r.get("he_100","")) or 0 for r in he_rows)
        he_tot  = he50_t + he100_t

        for di, rec in enumerate(he_rows):
            dt  = rec.get("_dt")
            wk  = dt.weekday() if pd.notna(dt) else 0
            ts  = pd.Timestamp(dt)
            is_hj   = ts == hoje
            sep_sty = ' class="ep-sep"' if di == 0 and pi > 0 else ""
            dt_sty  = 'style="color:#F7B731;font-weight:700"' if is_hj else ""

            he    = _he_total_min(rec.get("he_50",""), rec.get("he_100",""))
            he50  = rec.get("he_50","")  or "—"
            he100 = rec.get("he_100","") or "—"
            ent   = rec.get("entrada","")  or "—"
            sai   = rec.get("saida","")    or "—"
            mot   = rec.get("motivo","")
            just  = rec.get("justificativa_he","")

            # Nome só na primeira linha do colaborador (rowspan)
            if di == 0:
                nome_cell = (
                    f'<td class="ep-nome" rowspan="{len(he_rows)}">'
                    f'<strong>{_esc(pessoa)}</strong>'
                    f'<small style="color:{cor_g}">{_esc(funcao or grupo)}</small>'
                    f'<small style="color:#F7B731;margin-top:2px">⚡{_min_to_hhmm(he_tot)}</small>'
                    f'</td>'
                )
            else:
                nome_cell = ""

            # Tooltip HE
            tip_lines = [
                f'<div class="ep-tip-lbl">{ts.strftime("%d/%m/%Y")} ({_DAY_ABBR[wk]})</div>',
                f'<div style="display:flex;justify-content:space-between;gap:10px">'
                f'<span style="color:#6b7f8d">Entrada→Saída</span>'
                f'<span style="color:#BFCF99">{ent} → {sai}</span></div>',
                f'<div style="display:flex;justify-content:space-between;gap:10px">'
                f'<span style="color:#6b7f8d">HE 50%</span>'
                f'<span style="color:#F7B731;font-weight:600">{he50}</span></div>',
                f'<div style="display:flex;justify-content:space-between;gap:10px">'
                f'<span style="color:#6b7f8d">HE 100%</span>'
                f'<span style="color:#F7B731">{he100}</span></div>',
            ]
            if mot:
                tip_lines.append(
                    f'<div style="color:#8FA882;margin-top:3px;font-size:.58rem">Motivo: {_esc(mot[:50])}</div>')
            if just:
                tip_lines.append(
                    f'<div style="color:#A29BFE;font-size:.58rem">Justif.: {_esc(just[:60])}</div>')
            tip = f'<div class="ep-tip-box" style="min-width:190px">{"".join(tip_lines)}</div>'

            mot_cell = ""
            if mot:
                mot_cell += f'<span style="color:#8FA882;font-size:.58rem">{_esc(mot[:25])}</span>'
            if just:
                mot_cell += (f'{"<br>" if mot else ""}'
                             f'<span style="color:#A29BFE;font-size:.55rem">↳{_esc(just[:28])}</span>')

            bg = "background:rgba(247,183,49,.05);" if is_hj else ""
            html.append(
                f'<tr{sep_sty} style="{bg}">'
                f'{nome_cell}'
                f'<td {dt_sty}>{ts.strftime("%d/%m")}</td>'
                f'<td style="color:#6b7f8d;font-size:.58rem">{_DAY_ABBR[wk]}</td>'
                f'<td style="color:#BFCF99">{ent}</td>'
                f'<td style="color:#BFCF99">{sai}</td>'
                f'<td class="ep-he-pos">'
                f'<span class="ep-tip">{_min_to_hhmm(he)}{tip}</span></td>'
                f'<td style="color:#FFB347">{he50}</td>'
                f'<td style="color:#FF9F6B">{he100}</td>'
                f'<td style="text-align:left;padding-left:6px">{mot_cell}</td>'
                f'</tr>'
            )

    html.append('</tbody></table></div>')
    st.markdown("".join(html), unsafe_allow_html=True)


def _render_tabela_almoco(df: pd.DataFrame):
    """Grade: Colaborador × Dia — duração do almoço (saída – volta)."""
    dates   = sorted(df["_dt"].dropna().unique())
    pessoas = sorted(df["nome"].dropna().unique())
    idx     = {(r["nome"], r["_dt"]): r for _, r in df.iterrows()}
    hoje    = pd.Timestamp(date.today())

    html = ['<div class="ep-wrap"><table class="ep-tbl"><thead><tr>',
            '<th style="text-align:left;padding-left:8px">Colaborador</th>']
    for dt in dates:
        sty = 'style="color:#F7B731"' if dt == hoje else ""
        html.append(f'<th {sty}>{dt.day:02d}<br>'
                    f'<span style="font-size:.5rem;opacity:.6">{_DAY_ABBR[dt.weekday()]}</span></th>')
    html.append('<th>Saída avg</th><th>Volta avg</th><th>Dur avg</th></tr></thead><tbody>')

    for pi, pessoa in enumerate(pessoas):
        rows_p  = df[df["nome"] == pessoa]
        sep     = ' class="ep-sep"' if pi > 0 else ""
        grupo   = rows_p["grupo"].iloc[0] if "grupo" in rows_p.columns else "Outros"
        cor_g   = _COR_GRUPO.get(grupo, "#8FA882")
        funcao  = rows_p["funcao"].iloc[0] if "funcao" in rows_p.columns else ""

        sai_alm = rows_p["saida_almoco"].apply(_hhmm_to_min).dropna()
        vlt_alm = rows_p["volta_almoco"].apply(_hhmm_to_min).dropna()
        avg_sa  = _min_to_hhmm(sai_alm.mean() if len(sai_alm) else None)
        avg_va  = _min_to_hhmm(vlt_alm.mean() if len(vlt_alm) else None)
        durs    = []

        html.append(f'<tr{sep}>')
        html.append(f'<td class="ep-nome"><strong>{_esc(pessoa)}</strong>'
                    f'<small style="color:{cor_g}">{_esc(funcao or grupo)}</small></td>')

        for dt in dates:
            hj_sty = "outline:2px solid #F7B731;outline-offset:-1px;" if dt == hoje else ""
            rec    = idx.get((pessoa, dt))
            if rec is None or dt.weekday() >= 5:
                html.append(f'<td class="ep-ne" style="{hj_sty}">—</td>')
                continue
            sa = _hhmm_to_min(rec.get("saida_almoco",""))
            va = _hhmm_to_min(rec.get("volta_almoco",""))
            if not sa or not va:
                html.append(f'<td class="ep-ne" style="{hj_sty}">—</td>')
                continue
            dur = va - sa
            durs.append(dur)
            # Almoço > 80min = longo, < 50min = curto
            if dur > 80:
                cls = "ep-late"
            elif dur < 50:
                cls = "ep-early"
            else:
                cls = "ep-norm"
            tip = (f'<div class="ep-tip-box">'
                   f'<div class="ep-tip-lbl">{dt.strftime("%d/%m")}</div>'
                   f'<div>Saída: {rec.get("saida_almoco","—")}</div>'
                   f'<div>Volta: {rec.get("volta_almoco","—")}</div>'
                   f'<div>Duração: {_min_to_hhmm(dur)}</div>'
                   f'</div>')
            html.append(f'<td class="{cls}" style="{hj_sty}">'
                        f'<span class="ep-tip">{_min_to_hhmm(dur)}{tip}</span></td>')

        avg_dur = _min_to_hhmm(sum(durs)/len(durs)) if durs else "—"
        html.append(f'<td class="ep-total">{avg_sa}</td>'
                    f'<td class="ep-total">{avg_va}</td>'
                    f'<td class="ep-total">{avg_dur}</td></tr>')
    html.append('</tbody></table></div>')
    st.markdown("".join(html), unsafe_allow_html=True)


# ─── Tabela Resumo ───────────────────────────────────────────────────────────

def _render_tabela_resumo(df: pd.DataFrame):
    """
    Tabela compacta por colaborador com 3 colunas:
      Entrada (média) · Saída (média) · HE Total
    Cada célula tem tooltip com o detalhamento dia a dia.
    """
    pessoas = sorted(df["nome"].dropna().unique())
    hoje    = pd.Timestamp(date.today())

    ENT_REF = 7 * 60 + 57   # referência entrada: 07:57
    SAI_REF = 17 * 60 + 57  # referência saída:   17:57

    html = [
        '<div class="ep-wrap"><table class="ep-tbl" style="max-width:720px">',
        '<thead><tr>',
        '<th style="text-align:left;padding-left:8px;min-width:160px">Colaborador</th>',
        '<th style="min-width:90px">↑ Entrada</th>',
        '<th style="min-width:90px">↓ Saída</th>',
        '<th style="min-width:90px">⚡ HE Total</th>',
        '</tr></thead><tbody>',
    ]

    for pi, pessoa in enumerate(pessoas):
        rows_p = df[df["nome"] == pessoa].sort_values("_dt")
        grupo  = rows_p["grupo"].iloc[0]  if "grupo"  in rows_p.columns else "Outros"
        funcao = rows_p["funcao"].iloc[0] if "funcao" in rows_p.columns else ""
        cor_g  = _COR_GRUPO.get(grupo, "#8FA882")
        sep    = ' class="ep-sep"' if pi > 0 else ""

        # ── Médias ────────────────────────────────────────────────────────────
        ents  = rows_p["entrada"].apply(_hhmm_to_min).dropna()
        sais  = rows_p["saida"].apply(_hhmm_to_min).dropna()
        avg_e = ents.mean() if len(ents) else None
        avg_s = sais.mean() if len(sais) else None
        he_total = rows_p.apply(
            lambda r: _he_total_min(r.get("he_50", ""), r.get("he_100", "")), axis=1
        ).sum()

        # ── Cor entrada ───────────────────────────────────────────────────────
        if avg_e and avg_e < ENT_REF - 15:
            ent_cls = "ep-early"
        elif avg_e and avg_e > ENT_REF + 15:
            ent_cls = "ep-late"
        else:
            ent_cls = "ep-norm"

        # ── Cor saída ─────────────────────────────────────────────────────────
        if avg_s and avg_s > SAI_REF + 30:
            sai_cls = "ep-late"   # saída muito tardia = HE provável
        else:
            sai_cls = "ep-norm"

        # ── Tooltip Entrada — detalhes por dia ────────────────────────────────
        tip_ent_lines = ['<div class="ep-tip-lbl">Entrada por dia</div>']
        for _, r in rows_p.iterrows():
            dt = r.get("_dt")
            if pd.isna(dt) or dt.weekday() >= 5:
                continue
            v = r.get("entrada", "")
            if not v:
                mot = r.get("motivo", "")
                lbl = f'<span style="color:#3a4a5e">{mot[:8] or "—"}</span>'
            else:
                m = _hhmm_to_min(v)
                if m and m < ENT_REF - 15:
                    col = "#4CC9F0"
                elif m and m > ENT_REF + 15:
                    col = "#FF6B6B"
                else:
                    col = "#BFCF99"
                hj = " ★" if dt == hoje else ""
                lbl = f'<span style="color:{col}">{v}</span>{hj}'
            tip_ent_lines.append(
                f'<div style="display:flex;justify-content:space-between;gap:12px">'
                f'<span style="color:#6b7f8d">{dt.strftime("%d/%m")}</span>{lbl}</div>'
            )
        tip_ent = (
            '<div class="ep-tip-box" style="min-width:130px">'
            + "".join(tip_ent_lines)
            + "</div>"
        )

        # ── Tooltip Saída — detalhes por dia ──────────────────────────────────
        tip_sai_lines = ['<div class="ep-tip-lbl">Saída por dia</div>']
        for _, r in rows_p.iterrows():
            dt = r.get("_dt")
            if pd.isna(dt) or dt.weekday() >= 5:
                continue
            v = r.get("saida", "")
            he = _he_total_min(r.get("he_50", ""), r.get("he_100", ""))
            if not v:
                lbl = f'<span style="color:#3a4a5e">—</span>'
            else:
                m = _hhmm_to_min(v)
                if he > 0:
                    col = "#F7B731"   # HE = saída tardia intencional
                elif m and m > SAI_REF + 30:
                    col = "#FF6B6B"
                else:
                    col = "#BFCF99"
                hj = " ★" if dt == hoje else ""
                he_tag = f' <span style="color:#F7B731;font-size:.55rem">+HE</span>' if he > 0 else ""
                lbl = f'<span style="color:{col}">{v}</span>{he_tag}{hj}'
            tip_sai_lines.append(
                f'<div style="display:flex;justify-content:space-between;gap:12px">'
                f'<span style="color:#6b7f8d">{dt.strftime("%d/%m")}</span>{lbl}</div>'
            )
        tip_sai = (
            '<div class="ep-tip-box" style="min-width:130px">'
            + "".join(tip_sai_lines)
            + "</div>"
        )

        # ── Tooltip HE — por dia ──────────────────────────────────────────────
        tip_he_lines = ['<div class="ep-tip-lbl">HE por dia</div>']
        for _, r in rows_p.iterrows():
            dt = r.get("_dt")
            if pd.isna(dt) or dt.weekday() >= 5:
                continue
            he = _he_total_min(r.get("he_50", ""), r.get("he_100", ""))
            if he == 0:
                continue
            he50  = r.get("he_50", "")
            he100 = r.get("he_100", "")
            mot  = r.get("motivo", "")
            just = r.get("justificativa_he", "")
            extra_info = ""
            if mot:
                extra_info += f'<div style="color:#8FA882;font-size:.55rem">Motivo: {_esc(mot[:40])}</div>'
            if just:
                extra_info += f'<div style="color:#A29BFE;font-size:.55rem">Justif.: {_esc(just[:40])}</div>'
            tip_he_lines.append(
                f'<div style="margin-bottom:4px">'
                f'<div style="display:flex;justify-content:space-between;gap:12px">'
                f'<span style="color:#6b7f8d">{dt.strftime("%d/%m")}</span>'
                f'<span style="color:#F7B731">{_min_to_hhmm(he)}'
                f'<span style="color:#8FA882;font-size:.55rem"> (50%:{he50 or "—"} 100%:{he100 or "—"})</span>'
                f'</span></div>'
                f'{extra_info}'
                f'</div>'
            )
        if len(tip_he_lines) == 1:
            tip_he_lines.append('<div style="color:#3a4a5e">Sem horas extras</div>')
        tip_he = (
            '<div class="ep-tip-box" style="min-width:180px">'
            + "".join(tip_he_lines)
            + "</div>"
        )

        # ── HE display ────────────────────────────────────────────────────────
        he_str = _min_to_hhmm(he_total) if he_total > 0 else "—"
        he_cls = "ep-he-pos" if he_total > 0 else "ep-he-zero"

        html.append(f'<tr{sep}>')
        html.append(
            f'<td class="ep-nome">'
            f'<strong>{_esc(pessoa)}</strong>'
            f'<small style="color:{cor_g}">{_esc(funcao or grupo)}</small>'
            f'</td>'
        )
        html.append(
            f'<td class="{ent_cls}">'
            f'<span class="ep-tip">{_min_to_hhmm(avg_e)}{tip_ent}</span>'
            f'</td>'
        )
        html.append(
            f'<td class="{sai_cls}">'
            f'<span class="ep-tip">{_min_to_hhmm(avg_s)}{tip_sai}</span>'
            f'</td>'
        )
        html.append(
            f'<td class="{he_cls}">'
            f'<span class="ep-tip">{he_str}{tip_he}</span>'
            f'</td>'
        )
        html.append('</tr>')

    html.append('</tbody></table></div>')
    st.markdown("".join(html), unsafe_allow_html=True)


# ─── Resumo Diário por Profissional ──────────────────────────────────────────

_CSS_RDPP = """
<style>
.rdpp-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch;width:100%;margin-bottom:20px}
.rdpp-tbl{border-collapse:collapse;font-size:.65rem;font-family:Inter,sans-serif;width:100%;table-layout:auto}
.rdpp-tbl th{background:rgba(86,110,61,.22);color:#BFCF99;padding:5px 6px;
  text-align:center;font-weight:600;border:1px solid rgba(86,110,61,.15);
  font-size:.60rem;white-space:nowrap}
.rdpp-tbl td{padding:4px 5px;border:1px solid rgba(255,255,255,.05);
  text-align:center;white-space:nowrap;font-size:.63rem;vertical-align:middle}
.rdpp-nome{text-align:left!important;padding-left:8px!important;min-width:120px;
  font-weight:700;color:#E8EFD8;border-right:2px solid rgba(86,110,61,.25)!important;
  white-space:nowrap;max-width:180px;overflow:hidden;text-overflow:ellipsis}
.rdpp-nome small{font-size:.52rem;color:#8FA882;display:block;margin-top:1px}
.rdpp-sep td{border-top:2px solid rgba(86,110,61,.22)!important}
.rdpp-wk{background:rgba(255,255,255,.02);color:#3a4a5e}
.rdpp-today td{outline:2px solid rgba(247,183,49,.4);outline-offset:-1px}
.rdpp-he-day td.rdpp-he-cell{background:rgba(247,183,49,.12)}
.rdpp-ent-early{color:#4CC9F0;font-weight:600}
.rdpp-ent-late {color:#FF6B6B;font-weight:600}
.rdpp-ent-norm {color:#BFCF99}
.rdpp-he-val{color:#F7B731;font-weight:700}
.rdpp-abs{color:#3a4a5e;font-style:italic}
</style>
"""


def _render_resumo_diario_profissional(df: pd.DataFrame):
    """
    Tabela compacta: cada colaborador tem uma linha por dia,
    mostrando Entrada · Saída · HE com hovers detalhados.
    Colaboradores agrupados; dias úteis apenas (fins de semana omitidos).
    """
    st.markdown(_CSS_RDPP, unsafe_allow_html=True)

    pessoas = sorted(df["nome"].dropna().unique())
    hoje    = pd.Timestamp(date.today())
    ENT_REF = 7 * 60 + 57
    SAI_REF = 17 * 60 + 57

    # Todos os dias úteis do período
    all_dates = sorted([d for d in df["_dt"].dropna().unique() if pd.Timestamp(d).weekday() < 5])
    idx = {(r["nome"], r["_dt"]): r for _, r in df.iterrows()}

    html = [
        '<div class="rdpp-wrap"><table class="rdpp-tbl"><thead><tr>',
        '<th style="text-align:left;padding-left:8px;min-width:120px">Colaborador</th>',
        '<th>Data</th>',
        '<th>Dia</th>',
        '<th>↑ Entrada</th>',
        '<th>↓ Saída</th>',
        '<th>Intervalo</th>',
        '<th>H. Normais</th>',
        '<th style="color:#F7B731">⚡ HE</th>',
        '<th class="left" style="text-align:left;padding-left:6px">Motivo / Justif.</th>',
        '</tr></thead><tbody>',
    ]

    for pi, pessoa in enumerate(pessoas):
        rows_p = df[df["nome"] == pessoa]
        grupo  = rows_p["grupo"].iloc[0]  if "grupo"  in rows_p.columns else "Outros"
        funcao = rows_p["funcao"].iloc[0] if "funcao" in rows_p.columns else ""
        cor_g  = _COR_GRUPO.get(grupo, "#8FA882")
        dias_pessoa = [d for d in all_dates if (pessoa, d) in idx]

        if not dias_pessoa:
            continue

        for di, dt in enumerate(dias_pessoa):
            rec    = idx.get((pessoa, dt))
            ts     = pd.Timestamp(dt)
            wk     = ts.weekday()
            day_n  = _DAY_ABBR[wk]
            is_hj  = ts == hoje
            sep    = ' class="rdpp-sep"' if di == 0 and pi > 0 else ""

            # Nome só na primeira linha do colaborador
            if di == 0:
                nome_cell = (
                    f'<td class="rdpp-nome" rowspan="{len(dias_pessoa)}">'
                    f'{_esc(pessoa)}'
                    f'<small style="color:{cor_g}">{_esc(funcao or grupo)}</small>'
                    f'</td>'
                )
            else:
                nome_cell = ""

            dt_sty = 'style="color:#F7B731;font-weight:600"' if is_hj else ""
            row_extra_cls = " rdpp-today" if is_hj else ""

            if rec is None:
                html.append(
                    f'<tr{sep} class="rdpp-wk{row_extra_cls}">'
                    f'{nome_cell}'
                    f'<td {dt_sty}>{ts.strftime("%d/%m")}</td>'
                    f'<td style="color:#5a6a7e">{day_n}</td>'
                    f'<td class="rdpp-abs">—</td><td class="rdpp-abs">—</td>'
                    f'<td class="rdpp-abs">—</td><td class="rdpp-abs">—</td>'
                    f'<td class="rdpp-abs">—</td><td></td>'
                    f'</tr>'
                )
                continue

            ent   = rec.get("entrada","")
            sai   = rec.get("saida","")
            alm_s = rec.get("saida_almoco","")
            alm_v = rec.get("volta_almoco","")
            intv  = rec.get("intervalo","")
            ht    = rec.get("ht","")
            he50  = rec.get("he_50","")
            he100 = rec.get("he_100","")
            mot   = rec.get("motivo","")
            just  = rec.get("justificativa_he","")
            he    = _he_total_min(he50, he100)

            he_row_cls = " rdpp-he-day" if he > 0 else ""

            # Classe entrada
            ent_m = _hhmm_to_min(ent)
            if not ent and mot:
                ent_html = f'<span class="rdpp-abs">{_esc(mot[:6])}</span>'
            elif ent_m and ent_m < ENT_REF - 15:
                ent_html = f'<span class="rdpp-ent-early">{ent}</span>'
            elif ent_m and ent_m > ENT_REF + 15:
                ent_html = f'<span class="rdpp-ent-late">{ent}</span>'
            else:
                ent_html = f'<span class="rdpp-ent-norm">{ent or "—"}</span>'

            # Hover entrada
            tip_ent_lines = [
                f'<div class="ep-tip-lbl">{ts.strftime("%d/%m/%Y")} ({day_n})</div>',
                f'<div style="display:flex;justify-content:space-between;gap:10px">'
                f'<span style="color:#6b7f8d">Entrada</span>'
                f'<span style="color:#BFCF99;font-weight:600">{ent or "—"}</span></div>',
            ]
            if alm_s:
                tip_ent_lines.append(
                    f'<div style="display:flex;justify-content:space-between;gap:10px">'
                    f'<span style="color:#6b7f8d">Saída almoço</span>'
                    f'<span style="color:#8FA882">{alm_s}</span></div>'
                )
            if alm_v:
                tip_ent_lines.append(
                    f'<div style="display:flex;justify-content:space-between;gap:10px">'
                    f'<span style="color:#6b7f8d">Volta almoço</span>'
                    f'<span style="color:#8FA882">{alm_v}</span></div>'
                )
            tip_ent = (
                f'<div class="ep-tip-box" style="min-width:160px">'
                + "".join(tip_ent_lines) + "</div>"
            )
            ent_cell = f'<span class="ep-tip">{ent_html}{tip_ent}</span>'

            # Hover saída
            sai_m = _hhmm_to_min(sai)
            if he > 0:
                sai_col = "#F7B731"
            elif sai_m and sai_m > SAI_REF + 30:
                sai_col = "#FF6B6B"
            else:
                sai_col = "#BFCF99"
            sai_html = f'<span style="color:{sai_col}">{sai or "—"}</span>'
            tip_sai_lines = [
                f'<div class="ep-tip-lbl">{ts.strftime("%d/%m/%Y")} ({day_n})</div>',
                f'<div style="display:flex;justify-content:space-between;gap:10px">'
                f'<span style="color:#6b7f8d">Saída</span>'
                f'<span style="color:{sai_col};font-weight:600">{sai or "—"}</span></div>',
            ]
            if he > 0:
                tip_sai_lines.append(
                    f'<div style="color:#F7B731;font-size:.58rem;margin-top:2px">'
                    f'⚡ HE: {_min_to_hhmm(he)}</div>'
                )
            tip_sai = (
                f'<div class="ep-tip-box" style="min-width:150px">'
                + "".join(tip_sai_lines) + "</div>"
            )
            sai_cell = f'<span class="ep-tip">{sai_html}{tip_sai}</span>'

            # Hover HE
            if he > 0:
                tip_he_lines = [
                    f'<div class="ep-tip-lbl">{ts.strftime("%d/%m/%Y")} ({day_n})</div>',
                    f'<div style="display:flex;justify-content:space-between;gap:10px">'
                    f'<span style="color:#6b7f8d">Entrada→Saída</span>'
                    f'<span style="color:#BFCF99">{ent or "—"} → {sai or "—"}</span></div>',
                    f'<div style="display:flex;justify-content:space-between;gap:10px">'
                    f'<span style="color:#6b7f8d">HE 50%</span>'
                    f'<span style="color:#F7B731;font-weight:600">{he50 or "—"}</span></div>',
                    f'<div style="display:flex;justify-content:space-between;gap:10px">'
                    f'<span style="color:#6b7f8d">HE 100%</span>'
                    f'<span style="color:#F7B731">{he100 or "—"}</span></div>',
                ]
                if mot:
                    tip_he_lines.append(
                        f'<div style="color:#8FA882;margin-top:3px;font-size:.58rem">'
                        f'Motivo: {_esc(mot[:50])}</div>'
                    )
                if just:
                    tip_he_lines.append(
                        f'<div style="color:#A29BFE;margin-top:2px;font-size:.58rem">'
                        f'Justif.: {_esc(just[:60])}</div>'
                    )
                tip_he = (
                    f'<div class="ep-tip-box" style="min-width:190px">'
                    + "".join(tip_he_lines) + "</div>"
                )
                he_cell = (
                    f'<span class="ep-tip rdpp-he-val">'
                    f'{_min_to_hhmm(he)}{tip_he}</span>'
                )
                he_td_cls = ' class="rdpp-he-cell"'
            else:
                he_cell    = '<span style="color:#3a4a5e">—</span>'
                he_td_cls  = ""

            # Célula motivo/justificativa
            mot_cell = ""
            if mot:
                mot_cell += f'<span style="color:#8FA882">{_esc(mot[:30])}</span>'
            if just:
                mot_cell += (
                    f'{"<br>" if mot else ""}'
                    f'<span style="color:#A29BFE;font-size:.58rem">↳ {_esc(just[:35])}</span>'
                )

            html.append(
                f'<tr{sep} class="{he_row_cls.strip()}{row_extra_cls}">'
                f'{nome_cell}'
                f'<td {dt_sty}>{ts.strftime("%d/%m")}</td>'
                f'<td style="color:#6b7f8d">{day_n}</td>'
                f'<td>{ent_cell}</td>'
                f'<td>{sai_cell}</td>'
                f'<td style="color:#6b7f8d">{intv or "—"}</td>'
                f'<td style="color:#7BBF6A">{ht or "—"}</td>'
                f'<td{he_td_cls}>{he_cell}</td>'
                f'<td style="text-align:left;padding-left:6px">{mot_cell}</td>'
                f'</tr>'
            )

    html.append('</tbody></table></div>')
    st.markdown("".join(html), unsafe_allow_html=True)


# ─── Aba de Colaboradores ────────────────────────────────────────────────────

_CSS_COLAB = """
<style>
.ep-colab-grid{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0 18px 0}
.ep-colab-card{background:rgba(18,25,38,.85);border:1px solid rgba(86,110,61,.18);
  border-radius:8px;padding:7px 12px;font-size:.72rem;color:#BFCF99;cursor:pointer;
  transition:background .15s,border-color .15s;white-space:nowrap}
.ep-colab-card:hover{background:rgba(86,110,61,.2);border-color:rgba(86,110,61,.5)}
.ep-colab-card.selected{background:rgba(86,110,61,.3);border-color:#7BBF6A;color:#E8EFD8;font-weight:700}
.ep-colab-badge{font-size:.55rem;border-radius:4px;padding:1px 5px;margin-left:5px;
  vertical-align:middle;font-weight:600}

/* tabela mensal */
.ep-mon-wrap{overflow-x:auto;-webkit-overflow-scrolling:touch;width:100%}
.ep-mon-tbl{border-collapse:collapse;font-size:.68rem;font-family:Inter,sans-serif;width:100%}
.ep-mon-tbl th{background:rgba(86,110,61,.22);color:#BFCF99;padding:5px 8px;
  text-align:center;font-weight:600;border:1px solid rgba(86,110,61,.18);
  font-size:.62rem;white-space:nowrap}
.ep-mon-tbl th.left{text-align:left}
.ep-mon-tbl td{padding:5px 8px;border:1px solid rgba(255,255,255,.05);
  text-align:center;white-space:nowrap;font-size:.67rem;vertical-align:middle}
.ep-mon-tbl td.left{text-align:left}
.ep-mon-tbl tr.weekend td{opacity:.35}
.ep-mon-tbl tr.today td{outline:2px solid #F7B731;outline-offset:-1px}
.ep-mon-tbl tr.he-day td{background:rgba(247,183,49,.07)}
.ep-mon-ent-early{color:#4CC9F0;font-weight:700}
.ep-mon-ent-late {color:#FF6B6B;font-weight:700}
.ep-mon-ent-norm {color:#BFCF99}
.ep-mon-he{color:#F7B731;font-weight:700}
.ep-mon-abs{color:#3a4a5e;font-style:italic}
.ep-mon-mot{color:#8FA882;font-size:.6rem}
.ep-mon-total td{font-weight:700;color:#BFCF99;border-top:2px solid rgba(86,110,61,.3)!important;
  background:rgba(86,110,61,.1)!important}
</style>
"""

_MESES_PT = {1:"Janeiro",2:"Fevereiro",3:"Março",4:"Abril",5:"Maio",6:"Junho",
             7:"Julho",8:"Agosto",9:"Setembro",10:"Outubro",11:"Novembro",12:"Dezembro"}


def _render_tabela_mensal_colab(nome: str, rows: pd.DataFrame):
    """Tabela completa do mês para um colaborador: todos os dias com todas as colunas."""
    if rows.empty:
        st.info("Sem dados para este colaborador.")
        return

    grupo  = rows["grupo"].iloc[0]  if "grupo"  in rows.columns else "Outros"
    funcao = rows["funcao"].iloc[0] if "funcao" in rows.columns else ""
    cor_g  = _COR_GRUPO.get(grupo, "#8FA882")

    # Período do mês baseado nos dados
    dts    = rows["_dt"].dropna().sort_values()
    mes    = dts.iloc[0].month
    ano    = dts.iloc[0].year
    from calendar import monthrange
    n_dias = monthrange(ano, mes)[1]
    hoje   = pd.Timestamp(date.today())

    # Totais
    he50_tot  = sum(_hhmm_to_min(v) or 0 for v in rows["he_50"])
    he100_tot = sum(_hhmm_to_min(v) or 0 for v in rows["he_100"])
    ht_tot    = sum(_hhmm_to_min(v) or 0 for v in rows["ht"])
    ents      = rows["entrada"].apply(_hhmm_to_min).dropna()
    sais      = rows["saida"].apply(_hhmm_to_min).dropna()
    dias_he   = rows[rows.apply(lambda r: _he_total_min(r.get("he_50",""),r.get("he_100",""))>0,axis=1)]["_dt"].nunique()

    # Cabeçalho do colaborador
    st.markdown(
        f'<div style="margin:8px 0 14px 0">'
        f'<span style="font-size:1rem;font-weight:700;color:#E8EFD8">{_esc(nome)}</span>'
        f'<span class="ep-badge" style="background:{cor_g}22;color:{cor_g};margin-left:8px">'
        f'{_esc(funcao or grupo)}</span>'
        f'<span style="font-size:.7rem;color:#6b7f8d;margin-left:10px">'
        f'{_MESES_PT[mes]} {ano}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

    # KPIs rápidos
    kpis = [
        (_min_to_hhmm(ents.mean() if len(ents) else None), "#4CC9F0", "Entrada média"),
        (_min_to_hhmm(sais.mean() if len(sais) else None), "#A29BFE", "Saída média"),
        (_min_to_hhmm(he50_tot + he100_tot),               "#F7B731", "HE total"),
        (_min_to_hhmm(ht_tot),                             "#7BBF6A", "Horas normais"),
        (str(dias_he),                                     "#FFB347", "Dias c/ HE"),
    ]
    parts = ['<div class="ep-kpi-grid">']
    for val, cor, lbl in kpis:
        parts.append(
            f'<div class="ep-kpi"><div class="kv" style="color:{cor}">{val}</div>'
            f'<div class="kl">{lbl}</div></div>'
        )
    parts.append('</div>')
    st.markdown("".join(parts), unsafe_allow_html=True)

    # Índice dia → registro
    idx = {r["_dt"]: r for _, r in rows.iterrows()}
    ENT_REF = 7 * 60 + 57

    html = [
        '<div class="ep-mon-wrap"><table class="ep-mon-tbl">',
        '<thead><tr>',
        '<th class="left">Data</th>',
        '<th>Dia</th>',
        '<th>↑ Entrada</th>',
        '<th>↓ Saída Alm.</th>',
        '<th>↑ Volta Alm.</th>',
        '<th>↓ Saída</th>',
        '<th>Intervalo</th>',
        '<th>H. Normais</th>',
        '<th style="color:#F7B731">HE 50%</th>',
        '<th style="color:#F7B731">HE 100%</th>',
        '<th class="left">Motivo / Justif. HE</th>',
        '</tr></thead><tbody>',
    ]

    for d in range(1, n_dias + 1):
        dt    = pd.Timestamp(ano, mes, d)
        wk    = dt.weekday()
        day_n = _DAY_ABBR[wk]
        rec   = idx.get(dt)

        row_cls = []
        if wk >= 5:
            row_cls.append("weekend")
        if dt == hoje:
            row_cls.append("today")

        # Determina valores
        if rec is None:
            if wk >= 5:
                cells = ["—", "—", "—", "—", "—", "—", "—", "—", "—"]
                he_day = False
            else:
                cells = [
                    '<span class="ep-mon-abs">sem reg.</span>',
                    "—", "—", "—", "—", "—", "—", "—", "",
                ]
                he_day = False
        else:
            ent   = rec.get("entrada","")
            sa    = rec.get("saida_almoco","")
            va    = rec.get("volta_almoco","")
            sai   = rec.get("saida","")
            intv  = rec.get("intervalo","")
            ht    = rec.get("ht","")
            he50  = rec.get("he_50","")
            he100 = rec.get("he_100","")
            mot   = rec.get("motivo","")
            just  = rec.get("justificativa_he","")
            he_total_d = _he_total_min(he50, he100)
            he_day = he_total_d > 0

            if he_day:
                row_cls.append("he-day")

            # Cor entrada
            ent_m = _hhmm_to_min(ent)
            if not ent and mot:
                ent_html = f'<span class="ep-mon-abs">{_esc(mot[:6])}</span>'
            elif ent_m and ent_m < ENT_REF - 15:
                ent_html = f'<span class="ep-mon-ent-early">{ent}</span>'
            elif ent_m and ent_m > ENT_REF + 15:
                ent_html = f'<span class="ep-mon-ent-late">{ent}</span>'
            else:
                ent_html = f'<span class="ep-mon-ent-norm">{ent or "—"}</span>'

            he50_html  = f'<span class="ep-mon-he">{he50}</span>'  if he50  else '<span style="color:#3a4a5e">—</span>'
            he100_html = f'<span class="ep-mon-he">{he100}</span>' if he100 else '<span style="color:#3a4a5e">—</span>'

            cells = [
                ent_html,
                sa   or "—",
                va   or "—",
                sai  or "—",
                intv or "—",
                ht   or "—",
                he50_html,
                he100_html,
                (f'<span class="ep-mon-mot">{_esc(mot[:25])}</span>' if mot else "") +
                (f'<br><span style="color:#A29BFE;font-size:.58rem">↳ {_esc(just[:35])}</span>' if just else ""),
            ]

        row_class = ' class="' + " ".join(row_cls) + '"' if row_cls else ""
        html.append(f'<tr{row_class}>')
        html.append(f'<td class="left" style="font-weight:500;color:#BFCF99">{dt.strftime("%d/%m")}</td>')
        html.append(f'<td style="color:#8FA882">{day_n}</td>')
        for c in cells:
            html.append(f'<td>{c}</td>')
        html.append('</tr>')

    # Linha de totais
    html.append(
        '<tr class="ep-mon-total">'
        '<td class="left" colspan="2">TOTAIS</td>'
        f'<td colspan="4"></td>'
        f'<td>{_min_to_hhmm(ht_tot)}</td>'
        f'<td><span class="ep-mon-he">{_min_to_hhmm(he50_tot)}</span></td>'
        f'<td><span class="ep-mon-he">{_min_to_hhmm(he100_tot)}</span></td>'
        f'<td></td></tr>'
    )

    html.append('</tbody></table></div>')
    st.markdown("".join(html), unsafe_allow_html=True)


def _render_aba_colaboradores(df: pd.DataFrame):
    """Lista de todos os colaboradores com tabela mensal ao selecionar."""
    st.markdown(_CSS_COLAB, unsafe_allow_html=True)

    pessoas = sorted(df["nome"].dropna().unique())
    n_total = len(pessoas)

    # Barra de busca + info
    col_busca, col_info = st.columns([3, 1])
    with col_busca:
        filtro = st.text_input(
            "Buscar", key="ep_colab_filtro",
            placeholder=f"🔍  Buscar entre {n_total} colaboradores…",
            label_visibility="collapsed",
        )
    with col_info:
        st.caption(f"{n_total} colaboradores no período")

    # Filtra
    if filtro.strip():
        fl = filtro.strip().lower()
        pessoas_vis = [p for p in pessoas if fl in p.lower()]
    else:
        pessoas_vis = pessoas

    # Estado de seleção
    sel = st.session_state.get("ep_colab_sel")

    # Grade de nomes por grupo (separados visualmente)
    grupos_ordem = ["SST","Pavimento","Topografia","Escritório","Outros"]
    for grupo_nome in grupos_ordem:
        membros = [p for p in pessoas_vis
                   if df[df["nome"]==p]["grupo"].iloc[0] == grupo_nome
                   if len(df[df["nome"]==p]) > 0]
        if not membros:
            continue
        cor_g = _COR_GRUPO.get(grupo_nome, "#8FA882")
        st.markdown(
            f'<div style="font-size:.62rem;font-weight:700;color:{cor_g};'
            f'letter-spacing:.06em;text-transform:uppercase;margin:10px 0 4px 0">'
            f'{grupo_nome} ({len(membros)})</div>',
            unsafe_allow_html=True,
        )
        # Botões em colunas de 4
        cols = st.columns(4)
        for i, pessoa in enumerate(membros):
            is_sel = (pessoa == sel)
            with cols[i % 4]:
                btn_type = "primary" if is_sel else "secondary"
                if st.button(
                    pessoa,
                    key=f"ep_cb_{pessoa.replace(' ','_')[:30]}",
                    use_container_width=True,
                    type=btn_type,
                ):
                    if sel == pessoa:
                        st.session_state.pop("ep_colab_sel", None)
                    else:
                        st.session_state["ep_colab_sel"] = pessoa
                    st.rerun()

    if not pessoas_vis:
        st.info("Nenhum colaborador encontrado para esse filtro.")

    # Tabela mensal do colaborador selecionado
    if sel and sel in df["nome"].values:
        st.markdown('<div class="ep-hr"></div>', unsafe_allow_html=True)
        rows_sel = df[df["nome"] == sel].sort_values("_dt")
        _render_tabela_mensal_colab(sel, rows_sel)


# ─── Aba principal ────────────────────────────────────────────────────────────

def _aba_espelho_ponto():
    try:
        st.image("Imagens/AE - Logo Hor Principal_2.png", width=220)
    except:
        pass

    st.markdown(_CSS, unsafe_allow_html=True)

    # Cabeçalho + botão
    col_hdr, col_btn = st.columns([6, 1])
    with col_hdr:
        st.markdown(
            '<div class="ep-header"><h2>⏱ Espelho de Ponto</h2>'
            '<p>ECO CERRADO · ECO MINAS · ECO RIOMINAS — Jornada mensal</p></div>',
            unsafe_allow_html=True,
        )
    with col_btn:
        st.markdown("<div style='padding-top:10px'>", unsafe_allow_html=True)
        atualizar = render_atualizar_btn("↺ Atualizar", "espelho_ponto", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if atualizar:
        st.session_state.pop("ep_auto_sync_tried", None)
        _iniciar_sync()
        st.rerun()

    # Mostra spinner enquanto bg task roda (poller em app.py consome o resultado)
    from _eco_bg_loader import is_loading
    if is_loading("espelho_ponto"):
        st.info("⏳ Buscando dados do PontoMais… aguarde (pode levar até 2 min)")
        return

    # Carrega dados
    df, ts = _carregar_dados()

    # Mostra upload se sync falhou
    if st.session_state.get("ep_show_upload"):
        _render_upload()
        if df is None or df.empty:
            return

    # Auto-sync se sem dados ou cache antigo (em segundo plano)
    if not st.session_state.get("ep_auto_sync_tried") and not st.session_state.get("ep_show_upload"):
        if df is None or df.empty or (ts and ts != date.today().isoformat()):
            st.session_state["ep_auto_sync_tried"] = True
            _iniciar_sync()
            st.rerun()

    if df is None or df.empty:
        _render_upload()
        return

    # ── Filtrar apenas colaboradores ECO (presentes no eco_checklist.json) ──
    if "is_eco" in df.columns:
        n_total    = df["nome"].nunique()
        df_eco     = df[df["is_eco"]]
        n_excluidos = n_total - df_eco["nome"].nunique()
        if n_excluidos > 0:
            nomes_ext = sorted(
                df[~df["is_eco"]]["nome"].dropna().unique().tolist()
            )
            with st.expander(
                f"⚠️ {n_excluidos} colaborador(es) externo(s) excluído(s) das análises",
                expanded=False,
            ):
                st.caption(
                    "Estes nomes constam no PontoMais mas **não** estão no "
                    "cadastro ECO (eco_checklist.json). Podem ser de outros contratos."
                )
                for nm in nomes_ext:
                    st.markdown(f"- {nm}")
        df = df_eco

    if df.empty:
        st.warning("Nenhum colaborador ECO encontrado nos dados do PontoMais.")
        return

    # ── Tabs por Grupo + Colaboradores ──────────────────────────────────
    grupos_presentes = ["Todos"] + sorted(df["grupo"].unique().tolist()) if "grupo" in df.columns else ["Todos"]
    tabs_order = [g for g in _GRUPOS if g in grupos_presentes]
    extras     = [g for g in grupos_presentes if g not in tabs_order]
    tabs_order += extras
    tabs_order.append("👥 Colaboradores")

    tabs = st.tabs(tabs_order)

    for tab_obj, grupo_nome in zip(tabs, tabs_order):
        with tab_obj:
            # ── Aba especial: lista de colaboradores ─────────────────────────
            if grupo_nome == "👥 Colaboradores":
                _render_aba_colaboradores(df)
                continue

            if grupo_nome == "Todos":
                df_g = df
            else:
                df_g = df[df["grupo"] == grupo_nome] if "grupo" in df.columns else df

            if df_g.empty:
                st.info(f"Sem colaboradores no grupo {grupo_nome}.")
                continue

            # KPIs do grupo
            _render_kpis(df_g, ts)
            st.markdown('<div class="ep-hr"></div>', unsafe_allow_html=True)

            # Sub-tabs de análise
            sub_resumo, sub_rdpp, sub_entrada, sub_almoco, sub_he = st.tabs([
                "📋 Resumo", "📅 Resumo Diário por Profissional",
                "🕐 Entrada / Saída", "🍽 Almoço", "⚡ Horas Extras"
            ])

            with sub_resumo:
                st.caption(
                    "Entrada média · Saída média · HE total do mês por colaborador. "
                    "Passe o mouse sobre cada valor para ver o detalhamento diário."
                )
                _render_tabela_resumo(df_g)

            with sub_rdpp:
                st.caption(
                    "Cada linha = um dia útil por colaborador. "
                    "Passe o mouse sobre Entrada, Saída ou ⚡ HE para ver detalhes e justificativas."
                )
                _render_resumo_diario_profissional(df_g)

            with sub_entrada:
                st.caption("Célula = hora de entrada. 🔵 Antecipado  ·  🔴 Atrasado  ·  Média no final.")
                _render_tabela_horarios(df_g)

            with sub_almoco:
                st.caption("Duração do almoço (Saída – Volta). 🔵 < 50min  ·  🔴 > 80min")
                _render_tabela_almoco(df_g)

            with sub_he:
                st.caption("Horas extras por dia (50% + 100%). Totais por colaborador no final.")
                _render_tabela_he(df_g)

    # Download
    st.markdown('<div class="ep-hr"></div>', unsafe_allow_html=True)
    st.download_button(
        "⬇ Baixar dados processados (Excel)",
        data=df.drop(columns=["_dt","_weekday"], errors="ignore").to_csv(index=False).encode(),
        file_name=f"espelho_ponto_eco_{date.today().strftime('%Y%m')}.csv",
        mime="text/csv",
    )
