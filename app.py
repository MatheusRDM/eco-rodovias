"""
=============================================================================
ECO RODOVIAS — Aplicação Standalone
=============================================================================
BR-050 (Eco Minas Goiás) + BR-365 (Eco Cerrado)
Checklist APP + Ensaios AEVIAS + Rastreamento Logos
=============================================================================
"""
import streamlit as st
import sys
import os

# ── Paths ─────────────────────────────────────────────────────────────────────
_ROOT = os.path.dirname(os.path.abspath(__file__))
_ECO  = os.path.join(_ROOT, "eco")
if _ROOT not in sys.path: sys.path.insert(0, _ROOT)
if _ECO  not in sys.path: sys.path.insert(0, _ECO)

from styles import aplicar_estilos
from auth import verificar_autenticacao, mostrar_tela_login, fazer_logout

# =============================================================================
st.set_page_config(
    page_title="Eco Rodovias | Afirma E-vias",
    page_icon="Imagens/logo_icon.png",
    layout="wide",
    initial_sidebar_state="collapsed",
)
aplicar_estilos()

# ── Autenticação ──────────────────────────────────────────────────────────────
if not verificar_autenticacao():
    mostrar_tela_login()
    st.stop()
# =============================================================================

st.markdown("""
<style>
/* ── Ocultar sidebar completamente ────────────────────────────────────────── */
section[data-testid="stSidebar"],
[data-testid="stSidebarNav"],
[data-testid="stSidebarNavItems"],
[data-testid="collapsedControl"],
button[aria-label="Close sidebar"],
button[aria-label="Open sidebar"],
button[kind="header"],
[data-testid="stSidebarToggle"] {
    display: none !important;
    width:  0   !important;
    min-width: 0 !important;
    overflow: hidden !important;
}
.main > .block-container {
    max-width: 100% !important;
    padding-left:  1.2rem !important;
    padding-right: 1.2rem !important;
}
[data-testid="stAppViewContainer"] > .main { margin-left: 0 !important; }

@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');

/* ═══════════════════════════════════════════════════════════
   MOBILE-FIRST RESPONSIVE
   ═══════════════════════════════════════════════════════════ */
@media (max-width: 768px) {
    [data-testid="stHorizontalBlock"] { flex-direction: column !important; gap: 4px !important; }
    [data-testid="stHorizontalBlock"] > div { width: 100% !important; flex: 1 1 100% !important; min-width: 0 !important; }
    .block-container { padding-left: 0.5rem !important; padding-right: 0.5rem !important; padding-top: 1rem !important; }
    section[data-testid="stSidebar"][aria-expanded="true"]  { width: 280px !important; min-width: 280px !important; overflow: visible !important; }
    section[data-testid="stSidebar"][aria-expanded="false"] { width: 0 !important; min-width: 0 !important; max-width: 0 !important; overflow: hidden !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 0px !important; overflow-x: auto !important; -webkit-overflow-scrolling: touch; scrollbar-width: none; flex-wrap: nowrap !important; }
    .stTabs [data-baseweb="tab-list"]::-webkit-scrollbar { display: none; }
    .stTabs [data-baseweb="tab"] { font-size: 0.72rem !important; padding: 8px 10px !important; white-space: nowrap !important; flex-shrink: 0 !important; }
    .eco-header h1 { font-size: 1.1rem !important; }
    .eco-header p  { font-size: 0.70rem !important; }
    .eco-header { padding: 10px 0 6px 0 !important; margin-bottom: 12px !important; }
    .eco-kpi { padding: 10px 8px !important; border-radius: 8px !important; }
    .eco-kpi .val { font-size: 1.4rem !important; }
    .eco-kpi .lbl { font-size: 0.62rem !important; }
    .cal-wrap { -webkit-overflow-scrolling: touch; }
    .cal-table { font-size: 0.60rem !important; min-width: 700px !important; }
    .cal-table th { font-size: 0.55rem !important; padding: 4px 2px !important; }
    .cal-table td { padding: 4px 2px !important; }
    .cal-table td.colab  { min-width: 100px !important; max-width: 130px !important; font-size: 0.62rem !important; }
    .cal-table td.funcao { min-width: 70px !important; max-width: 100px !important; font-size: 0.55rem !important; }
    .legend-item { font-size: 0.65rem !important; margin-right: 8px !important; }
    .js-plotly-plot, .plotly { width: 100% !important; }
    [data-testid="stDataFrame"] { overflow-x: auto !important; -webkit-overflow-scrolling: touch; }
    .stSelectbox > div > div, .stDateInput > div > div, .stMultiSelect > div > div { min-height: 42px !important; }
    .stButton > button { min-height: 44px !important; font-size: 0.82rem !important; }
    iframe[title*="streamlit_folium"] { width: 100% !important; height: 400px !important; }
    div[style*="display:flex"][style*="gap"] > div[style*="min-width"] { min-width: 0 !important; flex: 1 1 calc(50% - 4px) !important; }
}
@media (min-width: 769px) and (max-width: 960px) {
    [data-testid="stHorizontalBlock"] { flex-wrap: wrap !important; gap: 6px !important; }
    [data-testid="stHorizontalBlock"] > div { min-width: calc(50% - 6px) !important; flex: 1 1 calc(50% - 6px) !important; }
    .eco-header h1 { font-size: 1.3rem !important; }
    .eco-kpi .val { font-size: 1.6rem !important; }
}

/* ═══════════════════════════════════════════════════════════
   ESTILOS BASE
   ═══════════════════════════════════════════════════════════ */
.eco-header { padding: 18px 0 8px 0; border-bottom: 2px solid rgba(86,110,61,0.4); margin-bottom: 24px; }
.eco-header h1 { font-family: 'Poppins', sans-serif; font-size: 1.55rem; font-weight: 700; color: #BFCF99; margin: 0; }
.eco-header p  { font-family: 'Poppins', sans-serif; font-size: 0.82rem; color: #8FA882; margin: 4px 0 0 0; }
.eco-kpi { background: rgba(26,31,46,0.85); border: 1px solid rgba(86,110,61,0.35); border-radius: 10px; padding: 14px 18px; text-align: center; margin-bottom: 10px; }
.eco-kpi .val { font-family: 'Poppins', sans-serif; font-size: 2rem; font-weight: 700; line-height: 1; }
.eco-kpi .lbl { font-family: 'Poppins', sans-serif; font-size: 0.72rem; color: #8FA882; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.06em; }
.cal-wrap { overflow-x: auto; width: 100%; -webkit-overflow-scrolling: touch; }
.cal-table { border-collapse: collapse; font-family: 'Poppins', sans-serif; font-size: 0.68rem; width: 100%; min-width: 900px; }
.cal-table th { background: rgba(86,110,61,0.25); color: #BFCF99; padding: 5px 3px; text-align: center; font-weight: 600; border: 1px solid rgba(86,110,61,0.2); white-space: nowrap; font-size: 0.62rem; }
.cal-table td { padding: 5px 4px; border: 1px solid rgba(255,255,255,0.05); text-align: center; white-space: nowrap; }
.cal-table td.colab  { text-align: left; font-weight: 500; color: #E8EFD8; padding-left: 8px; min-width: 160px; max-width: 200px; overflow: hidden; text-overflow: ellipsis; }
.cal-table td.funcao { text-align: left; color: #8FA882; font-size: 0.60rem; min-width: 120px; max-width: 160px; overflow: hidden; text-overflow: ellipsis; }
.status-ok    { background: rgba(60,180,75,0.25);  color: #3cb44b; font-weight:600; border-radius:3px; }
.status-cobrar{ background: rgba(230,25,75,0.25);  color: #ff5577; font-weight:600; border-radius:3px; }
.status-ne    { background: rgba(58,74,94,0.4);    color: #7a90a8; }
.status-elab  { background: rgba(67,99,216,0.25);  color: #6ec6ff; font-weight:600; border-radius:3px; }
.status-vazio { background: transparent; color: #3a4a5e; }
.legend-item { display:inline-flex; align-items:center; gap:6px; margin-right:14px; font-size:0.75rem; font-family:'Poppins',sans-serif; color:#E8EFD8; }
.legend-dot  { width:12px; height:12px; border-radius:3px; display:inline-block; }
</style>
""", unsafe_allow_html=True)

