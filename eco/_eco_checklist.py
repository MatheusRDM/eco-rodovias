
"""
_eco_checklist.py — checklist tab for ECO Rodovias.
Layout padronizado baseado no modelo ENSAIOS.
"""
import sys, os, json, time
from datetime import datetime, date
from collections import defaultdict

_PAGES_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR  = os.path.dirname(_PAGES_DIR)
if _PAGES_DIR not in sys.path: sys.path.insert(0, _PAGES_DIR)
if _ROOT_DIR  not in sys.path: sys.path.insert(0, _ROOT_DIR)

import streamlit as st
from _eco_shared import (
    COR_TEXT, COR_MUTED, _BASE_DIR, _CACHE_DIR, _Y_BASE, _IS_CLOUD,
    AEVIAS_BASE_URL,
)
from _eco_funcoes import cargo_para_grupo, header_grupo, ORDEM_GRUPOS, GRUPOS

# =============================================================================
# CARREGAMENTO E UTILITÁRIOS
# =============================================================================

@st.cache_data(ttl=3600, show_spinner=False)
def _carregar_checklist_cache() -> dict:
    p = os.path.join(_CACHE_DIR, "eco_checklist.json")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f: return json.load(f)
    return {}

@st.cache_data(ttl=60, show_spinner=False)
def _carregar_details_ck() -> dict:
    p = os.path.join(_CACHE_DIR, "ensaios_details.json")
    if not os.path.exists(p): return {}
    try:
        with open(p, encoding="utf-8") as f: return json.load(f)
    except Exception: return {}

import unicodedata as _ucd
def _norm(s: str) -> str:
    s = _ucd.normalize("NFD", s.lower().strip())
    return "".join(c for c in s if _ucd.category(c) != "Mn")

import html as _html_mod
def _esc(s: str) -> str: return _html_mod.escape(str(s))

_FUNCOES_ISENTAS_NORM = {"assistente de engenharia", "encarregado sala tecnica", "encarregado de sala tecnica", "desenhista", "engenheiro sala tecnica", "engenheiro de sala tecnica"}
def _isento_checklist(funcao: str) -> bool:
    f = _norm(funcao)
    return f in _FUNCOES_ISENTAS_NORM or "auxiliar" in f

# =============================================================================
# CSS PADRÃO (MODELO ENSAIOS)
# =============================================================================

_CSS_CALENDARIO = """
<style>
.do-wrap-scroll{overflow-x:auto;-webkit-overflow-scrolling:touch;width:100%;margin-bottom:20px}
.do-table{border-collapse:collapse;font-size:.68rem;font-family:Inter,sans-serif;width:100%;min-width:700px}
.do-table th{
  background:rgba(86,110,61,.2);color:#BFCF99;padding:6px 4px;
  text-align:center;font-weight:600;border:1px solid rgba(86,110,61,.15);
  font-size:.6rem;white-space:nowrap;text-transform:uppercase
}
.do-table td{
  padding:5px 4px;border:1px solid rgba(255,255,255,.05);
  text-align:center;white-space:nowrap;font-size:0.65rem;
  transition: background 0.15s;
}
.do-table td.do-nome{
  text-align:left;font-weight:600;color:#E8EFD8;padding-left:12px;
  min-width:160px;max-width:220px;white-space:normal;
  vertical-align:middle;line-height:1.2;
  border-right: 2px solid rgba(86,110,61,0.2) !important;
  background: rgba(13, 27, 42, 0.4) !important;
}
.do-nome-cargo{font-size:.55rem;color:#8FA882;font-weight:400;
  display:block;margin-top:2px;white-space:nowrap;
  overflow:hidden;text-overflow:ellipsis;max-width:210px}

/* Status e Hover */
.do-ok{background:rgba(60,180,75,.2);color:#3cb44b;font-weight:700}
.do-pend{background:rgba(230,25,75,.2);color:#ff5577;font-weight:700}
.do-rep{background:rgba(230,25,75,.3);color:#e6194b;font-weight:700}
.do-elb{background:rgba(76,201,240,.2);color:#4CC9F0;font-weight:700}
.do-vazio{color:#3a4a5e;background:transparent}
.do-hj{outline:2px solid #F7B731 !important;outline-offset:-1px}

.do-table td:not(.do-nome):hover {
    background: rgba(123, 191, 106, 0.15) !important;
    cursor: pointer;
}

/* Tooltip Rico */
.do-tip-host{position:relative;display:block;width:100%;height:100%}
.do-tip-host a{color:inherit;text-decoration:none;display:block}
.do-tip-box{
  display:none;position:absolute;bottom:calc(100% + 8px);left:50%;
  transform:translateX(-50%);z-index:9999;
  background:#0D1B2A;border:1px solid rgba(123,191,106,.3);
  border-radius:8px;padding:12px;min-width:240px;max-width:340px;
  box-shadow:0 8px 32px rgba(0,0,0,.6);pointer-events:none;
  text-align:left;white-space:normal;font-weight:400
}
.do-tip-host:hover .do-tip-box{display:block}
.do-tip-date{font-size:.65rem;color:#8FA882;margin-bottom:2px}
.do-tip-status{font-size:.75rem;font-weight:700;margin-bottom:4px}
.do-tip-val{font-size:.68rem;color:#C8D8A8;line-height:1.45}
.do-tip-sep{display:block;height:1px;background:rgba(255,255,255,.08);margin:6px 0}
.do-tip-lbl{font-size:.54rem;text-transform:uppercase;letter-spacing:.08em;color:#6b7f8d;margin-bottom:2px}
.do-tip-jornada{font-size:.68rem;color:#F7B731;margin-top:6px;font-weight:700}
</style>
"""

