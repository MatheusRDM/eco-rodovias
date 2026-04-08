
"""
_eco_diario.py — Aba "Diário de Obra" para ECO Rodovias.
Layout padronizado baseado no modelo ENSAIOS.
"""
import os, json, sys
from datetime import datetime, date
from collections import defaultdict

_PAGES_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR  = os.path.dirname(_PAGES_DIR)
if _PAGES_DIR not in sys.path: sys.path.insert(0, _PAGES_DIR)
if _ROOT_DIR  not in sys.path: sys.path.insert(0, _ROOT_DIR)

import streamlit as st
from _eco_shared import _CACHE_DIR, AEVIAS_BASE_URL
from _eco_funcoes import cargo_para_grupo, header_grupo, ORDEM_GRUPOS, GRUPOS

_ENSAIOS_PATH = os.path.join(_CACHE_DIR, "ensaios_aevias.json")
_BASE44_URL   = AEVIAS_BASE_URL
_DATA_MIN     = date(2026, 3, 1)
_DAY_ABBR     = {0:"SEG",1:"TER",2:"QUA",3:"QUI",4:"SEX",5:"SÁB",6:"DOM"}

# =============================================================================
# CSS PADRÃO (MODELO ENSAIOS)
# =============================================================================

_CSS_TABELA = """
<style>
.do-wrap-scroll{overflow-x:auto;-webkit-overflow-scrolling:touch;width:100%;margin-bottom:20px}
.do-table{border-collapse:collapse;font-size:.68rem;font-family:Inter,sans-serif;width:100%;min-width:700px}
.do-table th{
  background:rgba(86,110,61,.2);color:#BFCF99;padding:6px 4px;
  text-align:center;font-weight:600;border:1px solid rgba(86,110,61,.15);
  font-size:.6rem;white-space:nowrap;text-transform:uppercase
}
.do-table td{
  padding:5px 3px;border:1px solid rgba(255,255,255,.05);
  text-align:center;white-space:nowrap;font-size:0.65rem;
  transition: background 0.15s;
}
.do-table td.do-nome{
  text-align:left;font-weight:600;color:#E8EFD8;padding-left:12px;
  min-width:140px;max-width:200px;white-space:normal;
  vertical-align:middle;line-height:1.2;
  border-right: 2px solid rgba(86,110,61,0.2) !important;
  background: rgba(13, 27, 42, 0.4) !important;
}
.do-nome-cargo{font-size:.55rem;color:#8FA882;font-weight:400;
  display:block;margin-top:1px;white-space:nowrap;
  overflow:hidden;text-overflow:ellipsis;max-width:210px}

/* Status e Hover */
.do-ok{background:rgba(60,180,75,.2);color:#3cb44b;font-weight:700}
.do-pend{background:rgba(230,25,75,.2);color:#ff5577;font-weight:700}
.do-rep{background:rgba(230,25,75,.3);color:#e6194b;font-weight:700}
.do-elb{background:rgba(76,201,240,.2);color:#4CC9F0;font-weight:700}
.do-vazio{color:#3a4a5e;background:transparent}
.do-hj{outline:2px solid #F7B731 !important;outline-offset:-1px}

/* INTERATIVIDADE CRÍTICA */
.do-table td:not(.do-nome):hover {
    background: rgba(123, 191, 106, 0.15) !important;
    filter: brightness(1.2);
    cursor: pointer;
}

/* Tooltip Rico (Padrão Ensaios) */
.do-tip-host{position:relative;display:block;width:100%;height:100%}
.do-tip-host a{color:inherit;text-decoration:none;display:block;width:100%;height:100%}
.do-tip-box{
  display:none;position:absolute;bottom:calc(100% + 8px);left:50%;
  transform:translateX(-50%);z-index:9999;
  background:#0D1B2A;border:1px solid rgba(123,191,106,.3);
  border-radius:8px;padding:12px;min-width:240px;max-width:340px;
  box-shadow:0 8px 32px rgba(0,0,0,.6);pointer-events:none;
  text-align:left;white-space:normal;font-weight:400;line-height:1.4
}
.do-tip-host:hover .do-tip-box{display:block}
.do-tip-date{font-size:.65rem;color:#8FA882;margin-bottom:2px}
.do-tip-status{font-size:.75rem;font-weight:700;margin-bottom:4px}
.do-tip-status.s-ok{color:#3cb44b}
.do-tip-status.s-pend{color:#F7B731}
.do-tip-status.s-rep{color:#FF6B6B}
.do-tip-val{font-size:.68rem;color:#C8D8A8}
.do-tip-sep{display:block;height:1px;background:rgba(255,255,255,.08);margin:8px 0}
.do-tip-lbl{font-size:.54rem;text-transform:uppercase;letter-spacing:.08em;color:#6b7f8d;margin-bottom:2px}
</style>
"""

# =============================================================================
# UTILITÁRIOS E DADOS
# =============================================================================

