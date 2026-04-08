
"""
_eco_resumo.py — Resumo diário por profissional.
Combina dados de: Checklist APP + Ensaios AEVIAS + Rastreamento Logos.
Layout baseado no padrão da aba ENSAIOS.
"""
import sys, os, json
from datetime import datetime, date, timedelta
from collections import defaultdict
from calendar import monthrange

_PAGES_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR  = os.path.dirname(_PAGES_DIR)
if _PAGES_DIR not in sys.path: sys.path.insert(0, _PAGES_DIR)
if _ROOT_DIR  not in sys.path: sys.path.insert(0, _ROOT_DIR)

import streamlit as st

from _eco_shared import (
    COR_TEXT, COR_MUTED,
    _BASE_DIR, _CACHE_DIR, _IS_CLOUD,
    AEVIAS_BASE_URL,
)
from _eco_funcoes import cargo_para_grupo, header_grupo, ORDEM_GRUPOS, GRUPOS

_BASE44_URL    = AEVIAS_BASE_URL
_DETAILS_PATH  = os.path.join(_CACHE_DIR, "ensaios_details.json")

@st.cache_data(ttl=300, show_spinner=False)
def _carregar_details() -> dict:
    """Carrega ensaios_details.json (atividades, observações, jornada) se existir."""
    if not os.path.exists(_DETAILS_PATH):
        return {}
    try:
        with open(_DETAILS_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

# ─── CSS (PADRÃO ABA ENSAIOS) ───────────────────────────────────────────────
_CSS_RESUMO = """
<style>
.rs-header{margin-bottom:12px}
.rs-header h2{font-size:1.1rem;font-weight:700;color:#BFCF99;margin:0}
.rs-header p{font-size:.7rem;color:#8FA882;margin:2px 0 0}
.rs-hr{height:1px;background:rgba(255,255,255,.06);margin:16px 0}
.rs-empty{text-align:center;padding:20px;color:#6b7f8d;font-size:.8rem}
.rs-alert{background:rgba(76,201,240,.08);border:1px solid rgba(76,201,240,.2);
  border-radius:10px;padding:10px 14px;font-size:.75rem;color:#8ECAE6;margin-bottom:12px}
</style>
"""

_CSS_GRADE_RESUMO = """
<style>
.do-wrap-scroll{overflow-x:auto;-webkit-overflow-scrolling:touch;width:100%;margin-bottom:20px}
.do-table{border-collapse:collapse;font-size:.68rem;font-family:Inter,sans-serif;width:100%;min-width:700px}
.do-table th{
  background:rgba(86,110,61,.2);color:#BFCF99;padding:4px 3px;
  text-align:center;font-weight:600;border:1px solid rgba(86,110,61,.15);
  font-size:.6rem;white-space:nowrap
}
.do-table td{
  padding:5px 3px;border:1px solid rgba(255,255,255,.05);
  text-align:center;white-space:nowrap;font-size:0.65rem;
  transition: background 0.15s;
}
.do-table td.do-nome{
  text-align:left;font-weight:600;color:#E8EFD8;padding-left:8px;
  min-width:140px;max-width:200px;white-space:normal;
  vertical-align:middle;line-height:1.2
}
.do-nome-cargo{font-size:.55rem;color:#8FA882;font-weight:400;
  display:block;margin-top:1px;white-space:nowrap;
  overflow:hidden;text-overflow:ellipsis;max-width:196px}

/* Status e Hover (Padrão Ensaios) */
.do-ok{background:rgba(60,180,75,.2);color:#3cb44b;font-weight:700}
.do-pend{background:rgba(230,25,75,.2);color:#ff5577;font-weight:700}
.do-rep{background:rgba(230,25,75,.3);color:#e6194b;font-weight:700}
.do-elb{background:rgba(76,201,240,.2);color:#4CC9F0;font-weight:700}
.do-ens{background:rgba(247,183,49,.2);color:#F7B731;font-weight:700}
.do-vazio{color:#3a4a5e;background:transparent}
.do-hj{outline:2px solid #F7B731 !important;outline-offset:-1px}

/* Interatividade */
.do-table td:not(.do-nome):hover {
    background: rgba(123, 191, 106, 0.15) !important;
    cursor: pointer;
}

/* Tooltip customizado para manter dados extras do Resumo */
.rgr-tip-host{position:relative;display:block;width:100%;height:100%}
.rgr-tip-host a{color:inherit;text-decoration:none;display:block}
.rgr-tip-box{
  display:none;position:absolute;bottom:calc(100% + 8px);left:50%;
  transform:translateX(-50%);z-index:9999;
  background:#0D1B2A;border:1px solid rgba(123,191,106,.3);
  border-radius:8px;padding:12px;min-width:240px;max-width:340px;
  box-shadow:0 8px 32px rgba(0,0,0,.6);pointer-events:none;
  text-align:left;white-space:normal;font-weight:400
}
.rgr-tip-host:hover .rgr-tip-box{display:block}
.rgr-tip-date{font-size:.65rem;color:#8FA882;margin-bottom:2px}
.rgr-tip-status{font-size:.75rem;font-weight:700;margin-bottom:4px}
.rgr-tip-val{font-size:.68rem;color:#C8D8A8;line-height:1.45}
.rgr-tip-sep{display:block;height:1px;background:rgba(255,255,255,.08);margin:6px 0}
.rgr-tip-lbl{font-size:.54rem;text-transform:uppercase;letter-spacing:.08em;color:#6b7f8d;margin-bottom:2px}
</style>
"""

_DAY_ABBR_RS = {0:"SEG",1:"TER",2:"QUA",3:"QUI",4:"SEX",5:"SÁB",6:"DOM"}


def _buscar_km_historico(dates_range: list, rastr_itens: list) -> None:
    """Busca KM diário via Logos API e cacheia."""
    import re as _re2
    from _eco_rast_api import _logos_login, _logos_get_rota, _km_from_hist, _pick, _HIST_DT_FIELDS
    try:
        sess, idcli = _logos_login()
    except Exception as err:
        st.error(f"Login Logos falhou: {err}")
        return

    def _hm(dt_str):
        m = _re2.search(r'(\d{2}):(\d{2})', str(dt_str or ""))
        return (int(m.group(1)), int(m.group(2))) if m else (None, None)

    cache    = st.session_state.get("km_diario_cache", {})
    cache18  = st.session_state.get("km18_cache",  {})
    cache730 = st.session_state.get("km730_cache", {})

    veiculos = [v for v in rastr_itens if v.get("idvei")]
    total    = len(veiculos) * len(dates_range)
    prog     = st.progress(0, text="Buscando KM…")
    n = 0
    for v in veiculos:
        idvei = str(v["idvei"])
        cache.setdefault(idvei, {})
        cache18.setdefault(idvei, {})
        cache730.setdefault(idvei, {})
        for d in dates_range:
            if d not in cache[idvei]:
                try:
                    hist = _logos_get_rota(sess, v["idvei"], f"{d} 00:00", f"{d} 23:59")
                    cache[idvei][d] = _km_from_hist(hist)
                    h18 = [p for p in hist if (lambda h,m: h is not None and h >= 18)(*_hm(_pick(p, _HIST_DT_FIELDS)))]
                    cache18[idvei][d] = _km_from_hist(h18) if h18 else 0
                    h730 = [p for p in hist if (lambda h,m: h is not None and (h < 7 or (h == 7 and m < 30)))(*_hm(_pick(p, _HIST_DT_FIELDS)))]
                    cache730[idvei][d] = _km_from_hist(h730) if h730 else 0
                except Exception:
                    cache[idvei][d] = None; cache18[idvei][d] = 0; cache730[idvei][d] = 0
            n += 1
            prog.progress(n / total, text=f"Buscando KM… {n}/{total}")
    prog.empty()
    st.session_state["km_diario_cache"] = cache
    st.session_state["km18_cache"] = cache18
    st.session_state["km730_cache"] = cache730
    st.success("KM atualizado!")


def _render_grade_resumo(ck_by_person, ens_by_prof, dates_range, funcao_por_pessoa,
                         rastr_itens: list | None = None):
    """Grade baseada no padrão ENSAIOS (do-table)."""
    if not dates_range: return

    st.markdown(_CSS_GRADE_RESUMO, unsafe_allow_html=True)
    today_str = date.today().strftime("%Y-%m-%d")
    _det_cache = _carregar_details()

    def _esc(s: str) -> str: return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

    def _tip_html(r: dict) -> str:
        status_raw = str(r.get("status","")).lower()
        sc = "s-apo" if "aprovado" in status_raw else "s-pend" if "pendente" in status_raw else "s-rep" if "reprovado" in status_raw else "s-ok"
        parts = [
            f'<div class="rgr-tip-date">{_esc(r.get("data",""))}</div>',
            f'<div class="rgr-tip-status {sc}">{_esc(r.get("status","—"))}</div>',
            f'<div class="rgr-tip-val">{_esc(r.get("obra",""))} · {_esc(r.get("local",""))}</div>',
        ]
        det = _det_cache.get(r.get("reportUrl",""), {})
        if det.get("atividades"):
            parts.append('<span class="rgr-tip-sep"></span><div class="rgr-tip-lbl">Atividades</div>'
                         f'<div class="rgr-tip-val">{_esc(det["atividades"][:200])}</div>')
        if det.get("jornada"):
            parts.append(f'<div style="font-size:.68rem;color:#F7B731;margin-top:6px;font-weight:700">⏱ {_esc(det["jornada"])}</div>')
        return "".join(parts)

    def _cell_tip(cls: str, label: str, r: dict, href: str = "") -> str:
        tip  = f'<div class="rgr-tip-box">{_tip_html(r)}</div>'
        inner = (f'<a href="{href}" target="_blank">{label}</a>{tip}' if href else f'{label}{tip}')
        return f'<td class="{cls}"><span class="rgr-tip-host">{inner}</span></td>'

    all_pessoas = sorted(set(ck_by_person) | set(ens_by_prof))

    # Lookup veículo por pessoa
    import unicodedata as _ucd2
    def _tok(s):
        s = _ucd2.normalize("NFD", s.lower())
        s = "".join(c for c in s if _ucd2.category(c) != "Mn")
        return {t for t in s.split() if len(t) >= 4}
    _rastr_tokens2 = [((_tok(v.get("motorista",""))), v) for v in (rastr_itens or []) if v.get("motorista")]
    def _veiculo_de(nome):
        toks = _tok(nome); best, bn = None, 0
        for tm, v in _rastr_tokens2:
            n = len(toks & tm)
            if n > bn: bn, best = n, v
        return best if bn >= 1 else None
    _vei_por_pessoa = {p: _veiculo_de(p) for p in all_pessoas}

    # Lookup AEVIAS por pessoa
    def _tok3(s):
        s = _ucd2.normalize("NFD", s.lower())
        s = "".join(c for c in s if _ucd2.category(c) != "Mn")
        return {t for t in s.split() if len(t) >= 3}
    _ens_tok_index = [(_tok3(k), k) for k in ens_by_prof]
    def _ens_match(nome: str) -> dict:
        exact = ens_by_prof.get(nome)
        if exact is not None: return exact
        toks = _tok3(nome); best_key, best_n = None, 0
        for tm, k in _ens_tok_index:
            n = sum(1 for at in toks for bt in tm if at==bt or at.startswith(bt))
            if n > best_n: best_n, best_key = n, k
        return ens_by_prof[best_key] if best_key else {}

    km_cache = st.session_state.get("km_diario_cache", {})
    km18_cache = st.session_state.get("km18_cache",  {})
    km730_cache = st.session_state.get("km730_cache", {})

    por_grupo = defaultdict(list)
    for pessoa in all_pessoas:
        g = cargo_para_grupo(funcao_por_pessoa.get(pessoa, ""))
        por_grupo[g].append(pessoa)

    def _e_diario(r): return "diario" in str(r.get("tipo", "")).lower()

    for grupo in ORDEM_GRUPOS:
        pessoas = sorted(por_grupo.get(grupo, []))
        if not pessoas: continue

        st.markdown(header_grupo(grupo), unsafe_allow_html=True)

        html = ['<div class="do-wrap-scroll"><table class="do-table"><thead><tr>']
        html.append('<th colspan="2" style="text-align:left;padding-left:12px">Profissional</th>')
        for d in dates_range:
            dt = datetime.strptime(d, "%Y-%m-%d")
            hj = d == today_str
            sty = 'style="color:#F7B731;font-weight:700"' if hj else ""
            lbl = "HOJE" if hj else f"{dt.day:02d}"
            sub = _DAY_ABBR_RS[dt.weekday()]
            html.append(f'<th {sty}>{lbl}<br>{sub}</th>')
        html.append('<th>Total</th></tr></thead><tbody>')

        for pessoa in pessoas:
            ck_data_p = ck_by_person.get(pessoa, {})
            ens_data_p = _ens_match(pessoa)
            func = funcao_por_pessoa.get(pessoa, "")
            total_ok = sum(1 for d in dates_range if str(ck_data_p.get(d,"")).upper().strip()=="OK")
            vei = _vei_por_pessoa.get(pessoa)
            idvei_str = str(vei["idvei"]) if vei and vei.get("idvei") else None
            tem_ens = grupo != "SST"
            n_rows = (2 if not tem_ens else 3) + (3 if idvei_str else 0)

            # --- LINHA 1: CHECK ---
            cargo_html = f'<span class="do-nome-cargo">{func}</span>' if func else ""
            html.append(f'<tr><td class="do-nome" rowspan="{n_rows}">{pessoa}{cargo_html}</td>')
            html.append('<td class="do-tipo t-ck" style="color:#3cb44b">CHECK</td>')
            for d in dates_range:
                hj_cls = ' do-hj' if d == today_str else ''
                vu = str(ck_data_p.get(d, "")).upper().strip()
                cls_ck, lbl_ck = (f"do-ok{hj_cls}", "OK") if vu=="OK" else (f"do-elb{hj_cls}", "ELB") if vu=="ELB" else (f"do-pend{hj_cls}", "COB") if vu in ("COBRAR","COBRE") else (f"do-vazio{hj_cls}", "—")
                recs = [r for r in ens_data_p.get(d, []) if _e_diario(r) and r.get("reportUrl")]
                html.append(_cell_tip(cls_ck, lbl_ck, recs[0], _BASE44_URL+recs[0]["reportUrl"]) if recs else f'<td class="{cls_ck}">{lbl_ck}</td>')
            html.append(f'<td rowspan="{n_rows}" style="color:#8FA882;font-weight:600">{total_ok}</td></tr>')

            # --- LINHA 2: D.OBRA ---
            html.append(f'<tr><td class="do-tipo t-do" style="color:#4CC9F0">D.OBRA</td>')
            for d in dates_range:
                hj_cls = ' do-hj' if d == today_str else ''
                recs = [r for r in ens_data_p.get(d, []) if _e_diario(r)]
                if not recs: html.append(f'<td class="do-vazio{hj_cls}">—</td>')
                else: html.append(_cell_tip(f"do-elb{hj_cls}", "DO" if len(recs)==1 else str(len(recs)), recs[0], _BASE44_URL+recs[0].get("reportUrl","")))
            html.append('</tr>')

            # --- LINHA 3: ENSAIO ---
            if tem_ens:
                html.append(f'<tr><td class="do-tipo t-ens" style="color:#F7B731">ENSAIO</td>')
                for d in dates_range:
                    hj_cls = ' do-hj' if d == today_str else ''
                    ens = [r for r in ens_data_p.get(d, []) if not _e_diario(r) and "checklist" not in str(r.get("tipo","")).lower()]
                    if not ens:
                        html.append(f'<td class="do-vazio{hj_cls}">—</td>')
                    elif len(ens)==1:
                        html.append(_cell_tip(f"do-ens{hj_cls}", "ENS", ens[0], _BASE44_URL+ens[0].get("reportUrl","")))
                    else:
                        tip_txt = " | ".join(r.get("tipo","—") for r in ens)
                        urls_js = "[" + ",".join(f'"{_BASE44_URL+r.get("reportUrl","")}"' for r in ens if r.get("reportUrl")) + "]"
                        # Clique múltiplo via JS + Tooltip nativo combinados
                        html.append(
                            f'<td class="do-ens{hj_cls}" title="{tip_txt}" '
                            f'onclick="(function(){{var us={urls_js};us.forEach(function(u){{window.open(u,\'_blank\');}})}})()" '
                            f'style="cursor:pointer;font-weight:800">{len(ens)}</td>'
                        )
                html.append('</tr>')

            # --- LINHAS KM ---
            if idvei_str:
                vk = km_cache.get(idvei_str, {}); vk18 = km18_cache.get(idvei_str, {}); vk730 = km730_cache.get(idvei_str, {})
                for lbl, data_km, cor in [("KM Total", vk, "#FDCB6E"), ("Após 18h", vk18, "#FF7675"), ("Antes 7h30", vk730, "#A29BFE")]:
                    html.append(f'<tr><td class="do-tipo" style="color:{cor}">{lbl}</td>')
                    for d in dates_range:
                        hj = ' do-hj' if d == today_str else ''; v = data_km.get(d)
                        html.append(f'<td style="color:{cor};font-weight:700" class="{hj}">{v:.0f}</td>' if v and v>0 else f'<td class="do-vazio{hj}">—</td>')
                    html.append('</tr>')

        html.append('</tbody></table></div>')
        st.markdown("".join(html), unsafe_allow_html=True)

        # ── RELATÓRIOS (ESTILO ENSAIOS) ──
        with st.expander(f"Relatórios — {GRUPOS[grupo]['label']} ({len(pessoas)} pessoas)", expanded=False):
            for pessoa in pessoas:
                ens_data_p = _ens_match(pessoa)
                st.markdown(f'<div style="font-weight:700;color:#E8EFD8;font-size:.9rem;margin:10px 0 4px 0">{pessoa}</div>', unsafe_allow_html=True)
                lines = []
                for d in sorted(dates_range, reverse=True):
                    for r in ens_data_p.get(d, []):
                        obra, stat, url = r.get("obra","—"), str(r.get("status","")).lower(), _BASE44_URL+r.get("reportUrl","")
                        clr = "#FF6B6B" if "reprovado" in stat or "pendente" in stat else "#3cb44b"
                        slbl = "Reprovado" if "reprovado" in stat else ("Pendente" if "pendente" in stat else "Aprovado")
                        lines.append(f'<a href="{url}" target="_blank" style="display:block;color:{clr};font-size:.82rem;padding:3px 0;text-decoration:none;font-family:Inter,sans-serif;">{r.get("data",d)[-5:]} — {obra} ({slbl})</a>')
                st.markdown("".join(lines) if lines else '<div style="font-size:.75rem;color:#6b7f8d">Sem registros no período.</div>', unsafe_allow_html=True)
                st.markdown("<hr style='margin:8px 0;border:none;border-top:1px solid rgba(255,255,255,.07)'>", unsafe_allow_html=True)


def _carregar_ensaios_resumo():
    p = os.path.join(_CACHE_DIR, "ensaios_aevias.json")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f: return json.load(f)
    return []

def _carregar_checklist_resumo():
    p = os.path.join(_CACHE_DIR, "eco_checklist.json")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f: return json.load(f)
    return {}

def _get_rastreamento_data():
    veiculos = st.session_state.get("logos_veiculos", [])
    if not veiculos: return []
    try:
        from _eco_rast_api import _parse_eco
        return [_parse_eco(v, i) for i, v in enumerate(veiculos)]
    except Exception: return []

def _aba_resumo():
    """Aba Resumo — análise diária por profissional (Padrão Ensaios)."""
    try:
        st.image("Imagens/AE - Logo Hor Principal_2.png", width=220)
    except:
        pass

    st.markdown(_CSS_RESUMO, unsafe_allow_html=True)
    st.markdown('<div class="rs-header"><h2>Resumo Diário por Profissional</h2><p>Checklist + Ensaios + Rastreamento combinados (Visual Ensaios)</p></div>', unsafe_allow_html=True)

    today = date.today(); today_str = today.strftime("%Y-%m-%d")
    ensaios_raw = _carregar_ensaios_resumo(); checklist_cache = _carregar_checklist_resumo(); rastr_itens = _get_rastreamento_data()

    # Build indices
    ens_by_prof = defaultdict(lambda: defaultdict(list))
    for e in ensaios_raw:
        prof = (e.get("lab") or e.get("profissional") or "").strip()
        if not prof: continue
        try: d = datetime.strptime(e["data"].split()[0], "%d/%m/%Y").strftime("%Y-%m-%d")
        except Exception: continue
        ens_by_prof[prof][d].append(e)

    ck_by_person = defaultdict(dict)
    if checklist_cache:
        meds = sorted(checklist_cache.keys()); latest_med = meds[-1] if meds else None
        if latest_med:
            for people in checklist_cache[latest_med].get("sheets", {}).values():
                for p in people:
                    nome = p.get("colaborador", "").strip()
                    if nome:
                        for d, v in p.get("dias", {}).items(): ck_by_person[nome][d] = v

    all_people = set(ens_by_prof.keys()) | set(ck_by_person.keys())
    if not all_people:
        st.markdown('<div class="rs-empty">Nenhum dado encontrado.</div>', unsafe_allow_html=True); return

    if not rastr_itens: st.markdown('<div class="rs-alert">&#9432; Rastreamento não carregado.</div>', unsafe_allow_html=True)

    _DATA_MIN = date(2026, 3, 1)
    _PT = {1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"}
    meses_disp = []; cur = _DATA_MIN.replace(day=1)
    while cur <= today.replace(day=1):
        meses_disp.append((cur.year, cur.month))
        m2 = cur.month+1; cur = cur.replace(year=cur.year+(1 if m2>12 else 0), month=(m2-1)%12+1)
    meses_disp.reverse(); opcoes_mes = {f"{_PT[m]}/{y}": (y, m) for y, m in meses_disp}

    fl1, fl2 = st.columns([1, 1])
    with fl1: mes_lbl = st.selectbox("Mes:", list(opcoes_mes.keys()), key="rs_mes")
    ano_sel, mes_sel = opcoes_mes[mes_lbl]

    _, ultimo_dia = monthrange(ano_sel, mes_sel)
    dias_disp = list(range(1, min(ultimo_dia, today.day if (ano_sel==today.year and mes_sel==today.month) else ultimo_dia)+1))
    opcoes_dia = {"Todos os dias": 0, **{str(d): d for d in reversed(dias_disp)}}
    with fl2: dia_lbl = st.selectbox("Dia:", list(opcoes_dia.keys()), key="rs_dia")
    dia_sel = opcoes_dia[dia_lbl]

    if dia_sel == 0:
        d_ini = max(date(ano_sel, mes_sel, 1), _DATA_MIN)
        d_fim = date(ano_sel, mes_sel, min(ultimo_dia, today.day if (ano_sel==today.year and mes_sel==today.month) else ultimo_dia))
        dates_range = [(d_ini+timedelta(days=i)).strftime("%Y-%m-%d") for i in range((d_fim-d_ini).days+1)]
    else: dates_range = [date(ano_sel, mes_sel, dia_sel).strftime("%Y-%m-%d")]
    dates_range = [d for d in dates_range if d >= _DATA_MIN.strftime("%Y-%m-%d")]

    fl3, fl4 = st.columns([1, 1])
    obras_todas = sorted({e.get("obra","") for e in ensaios_raw if e.get("obra") and "diario" not in str(e.get("tipo","")).lower()})
    with fl3: obra_sel = st.selectbox("Tipo de Obra:", ["Todas"] + obras_todas, key="rs_obra")
    with fl4: prof_sel = st.selectbox("Profissional:", ["Todos"] + sorted(all_people), key="rs_prof")
    
    people_sorted = [prof_sel] if prof_sel != "Todos" else sorted(all_people)
    ens_by_prof_filtrado = ens_by_prof
    if obra_sel != "Todas":
        ens_by_prof_filtrado = defaultdict(lambda: defaultdict(list))
        for prof, dias in ens_by_prof.items():
            for d, recs in dias.items():
                rf = [r for r in recs if r.get("obra")==obra_sel or "diario" in str(r.get("tipo","")).lower()]
                if rf: ens_by_prof_filtrado[prof][d] = rf

    funcao_por_pessoa = {}
    for med in checklist_cache.values():
        for pessoas in med.get("sheets", {}).values():
            for p in pessoas:
                if p.get("colaborador") and p.get("funcao"): funcao_por_pessoa[p["colaborador"].strip()] = p["funcao"]

    st.markdown('<div class="rs-hr"></div>', unsafe_allow_html=True)
    if rastr_itens:
        _c1, _c2 = st.columns([5, 1])
        with _c2:
            if st.button("Buscar KM", key="btn_km_hist", use_container_width=True):
                with st.spinner("Buscando KM..."): _buscar_km_historico(dates_range, rastr_itens)
                st.rerun()

    _render_grade_resumo(ck_by_person, ens_by_prof_filtrado, dates_range, funcao_por_pessoa, rastr_itens=rastr_itens)
