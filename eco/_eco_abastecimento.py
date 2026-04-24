# -*- coding: utf-8 -*-
"""
_eco_abastecimento.py
=====================
Aba de Abastecimento — integração com SouLog / GoodManager (Ticket Log / Edenred).

Scraping via subprocess Playwright (_eco_abast_worker.py) com perfil Chrome persistente
onde o usuário já está autenticado — mesmo padrão de _eco_ponto_worker.py.

Cache JSON em: cache_certificados/abastecimento_cache.json

Credenciais via st.secrets (apenas cd_veiculo e nr_cartao necessários):
  goodmanager_cd_veiculo → cd_veiculo_cliente
  goodmanager_nr_cartao  → nr_cartao (hash hex)
"""
from __future__ import annotations

import os, sys, re, json, subprocess
from pathlib import Path
from datetime import datetime, timedelta
from io import StringIO

import streamlit as st
import pandas as pd
import plotly.express as px

# Detecta se está no Streamlit Cloud (sem drive local)
_GDRIVE_PROBE = r"G:\.shortcut-targets-by-id\1NUJ7pNAqedohSrLjiwFErFrtVqVZkrjk"
_IS_CLOUD = not os.path.isdir(_GDRIVE_PROBE)

# =============================================================================
# CONSTANTES
# =============================================================================
_HERE      = Path(__file__).parent
_CACHE_DIR = _HERE.parent / "cache_certificados"
_CACHE_DIR.mkdir(parents=True, exist_ok=True)
_CACHE_JSON = _CACHE_DIR / "abastecimento_cache.json"
_WORKER     = _HERE / "_eco_abast_worker.py"

_CD_VEICULO_DEFAULT = "25135541"
_NR_CARTAO_DEFAULT  = (
    "E3ED76A3728933D9E9218801A8EBC78883B908B34BED8A180F0DF5ADC30E5BEC4"
    "22648986246099B412A50BA828E125A"
)


# =============================================================================
# HELPERS
# =============================================================================

def _secret(key: str, fallback: str = "") -> str:
    try:
        v = st.secrets.get(key, fallback)
        return v if v else fallback
    except Exception:
        return fallback


def _cd_veiculo() -> str:
    return _secret("goodmanager_cd_veiculo", _CD_VEICULO_DEFAULT)


def _nr_cartao() -> str:
    return _secret("goodmanager_nr_cartao", _NR_CARTAO_DEFAULT)


def _kpi_html(valor: str, label: str, cor: str = "#BFCF99") -> str:
    return f"""
    <div class="eco-kpi">
        <div class="val" style="color:{cor}">{valor}</div>
        <div class="lbl">{label}</div>
    </div>"""


# =============================================================================
# WORKER SUBPROCESS
# =============================================================================

def _sincronizar(data_ini: str = "", data_fim: str = "") -> tuple[bool, str]:
    """
    Chama o worker Playwright em subprocess isolado.
    Retorna (sucesso, mensagem).
    """
    if not _WORKER.exists():
        return False, f"Worker não encontrado: {_WORKER}"

    env = os.environ.copy()
    env["GM_CD_VEICULO"] = _cd_veiculo()
    env["GM_NR_CARTAO"]  = _nr_cartao()

    cmd = [sys.executable, str(_WORKER), str(_CACHE_JSON)]
    if data_ini:
        cmd += [data_ini, data_fim]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120, env=env)
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        if "DONE:" in stdout:
            n = stdout.split("DONE:")[-1].strip()
            return True, f"{n} registros carregados"
        if "SESSAO_EXPIRADA" in stdout:
            return False, (
                "⚠️ Sessão GoodManager expirada — abra o Chrome e faça login em "
                "www.goodmanager.com.br, depois sincronize novamente."
            )
        erro = stderr[-500:] if stderr else stdout
        return False, f"Erro no worker: {erro}"
    except subprocess.TimeoutExpired:
        return False, "Timeout (>120s) — servidor GoodManager lento."
    except Exception as e:
        return False, str(e)


# =============================================================================
# CARREGAMENTO DO CACHE
# =============================================================================