_DAY_ABBR = {0:"SEG",1:"TER",2:"QUA",3:"QUI",4:"SEX",5:"SÁB",6:"DOM"}
_BASE44_URL = AEVIAS_BASE_URL

def _status_badge_class(v):
    if v is None or str(v).strip() == "": return "do-vazio", "—"
    vu = str(v).upper().strip()
    if vu == "OK": return "do-ok", "OK"
    if vu in ("COBRAR", "COBRE"): return "do-pend", "COB"
    if vu in ("N/E", "NE"): return "do-vazio", "—"
    if vu in ("ELAB.", "ELAB"): return "do-elb", "ELB"
    return "do-vazio", v[:3] if v else "—"

def _renderizar_calendario(people: list[dict], mes_ref: str, aevias_por_grp: dict | None = None):
    """View padronizada com Hover, Clique e Relatórios."""
    if not people: return
    today = date.today(); today_str = today.strftime("%Y-%m-%d")
    campo_people = [p for p in people if not _isento_checklist(p.get("funcao",""))]
    datas_mes = sorted({d for p in campo_people for d in p.get("dias", {}).keys() if d and d <= today_str})
    if not datas_mes: return

    # Lookup AEVIAS
    _av_flat = {}
    if aevias_por_grp:
        for grp_recs in aevias_por_grp.values():
            for prof, recs in grp_recs.items():
                k = _norm(prof)
                if k not in _av_flat: _av_flat[k] = {}
                for r in recs:
                    ds = r.get("_dstr", "")
                    if ds: _av_flat[k].setdefault(ds, []).append(r)

    def _av_match_name(nome: str) -> dict:
        nk = _norm(nome)
        if nk in _av_flat: return _av_flat[nk]
        tokens = set(nk.split()); best_key, best_score = None, 0
        for k in _av_flat:
            score = len(tokens & set(k.split()))
            if score > best_score and score >= min(2, len(tokens)): best_score, best_key = score, k
        return _av_flat[best_key] if best_key else {}

    _det_cache = _carregar_details_ck()

    def _tip_html_cal(r: dict) -> str:
        sl = str(r.get("status", "")).lower()
        sc = "s-ok" if "aprovado" in sl else "s-pend" if "pendente" in sl else "s-rep" if "reprovado" in sl else "s-ok"
        parts = [f'<div class="do-tip-date">{_esc(r.get("data",""))}</div>',
                 f'<div class="do-tip-status {sc}">{_esc(r.get("status","—"))}</div>',
                 f'<div class="do-tip-val">{_esc(r.get("obra",""))} · {_esc(r.get("local",""))}</div>']
        det = _det_cache.get(r.get("reportUrl", ""), {})
        if det.get("atividades"): parts.append(f'<span class="do-tip-sep"></span><div class="do-tip-lbl">Atividades</div><div class="do-tip-val">{_esc(det["atividades"][:180])}</div>')
        if det.get("jornada"): parts.append(f'<div class="do-tip-jornada">⏱ {_esc(det["jornada"])}</div>')
        return "".join(parts)

    st.markdown(_CSS_CALENDARIO, unsafe_allow_html=True)
    por_grupo = defaultdict(list)
    for p in campo_people: por_grupo[cargo_para_grupo(p.get("funcao", ""))].append(p)

    for grupo in [g for g in ORDEM_GRUPOS if por_grupo.get(g)]:
        st.markdown(header_grupo(grupo), unsafe_allow_html=True)
        people_grupo = sorted(por_grupo[grupo], key=lambda x: x["colaborador"])

        html = ['<div class="do-wrap-scroll"><table class="do-table"><thead><tr><th>Profissional</th>']
        for d in datas_mes:
            dt = datetime.strptime(d, "%Y-%m-%d"); is_hj = (d == today_str)
            html.append(f'<th style="{"color:#F7B731;font-weight:700" if is_hj else ""}">{("HOJE" if is_hj else f"{dt.day:02d}")}<br>{_DAY_ABBR[dt.weekday()]}</th>')
        html.append('<th>Total</th></tr></thead><tbody>')

        for p in people_grupo:
            dias = p.get("dias", {}); func = p.get("funcao", ""); av_dias = _av_match_name(p["colaborador"])
            html.append(f'<tr><td class="do-nome">{p["colaborador"]}<span class="do-nome-cargo">{func}</span></td>')
            for d in datas_mes:
                hj_cls = " do-hj" if d == today_str else ""
                cls, txt = _status_badge_class(dias.get(d))
                av_recs = [r for r in av_dias.get(d, []) if r.get("reportUrl")]
                if av_recs:
                    tip = f'<div class="do-tip-box">{_tip_html_cal(av_recs[0])}</div>'
                    if len(av_recs) == 1:
                        inner = f'<a href="{_BASE44_URL + av_recs[0]["reportUrl"]}" target="_blank">{txt}</a>{tip}'
                    else:
                        js = "[" + ",".join(f'"{_BASE44_URL+r["reportUrl"]}"' for r in av_recs) + "]"
                        inner = f'<span onclick="(function(){{var us={js};us.forEach(function(u){{window.open(u,\'_blank\');}})}})()" style="cursor:pointer">{txt}</span>{tip}'
                    html.append(f'<td class="{cls}{hj_cls}"><span class="do-tip-host">{inner}</span></td>')
                else: html.append(f'<td class="{cls}{hj_cls}">{txt}</td>')
            html.append(f'<td style="color:#8FA882;font-weight:600">{sum(1 for v in dias.values() if str(v).upper().strip()=="OK")}</td></tr>')
        
        html.append('</tbody></table></div>')
        st.markdown("".join(html), unsafe_allow_html=True)

        # Relatórios abaixo da tabela (Padrão Ensaios)
        if aevias_por_grp and aevias_por_grp.get(grupo):
            grp_data = aevias_por_grp[grupo]
            with st.expander(f"Relatórios — {GRUPOS[grupo]['label']} ({len(grp_data)} pessoas)", expanded=False):
                for prof in sorted(grp_data.keys()):
                    st.markdown(f'<div style="font-weight:700;color:#E8EFD8;font-size:.9rem;margin:10px 0 4px 0">{prof}</div>', unsafe_allow_html=True)
                    lines = []
                    for r in sorted(grp_data[prof], key=lambda x: x.get("_dstr", "")):
                        sl = str(r.get("status", "")).lower()
                        clr = "#FF6B6B" if "reprovado" in sl or "pendente" in sl else "#3cb44b"
                        slbl = "Reprovado" if "reprovado" in sl else ("Pendente" if "pendente" in sl else "Aprovado")
                        lines.append(f'<a href="{_BASE44_URL + r.get("reportUrl", "")}" target="_blank" style="display:block;color:{clr};font-size:.82rem;padding:3px 0;text-decoration:none;font-family:Inter,sans-serif;">{r.get("data", "")[:5]} — {r.get("obra", "—")} ({slbl})</a>')
                    st.markdown("".join(lines), unsafe_allow_html=True)
                    st.markdown("<hr style='margin:8px 0;border:none;border-top:1px solid rgba(255,255,255,.07)'>", unsafe_allow_html=True)