@st.cache_data(ttl=60, show_spinner=False)
def _carregar_diarios() -> list:
    if not os.path.exists(_ENSAIOS_PATH): return []
    with open(_ENSAIOS_PATH, encoding="utf-8") as f:
        dados = json.load(f)
    recs = dados if isinstance(dados, list) else dados.get("registros", dados.get("data", []))
    return [r for r in recs if r.get("tipo", "") == "Diário de Obra"]

def _parse_data(s: str) -> date | None:
    s = (s or "").split()[0]  # remove parte de hora se vier "DD/MM/YYYY HH:MM"
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try: return datetime.strptime(s, fmt).date()
        except: pass
    return None

def _status_badge_class(s: str):
    s = (s or "").lower()
    if "aprovado" in s: return "do-ok", "OK"
    if "reprovado" in s: return "do-rep", "REP"
    return "do-pend", "PND"

def _lookup_funcao(lab: str, checklist_cache: dict) -> str:
    nome_norm = lab.strip().lower()
    for med in checklist_cache.values():
        for pessoas in med.get("sheets", {}).values():
            for p in pessoas:
                p_nome = p.get("colaborador", "").strip().lower()
                if p_nome in nome_norm or nome_norm in p_nome: return p.get("funcao", "")
    return ""

def _grupo_por_obra(obra: str) -> str:
    o = (obra or "").lower()
    if "sst" in o or "segurança" in o or "seguranca" in o: return "SST"
    if "topografia" in o: return "Topografia"
    if "escritório" in o or "escritorio" in o: return "Escritório"
    return "Pavimento"