def _carregar_cache(data_ini: datetime, data_fim: datetime) -> pd.DataFrame:
    """Lê o JSON de cache e filtra por período."""
    if not _CACHE_JSON.exists():
        return pd.DataFrame()
    try:
        with open(_CACHE_JSON, encoding="utf-8") as f:
            dados = json.load(f)
        if not dados:
            return pd.DataFrame()
        # Suporta tanto lista plana quanto dict com chave "transacoes"
        if isinstance(dados, dict):
            dados = dados.get("transacoes", dados.get("data", []))
        if not dados:
            return pd.DataFrame()
        df = pd.DataFrame(dados)
        df = _normalizar(df)

        if "data_hora" in df.columns:
            mask = (
                (df["data_hora"].dt.date >= data_ini.date()) &
                (df["data_hora"].dt.date <= data_fim.date())
            )
            df = df[mask]
        return df
    except Exception as e:
        st.warning(f"Erro ao ler cache: {e}")
        return pd.DataFrame()


# =============================================================================
# NORMALIZAÇÃO
# =============================================================================

_MAPA_COLUNAS = {
    "data":           ["data transacao", "data", "dt", "data transação", "data/hora", "data da transação"],
    "hora":           ["hora", "horário", "horario"],
    "placa":          ["placa", "veículo", "veiculo"],
    "motorista":      ["nome motorista", "motorista", "condutor"],
    "produto":        ["tipo combustivel", "produto", "combustivel", "combustível", "tipo combustível"],
    "litros":         ["litros", "quantidade", "qtde", "volume"],
    "valor_unitario": ["vl/litro", "preço unit", "preço unitário", "vlr unit", "p.unit"],
    "valor_total":    ["valor emissao", "valor", "valor total", "vlr total", "total", "valor (r$)"],
    "posto":          ["nome estabelecimento", "posto", "estabelecimento", "local"],
    "km":             ["hodometro ou horimetro", "km", "hodômetro", "hodometro", "quilometragem"],
    "km_percorrido":  ["km rodados ou horas trabalhadas", "km percorrido", "km rodados"],
}


def _normalizar(df: pd.DataFrame) -> pd.DataFrame:
    rename = {}
    cols_l = {c.lower().strip(): c for c in df.columns}
    for std, variantes in _MAPA_COLUNAS.items():
        for v in variantes:
            if v in cols_l:
                rename[cols_l[v]] = std
                break
    df = df.rename(columns=rename)

    # data_hora
    if "data" in df.columns and "hora" in df.columns:
        df["data_hora"] = pd.to_datetime(
            df["data"].astype(str) + " " + df["hora"].astype(str),
            dayfirst=True, errors="coerce")
    elif "data" in df.columns:
        df["data_hora"] = pd.to_datetime(df["data"], dayfirst=True, errors="coerce")

    # Numéricos — se já forem float/int, converte direto; se forem string BR (1.234,56), normaliza
    for col in ["litros", "valor_total", "valor_unitario", "km", "km_percorrido"]:
        if col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                df[col] = pd.to_numeric(df[col], errors="coerce")
            else:
                df[col] = (df[col].astype(str)
                           .str.replace(r"R\$\s*", "", regex=True)
                           .str.replace(r"\.", "", regex=True)   # milhar: 1.234 → 1234
                           .str.replace(",", ".", regex=False)   # decimal: 1234,56 → 1234.56
                           .str.strip())
                df[col] = pd.to_numeric(df[col], errors="coerce")

    return df


# =============================================================================
# KPIs
# =============================================================================

def _kpis(df: pd.DataFrame):
    total  = len(df)
    litros = df["litros"].sum()      if "litros"      in df.columns else 0
    valor  = df["valor_total"].sum() if "valor_total" in df.columns else 0
    mots   = df["motorista"].nunique() if "motorista" in df.columns else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(_kpi_html(str(total), "Abastecimentos"), unsafe_allow_html=True)
    with c2:
        st.markdown(_kpi_html(f"{litros:,.0f} L".replace(",", "."), "Total Litros", "#6EC6FF"),
                    unsafe_allow_html=True)
    with c3:
        val_fmt = f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        st.markdown(_kpi_html(val_fmt, "Valor Total", "#81C784"), unsafe_allow_html=True)
    with c4:
        st.markdown(_kpi_html(str(mots), "Motoristas", "#FFB74D"), unsafe_allow_html=True)


# =============================================================================
# GRÁFICOS
# =============================================================================