# ── Module imports ─────────────────────────────────────────────────────────────
from _eco_shared import _IS_CLOUD
from _eco_checklist import _aba_checklist
from _eco_ensaios import _aba_ensaios
from _eco_rastreamento import _aba_rastreamento
from _eco_resumo import _aba_resumo
from _eco_diario import _aba_diario
from _eco_espelho_ponto import _aba_espelho_ponto, _salvar_cache, _processar_dados
from _eco_abastecimento import _aba_abastecimento
from _eco_bg_loader import is_loading, has_result, has_error, pop_result, pop_error


# =============================================================================
# POLLER DE SEGUNDO PLANO — verifica tarefas a cada 2s
# =============================================================================

@st.fragment(run_every=2)
def _bg_status_poller():
    try:
        _bg_status_poller_inner()
    except Exception as _exc:
        st.caption(f"⚠️ Poller: {_exc}")


def _bg_status_poller_inner():
    from datetime import date as _date

    # ── Logos Rastreamento ────────────────────────────────────────────────────
    if has_result("logos"):
        result = pop_result("logos")
        if result:
            st.session_state["logos_veiculos"]           = result["veiculos"]
            st.session_state["logos_ultima_atualizacao"] = result["ts"]
            st.session_state.pop("logos_ultimo_erro", None)
            for k in ("logos_rota", "logos_periodo_result", "fd_padroes"):
                st.session_state.pop(k, None)
            if result.get("fd_resultados"):
                st.session_state["fd_resultados"]     = result["fd_resultados"]
                st.session_state["fd_data_carregada"] = result.get("fd_data", "")
            st.toast("✅ Rastreamento atualizado!", icon="🚗")
            st.rerun(scope="app")
    if has_error("logos"):
        err = pop_error("logos")
        st.session_state["logos_ultimo_erro"] = err
        st.toast(f"❌ Rastreamento: {err}", icon="🚨")

    # ── Frota Dia ─────────────────────────────────────────────────────────────
    if has_result("frota_dia"):
        r = pop_result("frota_dia")
        if r:
            st.session_state["fd_resultados"]     = r["resultados"]
            st.session_state["fd_data_carregada"] = r["data"]
            st.session_state.pop("fd_padroes", None)
            st.toast("✅ Frota do dia atualizada!", icon="🚛")
            st.rerun(scope="app")
    if has_error("frota_dia"):
        st.toast(f"❌ Frota dia: {pop_error('frota_dia')}", icon="🚨")

    # ── Espelho Ponto ─────────────────────────────────────────────────────────
    if has_result("espelho_ponto"):
        raw_bytes = pop_result("espelho_ponto")
        if raw_bytes:
            _salvar_cache(raw_bytes)
            st.session_state["ep_raw_bytes"] = raw_bytes
            st.session_state["ep_ts"]        = _date.today().isoformat()
            st.session_state.pop("ep_show_upload", None)
            _processar_dados.clear()
            st.toast("✅ Espelho Ponto atualizado!", icon="⏱")
            st.rerun(scope="app")
    if has_error("espelho_ponto"):
        err = pop_error("espelho_ponto")
        st.session_state["ep_show_upload"] = True
        st.toast(f"❌ Espelho Ponto: {err}", icon="🚨")

    # ── Ensaios ───────────────────────────────────────────────────────────────
    if has_result("ensaios"):
        result = pop_result("ensaios")
        if result:
            ok, msg = result
            if ok:
                st.cache_data.clear()
                st.toast(f"✅ Ensaios: {msg}", icon="🧪")
                st.rerun(scope="app")
            else:
                st.toast(f"❌ Ensaios: {msg}", icon="🚨")
    if has_error("ensaios"):
        st.toast(f"❌ Ensaios: {pop_error('ensaios')}", icon="🚨")