@st.cache_data(ttl=3600, show_spinner=False)
def _checklist_cache_do() -> dict:
    p = os.path.join(_CACHE_DIR, "eco_checklist.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}

def _esc(s: str) -> str:
    import html as _html_mod
    return _html_mod.escape(str(s))

def _tip_html_do(r: dict) -> str:
    """Gera o conteúdo HTML rico para o tooltip do Diário."""
    sl = str(r.get("status", "")).lower()
    sc = "s-ok" if "aprovado" in sl else "s-pend" if "pendente" in sl else "s-rep" if "reprovado" in sl else "s-ok"
    return (f'<div class="do-tip-date">{_esc(r.get("data",""))}</div>'
            f'<div class="do-tip-status {sc}">{_esc(r.get("status","—"))}</div>'
            f'<div class="do-tip-val">{_esc(r.get("obra",""))} · {_esc(r.get("empreiteira",""))}</div>'
            f'<span class="do-tip-sep"></span><div class="do-tip-lbl">Localização</div>'
            f'<div class="do-tip-val">{_esc(r.get("local",""))}</div>')

def _cell_interativa(cls: str, label: str, recs: list, hj_cls: str) -> str:
    """Monta a célula <td> com suporte a Hover Rico e Clique (abertura única ou múltipla)."""
    if not recs:
        return f'<td class="do-vazio{hj_cls}">—</td>'
    
    tip = f'<div class="do-tip-box">{_tip_html_do(recs[0])}</div>'
    
    if len(recs) == 1:
        # Clique único direto
        url = _BASE44_URL + recs[0].get("reportUrl", "")
        inner = f'<a href="{url}" target="_blank">{label}{tip}</a>'
    else:
        # Clique múltiplo via JavaScript
        js_urls = "[" + ",".join(f'"{_BASE44_URL + r.get("reportUrl","")}"' for r in recs if r.get("reportUrl")) + "]"
        onclick = f"(function(){{var us={js_urls};us.forEach(function(u){{window.open(u,'_blank');}})}})()"
        inner = f'<div onclick="{onclick}" style="width:100%;height:100%">{label}{tip}</div>'
        
    return f'<td class="{cls}{hj_cls}"><span class="do-tip-host">{inner}</span></td>'

# =============================================================================
# VIEW PRINCIPAL
# =============================================================================

def _aba_diario():
    try:
        st.image("Imagens/AE - Logo Hor Principal_2.png", width=220)
    except:
        pass

    diarios = _carregar_diarios()
    if not diarios:
        st.info("Nenhum Diário de Obra encontrado."); return

    chk_cache = _checklist_cache_do()
    today = date.today(); today_str = today.strftime("%Y-%m-%d")
    
    # Enriquece e Filtra
    for r in diarios:
        r["_data"] = _parse_data(r.get("data", ""))
        r["_dstr"] = r["_data"].strftime("%Y-%m-%d") if r["_data"] else ""
        r["_funcao"] = _lookup_funcao(r.get("lab", ""), chk_cache)
        r["_grupo"] = cargo_para_grupo(r["_funcao"]) if r["_funcao"] else _grupo_por_obra(r.get("obra", ""))
    
    diarios = [r for r in diarios if r["_data"] and r["_data"] >= _DATA_MIN and r["_data"] <= today]
    if not diarios:
        st.info("Sem Diários a partir de 01/03/2026."); return

    # Filtro Mês
    meses_disp = sorted({(r["_data"].year, r["_data"].month) for r in diarios}, reverse=True)
    _PT = {1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"}
    opcoes = {f"{_PT[m]}/{y}": (y, m) for y, m in meses_disp}
    c_mes, _ = st.columns([2, 4])
    with c_mes: mes_lbl = st.selectbox("Mes:", list(opcoes.keys()), key="do_mes_sel")
    ano_sel, mes_sel = opcoes[mes_lbl]

    diarios_mes = [r for r in diarios if r["_data"].year == ano_sel and r["_data"].month == mes_sel]
    datas_mes = sorted({r["_dstr"] for r in diarios_mes})

    # Agrupa por profissional
    por_lab = defaultdict(lambda: {"registros": defaultdict(list), "funcao": "", "grupo": "Pavimento"})
    for r in diarios_mes:
        lab = r.get("lab", "—")
        por_lab[lab]["registros"][r["_dstr"]].append(r)
        if r["_funcao"]: por_lab[lab]["funcao"] = r["_funcao"]
        por_lab[lab]["grupo"] = r["_grupo"]

    # KPIs
    aprovados = sum(1 for r in diarios_mes if "aprovado" in str(r.get("status","")).lower())
    c1, c2, c3, _ = st.columns([1, 1, 1, 3])
    c1.metric("Total no mes", len(diarios_mes))
    c2.metric("Aprovados", aprovados)
    c3.metric("Pendentes", len(diarios_mes) - aprovados)

    st.markdown(_CSS_TABELA, unsafe_allow_html=True)
    por_grupo = defaultdict(list)
    for lab, info in por_lab.items(): por_grupo[info["grupo"]].append((lab, info))

    for grupo in [g for g in ORDEM_GRUPOS if por_grupo.get(g)]:
        st.markdown(header_grupo(grupo), unsafe_allow_html=True)
        labs_grupo = sorted(por_grupo[grupo], key=lambda x: x[0])

        html = ['<div class="do-wrap-scroll"><table class="do-table"><thead><tr><th>Profissional</th>']
        for d in datas_mes:
            dt = datetime.strptime(d, "%Y-%m-%d"); is_hj = (d == today_str)
            html.append(f'<th style="{"color:#F7B731;font-weight:700" if is_hj else ""}">{("HOJE" if is_hj else f"{dt.day:02d}")}<br>{_DAY_ABBR[dt.weekday()]}</th>')
        html.append('<th>Total</th></tr></thead><tbody>')

        for lab, info in labs_grupo:
            regs_dia = info["registros"]; total_lab = sum(len(v) for v in regs_dia.values())
            cargo_html = f'<span class="do-nome-cargo">{info["funcao"]}</span>' if info["funcao"] else ""
            html.append(f'<tr><td class="do-nome">{lab}{cargo_html}</td>')
            for d in datas_mes:
                is_hj = (d == today_str); hj_cls = " do-hj" if is_hj else ""; recs = regs_dia.get(d, [])
                
                # Determina status visual
                if not recs:
                    html.append(_cell_interativa("do-vazio", "—", [], hj_cls))
                else:
                    st_raw = "aprovado" if all("aprovado" in str(r.get("status","")).lower() for r in recs) else "pendente"
                    if any("reprovado" in str(r.get("status","")).lower() for r in recs): st_raw = "reprovado"
                    cls, txt = _status_badge_class(st_raw)
                    label = f"{len(recs)}" if len(recs) > 1 else txt
                    html.append(_cell_interativa(cls, label, recs, hj_cls))
                    
            html.append(f'<td style="color:#8FA882;font-weight:600">{total_lab}</td></tr>')
        
        html.append('</tbody></table></div>')
        st.markdown("".join(html), unsafe_allow_html=True)

        # Relatórios abaixo (Padrão Ensaios)
        with st.expander(f"Relatórios — {GRUPOS[grupo]['label']} ({len(labs_grupo)} pessoas)", expanded=False):
            for lab, info in labs_grupo:
                st.markdown(f'<div style="font-weight:700;color:#E8EFD8;font-size:.9rem;margin:10px 0 4px 0">{lab}</div>', unsafe_allow_html=True)
                lines = []
                for d in sorted(datas_mes, reverse=True):
                    for r in info["registros"].get(d, []):
                        sl = str(r.get("status", "")).lower(); clr = "#FF6B6B" if "reprovado" in sl or "pendente" in sl else "#3cb44b"
                        lines.append(f'<a href="{_BASE44_URL + r.get("reportUrl", "")}" target="_blank" style="display:block;color:{clr};font-size:.82rem;padding:3px 0;text-decoration:none;font-family:Inter,sans-serif;">{r.get("data", "")[:5]} — {r.get("obra", "—")} ({r.get("status", "Pendente")})</a>')
                st.markdown("".join(lines) if lines else '<div style="font-size:.75rem;color:#6b7f8d">Sem registros.</div>', unsafe_allow_html=True)
                st.markdown("<hr style='margin:8px 0;border:none;border-top:1px solid rgba(255,255,255,.07)'>", unsafe_allow_html=True)