# =============================================================================
# MAIN ABA CHECKLIST
# =============================================================================

def _aba_checklist():
    try:
        st.image("Imagens/AE - Logo Hor Principal_2.png", width=220)
    except:
        pass

    st.markdown('<div class="rs-header"><h2>Controle de Checklist APP</h2><p>Acompanhamento diário de envio de checklists via aplicativo</p></div>', unsafe_allow_html=True)
    
    # Carga de dados (Checklist + Ensaios para links)
    cache = _carregar_checklist_cache(); meds = sorted(cache.keys(), reverse=True)
    if not meds:
        st.info("Nenhum dado de checklist encontrado no cache."); return
    
    med_sel = st.selectbox("Medição:", meds, key="ck_med_sel")
    data_med = cache[med_sel]; all_people = []
    for sheet_people in data_med.get("sheets", {}).values(): all_people.extend(sheet_people)
    
    # Carrega ensaios para cruzar links
    from _eco_resumo import _carregar_ensaios_resumo
    ensaios_raw = _carregar_ensaios_resumo()
    aevias_por_grp = defaultdict(lambda: defaultdict(list))
    for e in ensaios_raw:
        if "checklist" in str(e.get("tipo","")).lower():
            prof = (e.get("lab") or e.get("profissional") or "").strip()
            try: e["_dstr"] = datetime.strptime(e["data"].split()[0], "%d/%m/%Y").strftime("%Y-%m-%d")
            except: e["_dstr"] = ""
            if prof: aevias_por_grp[cargo_para_grupo(e.get("funcao",""))][prof].append(e)

    _renderizar_calendario(all_people, med_sel, aevias_por_grp=aevias_por_grp)