_LAYOUT = dict(
    plot_bgcolor="#0D1B2A", paper_bgcolor="#0D1B2A",
    font=dict(color="#E8EFD8", family="Poppins"),
    title_font_color="#BFCF99",
    xaxis=dict(gridcolor="rgba(86,110,61,0.2)"),
    yaxis=dict(gridcolor="rgba(86,110,61,0.2)"),
)


def _graficos(df: pd.DataFrame):
    g1, g2 = st.columns(2)

    with g1:
        if "data_hora" in df.columns and "litros" in df.columns:
            ag = df.copy()
            ag["dia"] = ag["data_hora"].dt.date
            ag = ag.groupby("dia")["litros"].sum().reset_index()
            fig = px.bar(ag, x="dia", y="litros", title="Litros por Dia",
                         color_discrete_sequence=["#566E3D"],
                         labels={"dia": "Data", "litros": "Litros"})
            fig.update_layout(**_LAYOUT)
            st.plotly_chart(fig, use_container_width=True)

    with g2:
        if "motorista" in df.columns and "litros" in df.columns:
            ag2 = df.groupby("motorista")["litros"].sum().sort_values(ascending=True).reset_index()
            fig2 = px.bar(ag2, x="litros", y="motorista", orientation="h",
                          title="Litros por Motorista",
                          color_discrete_sequence=["#BFCF99"],
                          labels={"litros": "Litros", "motorista": ""})
            fig2.update_layout(**_LAYOUT)
            st.plotly_chart(fig2, use_container_width=True)

    g3, g4 = st.columns(2)

    with g3:
        if "produto" in df.columns and "litros" in df.columns:
            ag3 = df.groupby("produto")["litros"].sum().reset_index()
            fig3 = px.pie(ag3, names="produto", values="litros",
                          title="Combustível",
                          color_discrete_sequence=["#566E3D", "#BFCF99", "#8FA882"])
            fig3.update_layout(paper_bgcolor="#0D1B2A",
                               font=dict(color="#E8EFD8", family="Poppins"),
                               title_font_color="#BFCF99")
            st.plotly_chart(fig3, use_container_width=True)

    with g4:
        if "data_hora" in df.columns and "valor_unitario" in df.columns:
            df2 = df.dropna(subset=["data_hora", "valor_unitario"]).copy()
            df2["dia"] = df2["data_hora"].dt.date
            ag4 = df2.groupby("dia")["valor_unitario"].mean().reset_index()
            fig4 = px.line(ag4, x="dia", y="valor_unitario",
                           title="Preço Médio/L (R$)",
                           color_discrete_sequence=["#BFCF99"], markers=True)
            fig4.update_layout(**{**_LAYOUT, "yaxis": dict(
                gridcolor="rgba(86,110,61,0.2)", tickprefix="R$ ")})
            st.plotly_chart(fig4, use_container_width=True)


# =============================================================================
# TABELA
# =============================================================================

_COL_LABELS = {
    "data_hora":      "Data / Hora",
    "placa":          "Placa",
    "motorista":      "Motorista",
    "produto":        "Combustível",
    "litros":         "Litros",
    "valor_unitario": "Preço/L (R$)",
    "valor_total":    "Total (R$)",
    "posto":          "Posto",
    "km":             "Hodômetro",
    "km_percorrido":  "KM Rodados",
}


def _tabela(df: pd.DataFrame):
    cols = [c for c in _COL_LABELS if c in df.columns]
    df_s = df[cols].copy().rename(columns=_COL_LABELS)

    for col, lbl in _COL_LABELS.items():
        if col in ["litros", "km", "km_percorrido"] and lbl in df_s.columns:
            df_s[lbl] = df_s[lbl].apply(
                lambda x: f"{x:,.0f}".replace(",", ".") if pd.notna(x) else "—")
        elif col in ["valor_total", "valor_unitario"] and lbl in df_s.columns:
            df_s[lbl] = df_s[lbl].apply(
                lambda x: f"R$ {x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
                          if pd.notna(x) else "—")
        elif col == "data_hora" and lbl in df_s.columns:
            df_s[lbl] = df_s[lbl].apply(
                lambda x: x.strftime("%d/%m/%Y %H:%M") if pd.notna(x) else "—")

    st.dataframe(df_s, use_container_width=True, hide_index=True)


# =============================================================================
# ABA PRINCIPAL
# =============================================================================