# =============================================================================
# SIDEBAR
# =============================================================================

def _sidebar():
    with st.sidebar:
        st.markdown("""
        <style>
        section[data-testid="stSidebar"] { background: #0D1B2A !important; }
        .eco-sidebar-title {
            font-family:'Poppins',sans-serif; font-size:0.78rem;
            color:#8FA882; text-transform:uppercase; letter-spacing:.06em;
            margin: 8px 0 4px 0;
        }
        div[data-testid="stButton"] button {
            background: rgba(86,110,61,0.15) !important;
            border: 1px solid rgba(86,110,61,0.4) !important;
            color: #BFCF99 !important;
            font-family:'Poppins',sans-serif !important;
            font-size:0.78rem !important;
            padding:0.2rem 0.6rem !important;
            border-radius:6px !important;
            margin-bottom:0.5rem !important;
        }
        </style>""", unsafe_allow_html=True)

        try:
            st.image("Imagens/AE - Logo Hor Principal_2.png", use_container_width=True)
        except Exception:
            st.markdown('<h3 style="color:white;text-align:center">AFIRMA E-VIAS</h3>', unsafe_allow_html=True)

        st.markdown("---")
        st.markdown('<div class="eco-sidebar-title">Contrato</div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="font-family:'Poppins',sans-serif; font-size:0.80rem; color:#E8EFD8; line-height:1.6">
            <b style="color:#BFCF99">ECO RODOVIAS 6771</b><br>
            🛣️ BR-050 — Eco Minas Goiás<br>
            🛣️ BR-365 — Eco Cerrado<br>
            <span style="color:#8FA882; font-size:0.72rem">Supervisão de Obras</span>
        </div>""", unsafe_allow_html=True)

        st.markdown("---")
        usuario = st.session_state.get("usuario", "")
        st.markdown(
            f"<span style='font-size:0.82rem;color:#BFCF99;'>👤 {usuario}</span>",
            unsafe_allow_html=True,
        )
        if st.button("SAIR", use_container_width=True, key="logout_main"):
            fazer_logout()

        st.markdown("---")
        st.markdown('<div class="eco-sidebar-title">Acesso ao Servidor</div>', unsafe_allow_html=True)
        if _IS_CLOUD:
            st.warning("☁️ Modo Cloud — dados do cache", icon=None)
        else:
            st.success("💻 Servidor Y: conectado", icon=None)


# =============================================================================
# MAIN
# =============================================================================

def main():
    _sidebar()
    _bg_status_poller()

    st.markdown("""
    <div class="eco-header">
        <h1>🛣️ Eco Rodovias — Contrato 6771</h1>
        <p>BR-050 (Eco Minas Goiás) · BR-365 (Eco Cerrado) · Supervisão de Obras AFIRMA E-VIAS</p>
    </div>""", unsafe_allow_html=True)

    tab_resumo, tab_checklist, tab_diario, tab_ensaios, tab_rastr, tab_ponto, tab_abast = st.tabs([
        "Resumo",
        "Checklist",
        "Diario de Obra",
        "Ensaios",
        "Rastreamento",
        "Espelho Ponto",
        "⛽ Abastecimento",
    ])

    with tab_resumo:    _aba_resumo()
    with tab_checklist: _aba_checklist()
    with tab_diario:    _aba_diario()
    with tab_ensaios:   _aba_ensaios()
    with tab_rastr:     _aba_rastreamento()
    with tab_ponto:     _aba_espelho_ponto()
    with tab_abast:     _aba_abastecimento()


if __name__ == "__main__" or True:
    main()