def _aba_abastecimento():
    st.markdown("""
    <div style="margin-bottom:16px">
        <span style="font-family:Poppins,sans-serif; font-size:0.85rem; color:#8FA882">
            ⛽ Transações de abastecimento via
            <b style="color:#BFCF99">SouLog / Ticket Log</b> (Edenred · GoodManager)
        </span>
    </div>""", unsafe_allow_html=True)

    # ── Filtros ────────────────────────────────────────────────────────────────
    hoje = datetime.now().date()
    c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
    with c1:
        d_ini = st.date_input("De", value=hoje.replace(day=1), key="gm_dini")
    with c2:
        d_fim = st.date_input("Até", value=hoje, key="gm_dfim")
    with c3:
        sincronizar = st.button(
            "🔄 Sincronizar", key="gm_sync", use_container_width=True,
            disabled=_IS_CLOUD)
    with c4:
        cache_ts = ""
        if _CACHE_JSON.exists():
            ts = datetime.fromtimestamp(_CACHE_JSON.stat().st_mtime)
            cache_ts = ts.strftime("%d/%m/%Y %H:%M")
        if cache_ts:
            st.markdown(
                f"<span style='font-size:0.75rem;color:#8FA882'>Cache: {cache_ts}</span>",
                unsafe_allow_html=True)

    # ── Sincronização (local apenas) ───────────────────────────────────────────
    if sincronizar and not _IS_CLOUD:
        with st.spinner("Conectando ao GoodManager via Chrome..."):
            ok, msg = _sincronizar(
                d_ini.strftime("%d/%m/%Y"),
                d_fim.strftime("%d/%m/%Y")
            )
        if ok:
            st.success(f"✅ {msg}")
        else:
            st.error(f"❌ {msg}")
            if "Sessão" in msg or "expirada" in msg.lower():
                st.info(
                    "**Como renovar a sessão:**\n"
                    "1. Abra o Chrome normalmente\n"
                    "2. Acesse www.goodmanager.com.br\n"
                    "3. Faça login com suas credenciais\n"
                    "4. Volte aqui e clique em **Sincronizar** novamente\n\n"
                    "O Chrome usado pelo worker está em:\n"
                    f"`{Path.home() / 'OneDrive/Área de Trabalho/Ensaios AEVIAS/.cache_chrome_gm'}`"
                )
            return

    # ── Carregamento do cache ──────────────────────────────────────────────────
    df = _carregar_cache(
        datetime.combine(d_ini, datetime.min.time()),
        datetime.combine(d_fim, datetime.max.time())
    )

    if df.empty:
        st.info("Nenhuma transação no período selecionado.")
        return

    # ── KPIs ──────────────────────────────────────────────────────────────────
    _kpis(df)
    st.markdown("---")

    # ── Gráficos ──────────────────────────────────────────────────────────────
    _graficos(df)

    # ── Tabela detalhada ──────────────────────────────────────────────────────
    st.markdown("### Transações Detalhadas")

    f1, f2 = st.columns(2)
    with f1:
        if "motorista" in df.columns:
            mots = ["Todos"] + sorted(df["motorista"].dropna().unique().tolist())
            mot = st.selectbox("Motorista", mots, key="gm_mot")
        else:
            mot = "Todos"
    with f2:
        if "produto" in df.columns:
            prods = ["Todos"] + sorted(df["produto"].dropna().unique().tolist())
            prod = st.selectbox("Combustível", prods, key="gm_prod")
        else:
            prod = "Todos"

    df_tab = df.copy()
    if mot  != "Todos" and "motorista" in df_tab.columns:
        df_tab = df_tab[df_tab["motorista"] == mot]
    if prod != "Todos" and "produto" in df_tab.columns:
        df_tab = df_tab[df_tab["produto"] == prod]

    _tabela(df_tab)

    # ── Export ────────────────────────────────────────────────────────────────
    csv = df_tab.to_csv(index=False, sep=";", encoding="utf-8-sig")
    st.download_button(
        "📥 Exportar CSV",
        data=csv.encode("utf-8-sig"),
        file_name=f"abastecimento_{d_ini.strftime('%d-%m-%Y')}_{d_fim.strftime('%d-%m-%Y')}.csv",
        mime="text/csv",
        key="gm_csv",
    )
