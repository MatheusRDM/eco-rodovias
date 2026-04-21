"""
_eco_ensaios.py — Ensaios AEVIAS: analytics completo.

FONTE DE DADOS (ordem de prioridade):
  1. API Base44 direta (sempre disponível, TTL 5 min) — _base44_api.listar()
  2. JSON do desktop (máquina local, fallback)
  3. JSON do cache do app (cloud, fallback final)
"""
import sys, os, json, subprocess, shutil
from datetime import datetime, date, timedelta

_PAGES_DIR = os.path.dirname(os.path.abspath(__file__))
_ROOT_DIR  = os.path.dirname(_PAGES_DIR)
if _PAGES_DIR not in sys.path: sys.path.insert(0, _PAGES_DIR)
if _ROOT_DIR  not in sys.path: sys.path.insert(0, _ROOT_DIR)

import streamlit as st
import pandas as pd
import plotly.graph_objects as go

from _eco_shared import (
    COR_TEXT, COR_MUTED,
    PLOTLY_LAYOUT, PLOTLY_CONFIG,
    _BASE_DIR, _CACHE_DIR, _IS_CLOUD,
    AEVIAS_BASE_URL,
)
from _eco_funcoes import cargo_para_grupo, header_grupo, ORDEM_GRUPOS, GRUPOS, badge_grupo
from _eco_bg_loader import start_bg_task, is_loading, render_atualizar_btn
from _base44_api import listar as _b44_listar, token_info as _b44_token_info

# =============================================================================
# CONSTANTES
# =============================================================================
_AEVIAS_BASE    = AEVIAS_BASE_URL
_JSON_CACHE     = os.path.join(_CACHE_DIR, "ensaios_aevias.json")
_JSON_DESKTOP   = os.path.join(
    os.path.expanduser("~"), "OneDrive", "Área de Trabalho",
    "Ensaios AEVIAS", "ensaios_dados.json"
)
_SCRIPT_SYNC    = os.path.join(
    os.path.expanduser("~"), "OneDrive", "Área de Trabalho",
    "Ensaios AEVIAS", "baixar_ensaios.py"
)

# Paleta de cores por categoria (obra)
_COR_OBRA = {
    "SST":              "#e6194b",
    "Pavimento":        "#3cb44b",
    "TOPOGRAFIA":       "#ffe119",
    "OAE / Terraplenos":"#4363d8",
    "Ampliações":       "#f58231",
    "ESCRITÓRIO":       "#911eb4",
    "Conserva":         "#42d4f4",
}
_COR_TIPO = {
    "Diário de Obra":       "#7BBF6A",
    "Checklist de Usina":   "#4CC9F0",
    "Checklist de Aplicação":"#F7B731",
    "Checklist de MRAF":    "#FF6B6B",
    "Ensaio de CAUQ":       "#A29BFE",
}
_OBRAS_ORDEM = ["SST","Pavimento","TOPOGRAFIA","OAE / Terraplenos",
                "Ampliações","ESCRITÓRIO","Conserva"]

# Paleta gráficos
_C = {
    "bg":    "rgba(0,0,0,0)",
    "grid":  "rgba(255,255,255,0.06)",
    "text":  "#C8D8A8",
    "seq":   ["#7BBF6A","#4CC9F0","#F7B731","#FF6B6B","#A29BFE","#FD79A8","#00CEC9"],
}
_BASE = dict(
    paper_bgcolor=_C["bg"], plot_bgcolor=_C["bg"],
    font=dict(family="Inter, sans-serif", color=_C["text"], size=12),
    margin=dict(l=12, r=12, t=36, b=12),
    dragmode=False,
)
_NI = dict(displayModeBar=False, scrollZoom=False)

# =============================================================================
# CARGA DE DADOS — API BASE44 DIRETA
# =============================================================================

# Mapeamento entidade → nome amigável do tipo
_ENTIDADE_TIPO = {
    "DiarioObra":                "Diário de Obra",
    "EnsaioCAUQ":                "Ensaio de CAUQ",
    "ChecklistUsina":            "Checklist de Usina",
    "ChecklistAplicacao":        "Checklist de Aplicação",
    "ChecklistMRAF":             "Checklist de MRAF",
    "ChecklistTerraplanagem":    "Checklist Terraplanagem",
    "ChecklistConcretagem":      "Checklist Concretagem",
    "ChecklistReciclagem":       "Checklist Reciclagem",
    "AcompanhamentoUsinagem":    "Acompanhamento Usinagem",
    "AcompanhamentoCarga":       "Acompanhamento Carga",
    "EnsaioDensidadeInSitu":     "Ensaio Densidade In Situ",
    "EnsaioGranulometriaIndividual": "Ensaio Granulometria",
    "EnsaioManchaPendulo":       "Ensaio Mancha/Pêndulo",
    "EnsaioVigaBenkelman":       "Ensaio Viga Benkelman",
    "EnsaioProctor":             "Ensaio Proctor",
    "EnsaioTaxaMRAF":            "Ensaio Taxa MRAF",
    "EnsaioTaxaPinturaImprimacao": "Ensaio Taxa Pintura",
    "EnsaioSondagem":            "Ensaio Sondagem",
}

# Mapeamento entidade → categoria de obra
_ENTIDADE_OBRA = {
    "DiarioObra":                "Pavimento",
    "EnsaioCAUQ":                "Pavimento",
    "ChecklistUsina":            "Pavimento",
    "ChecklistAplicacao":        "Pavimento",
    "ChecklistMRAF":             "Pavimento",
    "ChecklistTerraplanagem":    "OAE / Terraplenos",
    "ChecklistConcretagem":      "OAE / Terraplenos",
    "ChecklistReciclagem":       "Pavimento",
    "AcompanhamentoUsinagem":    "Pavimento",
    "AcompanhamentoCarga":       "Pavimento",
    "EnsaioDensidadeInSitu":     "Pavimento",
    "EnsaioGranulometriaIndividual": "Pavimento",
    "EnsaioManchaPendulo":       "Pavimento",
    "EnsaioVigaBenkelman":       "Pavimento",
    "EnsaioProctor":             "OAE / Terraplenos",
    "EnsaioTaxaMRAF":            "Pavimento",
    "EnsaioTaxaPinturaImprimacao": "Pavimento",
    "EnsaioSondagem":            "OAE / Terraplenos",
}

# URL do app para abrir cada entidade
_AEVIAS_APP = "https://aevias-controle.base44.app"
_ENTIDADE_PATH = {
    "DiarioObra":             "/diario-de-obra",
    "EnsaioCAUQ":             "/ensaio-cauq",
    "ChecklistUsina":         "/checklist",
    "ChecklistAplicacao":     "/checklist-aplicacao",
    "ChecklistMRAF":          "/checklist-mraf",
    "ChecklistTerraplanagem": "/checklist-terraplanagem",
    "ChecklistConcretagem":   "/checklist-concretagem",
    "ChecklistReciclagem":    "/checklist-reciclagem",
    "AcompanhamentoUsinagem": "/acompanhamento-usinagem",
    "AcompanhamentoCarga":    "/acompanhamento-carga",
    "EnsaioDensidadeInSitu":  "/ensaio-densidade",
    "EnsaioGranulometriaIndividual": "/ensaio-granulometria",
    "EnsaioManchaPendulo":    "/ensaio-mancha-pendulo",
    "EnsaioVigaBenkelman":    "/ensaio-viga-benkelman",
    "EnsaioProctor":          "/EnsaioProctor",
    "EnsaioTaxaMRAF":         "/ensaio-taxa-mraf",
    "EnsaioTaxaPinturaImprimacao": "/ensaio-taxa-pintura",
    "EnsaioSondagem":         "/ensaio-sondagem",
}


def _status_b44(rec: dict) -> str:
    """Converte flags Base44 em label de status."""
    if rec.get("was_rejected"):
        return "Reprovado"
    if rec.get("approved"):
        return "Aprovado"
    return "Pendente"


def _data_b44(rec: dict) -> str:
    """Extrai data ISO do registro e converte para dd/mm/yyyy."""
    raw = rec.get("data") or rec.get("data_ensaio") or rec.get("created_date", "")
    try:
        d = datetime.fromisoformat(str(raw)[:10])
        return d.strftime("%d/%m/%Y")
    except Exception:
        return str(raw)[:10]


def _get_lab(rec: dict) -> str:
    """Extrai nome do laboratorista de forma segura (created_by pode ser str ou dict)."""
    nome = rec.get("laboratorista_name", "")
    if nome:
        return nome
    cb = rec.get("created_by")
    if isinstance(cb, dict):
        return cb.get("full_name", "—")
    if isinstance(cb, str):
        return cb or "—"
    return "—"


def _normalizar_registro(entidade: str, rec: dict) -> dict:
    """Converte um registro Base44 para o formato esperado por _df_ensaios."""
    rec_id   = rec.get("id", "")
    path     = _ENTIDADE_PATH.get(entidade, f"/{entidade}")
    report_url = f"{path}/{rec_id}" if rec_id else path
    return {
        "obra":       _ENTIDADE_OBRA.get(entidade, "Pavimento"),
        "tipo":       _ENTIDADE_TIPO.get(entidade, entidade),
        "lab":        _get_lab(rec),
        "profissional": _get_lab(rec),
        "data":       _data_b44(rec),
        "reportUrl":  report_url,
        "status":     _status_b44(rec),
        "id":         rec_id,
    }


def _obra_nome_para_grupo(obra_name: str) -> str:
    """Converte o nome da obra do Base44 para o grupo de frente de serviço."""
    n = (obra_name or "").upper()
    if "SST" in n or "SEGURANÇA" in n or "SEGURANCA" in n:
        return "SST"
    if "TOPOGRAFIA" in n or "TOPO" in n:
        return "Topografia"
    if "ESCRITÓRIO" in n or "ESCRITORIO" in n or "ESCRITOR" in n:
        return "Escritório"
    if "OAE" in n or "TERRAPLAN" in n or "SONDAGEM" in n:
        return "OAE / Terraplenos"
    if "CONSERVA" in n:
        return "Conserva"
    return "Pavimento"


@st.cache_data(ttl=3600, show_spinner=False)
def _carregar_mapa_obras() -> dict:
    """Busca entidade Obra do Base44 e retorna mapa {obra_id: grupo}."""
    try:
        obras = _b44_listar("Obra")
        return {o["id"]: _obra_nome_para_grupo(o.get("name", "")) for o in obras if o.get("id")}
    except Exception:
        return {}


def _carregar_ensaios_api() -> list[dict]:
    """
    Busca todos os tipos de registro diretamente da API Base44.
    Usa obra_id para categorizar corretamente em SST / Pavimento / Topografia / Escritório.
    """
    mapa_obras = _carregar_mapa_obras()
    resultado = []
    for entidade in _ENTIDADE_TIPO.keys():
        registros = _b44_listar(entidade)
        for rec in registros:
            norm = _normalizar_registro(entidade, rec)
            # Sobrescreve 'obra' com o grupo real baseado em obra_id
            obra_id = rec.get("obra_id") or rec.get("project_id") or ""
            if obra_id and obra_id in mapa_obras:
                norm["obra"] = mapa_obras[obra_id]
            resultado.append(norm)
    return resultado


# =============================================================================
# CARGA DE DADOS — FALLBACK JSON (local/cache)
# =============================================================================

def _carregar_ensaios(forcar_cache: bool = False) -> list[dict]:
    """
    Carrega dados de ensaios na seguinte ordem de prioridade:
      1. JSON do desktop (máquina local, mais atualizado)
      2. JSON do cache do app (cloud ou máquina sem desktop atualizado)
    Retorna lista de dicts com: data, obra, profissional, tipo, reportUrl
    """
    for caminho in ([_JSON_DESKTOP, _JSON_CACHE] if not forcar_cache
                    else [_JSON_CACHE]):
        if os.path.exists(caminho):
            with open(caminho, encoding="utf-8") as f:
                dados = json.load(f)
            return dados
    return []


def _sincronizar_playwright(data_ini: str = "", data_fim: str = "") -> tuple:
    """
    Scrapa AEVIAS CONTROLE on-demand via Playwright (perfil Chrome persistente).
    Grava o resultado direto em _JSON_CACHE e invalida o cache Streamlit.
    """
    worker = os.path.join(_PAGES_DIR, "_eco_aevias_worker.py")
    if not os.path.exists(worker):
        return False, "Worker não encontrado: " + worker

    args = [sys.executable, worker, _JSON_CACHE]
    if data_ini and data_fim:
        args += [data_ini, data_fim]

    try:
        result = subprocess.run(
            args, capture_output=True, text=True, timeout=300,
            cwd=_PAGES_DIR,
        )
    except subprocess.TimeoutExpired:
        return False, "Timeout (>5 min) — processo ainda pode estar rodando"
    except Exception as e:
        return False, str(e)

    stdout = result.stdout.strip()
    stderr = result.stderr.strip()

    if "SESSAO_EXPIRADA" in stdout:
        return False, (
            "Sessão expirada no Chrome — abra `baixar_ensaios.py` para fazer login "
            "novamente no AEVIAS CONTROLE."
        )
    if "DONE:" in stdout:
        n = stdout.split("DONE:")[-1].strip().split()[0]
        import streamlit as _st2
        _st2.cache_data.clear()
        return True, f"{n} registros sincronizados com sucesso."
    return False, (stderr or stdout)[-500:] or "Sem saída do worker"


def _sincronizar_e_copiar():
    """Mantido para compatibilidade — redireciona para _sincronizar_playwright."""
    return _sincronizar_playwright()


def _df_ensaios(dados: list[dict]) -> pd.DataFrame:
    """Constrói e normaliza o DataFrame de ensaios."""
    if not dados:
        return pd.DataFrame()
    df = pd.DataFrame(dados)
    df["obra"] = df["obra"].str.strip()
    df["tipo"] = df["tipo"].str.strip()
    # Retrocompatibilidade: novo scraper usa 'lab', antigo usava 'profissional'
    if "lab" in df.columns:
        df["profissional"] = df["lab"].fillna("").str.strip()
    elif "profissional" in df.columns:
        df["profissional"] = df["profissional"].fillna("").str.strip()
    else:
        df["profissional"] = "—"
    df["data_dt"]      = pd.to_datetime(df["data"].str.split().str[0], format="%d/%m/%Y", errors="coerce")
    df["data_iso"]     = df["data_dt"].dt.strftime("%Y-%m-%d")
    df["semana"]       = df["data_dt"].dt.isocalendar().week.astype(str)
    df["dia_semana"]   = df["data_dt"].dt.dayofweek  # 0=Seg
    df["url_completa"] = _AEVIAS_BASE + df["reportUrl"].fillna("")
    return df.sort_values("data_dt", ascending=False).reset_index(drop=True)


# =============================================================================
# SUBCOMPONENTES VISUAIS
# =============================================================================

def _cards_resumo(df: pd.DataFrame, ultima_sync: str):
    total    = len(df)
    obras_n  = df["obra"].nunique()
    profs_n  = df["profissional"].nunique()
    dias_n   = df["data_dt"].nunique()
    d_ini    = df["data_dt"].min().strftime("%d/%m") if not df.empty else "—"
    d_fim    = df["data_dt"].max().strftime("%d/%m") if not df.empty else "—"
    st.markdown(f"""
    <div style="display:flex;gap:10px;flex-wrap:wrap;margin-bottom:18px">
      <div style="flex:1;min-width:100px;background:rgba(123,191,106,0.12);border:1px solid #7BBF6A55;
                  border-radius:10px;padding:14px;text-align:center">
        <div style="font-size:1.7rem;font-weight:700;color:#7BBF6A">{total}</div>
        <div style="color:#C8D8A8;font-size:.75rem">Total registros</div></div>
      <div style="flex:1;min-width:100px;background:rgba(76,201,240,0.12);border:1px solid #4CC9F055;
                  border-radius:10px;padding:14px;text-align:center">
        <div style="font-size:1.7rem;font-weight:700;color:#4CC9F0">{dias_n}</div>
        <div style="color:#C8D8A8;font-size:.75rem">Dias com registro<br>{d_ini} → {d_fim}</div></div>
      <div style="flex:1;min-width:100px;background:rgba(247,183,49,0.12);border:1px solid #F7B73155;
                  border-radius:10px;padding:14px;text-align:center">
        <div style="font-size:1.7rem;font-weight:700;color:#F7B731">{profs_n}</div>
        <div style="color:#C8D8A8;font-size:.75rem">Profissionais/Projetos</div></div>
      <div style="flex:1;min-width:100px;background:rgba(255,107,107,0.12);border:1px solid #FF6B6B55;
                  border-radius:10px;padding:14px;text-align:center">
        <div style="font-size:1.7rem;font-weight:700;color:#FF6B6B">{obras_n}</div>
        <div style="color:#C8D8A8;font-size:.75rem">Categorias de obra</div></div>
      <div style="flex:1;min-width:100px;background:rgba(162,155,254,0.12);border:1px solid #A29BFE55;
                  border-radius:10px;padding:14px;text-align:center">
        <div style="font-size:.85rem;font-weight:700;color:#A29BFE">{ultima_sync}</div>
        <div style="color:#C8D8A8;font-size:.75rem">Última sincronização</div></div>
    </div>""", unsafe_allow_html=True)


def _grafico_timeline(df: pd.DataFrame):
    st.markdown("### Timeline — Produção Diária por Categoria")
    df_t = df.dropna(subset=["data_dt"]).copy()
    timeline = df_t.groupby(["data_iso","obra"]).size().reset_index(name="qtd")
    todas_datas = sorted(df_t["data_iso"].unique())
    todas_obras = list(_COR_OBRA.keys())

    fig = go.Figure()
    for obra in todas_obras:
        sub = timeline[timeline["obra"] == obra]
        fig.add_trace(go.Bar(
            x=sub["data_iso"], y=sub["qtd"],
            name=obra,
            marker_color=_COR_OBRA.get(obra, "#888"),
            hovertemplate=f"<b>{obra}</b><br>%{{x}}: %{{y}} reg<extra></extra>",
        ))
    fig.update_layout(
        **_BASE,
        height=280, barmode="stack",
        xaxis=dict(gridcolor=_C["grid"], tickangle=-45, tickfont=dict(size=10)),
        yaxis=dict(gridcolor=_C["grid"], title="Registros"),
        legend=dict(orientation="h", y=-0.3, x=0, font=dict(size=10)),
        title=dict(text="Registros por dia (empilhado por categoria)",
                   font=dict(size=12), x=0),
    )
    st.plotly_chart(fig, use_container_width=True, config=_NI)


def _heatmap_profissional(df: pd.DataFrame):
    st.markdown("### ️ Heatmap — Quem Trabalhou Cada Dia")
    df_t = df.dropna(subset=["data_dt"]).copy()
    profs = sorted(df_t["profissional"].unique())
    datas = sorted(df_t["data_iso"].unique())

    pivot = (df_t.groupby(["profissional","data_iso"]).size()
                  .unstack(fill_value=0)
                  .reindex(index=profs, columns=datas, fill_value=0))

    # Texto com contagem
    text_vals = [[str(v) if v > 0 else "" for v in row] for row in pivot.values]

    fig = go.Figure(go.Heatmap(
        z=pivot.values,
        x=[d[5:] for d in datas],   # MM-DD
        y=profs,
        text=text_vals,
        texttemplate="%{text}",
        colorscale=[[0,"#0D1B2A"],[0.01,"#1a3a1a"],[0.3,"#3cb44b"],[1,"#7BBF6A"]],
        showscale=False,
        hovertemplate="<b>%{y}</b> · %{x}: %{z} registros<extra></extra>",
        xgap=2, ygap=2,
    ))
    fig.update_layout(
        **_BASE,
        height=max(220, len(profs) * 38 + 60),
        xaxis=dict(tickfont=dict(size=9), side="top"),
        yaxis=dict(tickfont=dict(size=11), autorange="reversed"),
        title=dict(text="Registros por profissional/dia (verde = ativo, escuro = sem registro)",
                   font=dict(size=11), x=0),
    )
    st.plotly_chart(fig, use_container_width=True, config=_NI)


def _pivot_quem_fez_o_que(df: pd.DataFrame):
    st.markdown("### Pivot: Profissional × Dia × Tipo")
    df_t = df.dropna(subset=["data_dt"]).copy()
    datas = sorted(df_t["data_iso"].unique())
    profs = sorted(df_t["profissional"].unique())

    # Para cada célula: string com iniciais dos tipos
    _TIPO_SIGLA = {
        "Diário de Obra":        "DO",
        "Checklist de Usina":    "CU",
        "Checklist de Aplicação":"CA",
        "Checklist de MRAF":     "MR",
        "Ensaio de CAUQ":        "CAUQ",
    }

    rows = []
    for prof in profs:
        row = {"Profissional": prof}
        for d in datas:
            sub = df_t[(df_t["profissional"] == prof) & (df_t["data_iso"] == d)]
            if sub.empty:
                row[d[5:]] = ""
            else:
                siglas = sorted(set(_TIPO_SIGLA.get(t, t[:2]) for t in sub["tipo"]))
                row[d[5:]] = " · ".join(siglas)
        rows.append(row)

    df_pivot = pd.DataFrame(rows).set_index("Profissional")
    st.dataframe(df_pivot, use_container_width=True, height=max(200, len(profs)*35+50))
    st.caption("DO=Diário de Obra · CU=Checklist Usina · CA=Checklist Aplicação · "
               "MR=MRAF · CAUQ=Ensaio CAUQ")


def _grafico_por_profissional(df: pd.DataFrame):
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Registros por Profissional")
        cnt = (df.groupby(["profissional","tipo"]).size()
                  .reset_index(name="n"))
        profs_sorted = (df.groupby("profissional").size()
                           .sort_values().index.tolist())
        fig = go.Figure()
        for tipo, cor in _COR_TIPO.items():
            sub = cnt[cnt["tipo"] == tipo]
            sub = sub.set_index("profissional").reindex(profs_sorted, fill_value=0).reset_index()
            fig.add_trace(go.Bar(
                y=sub["profissional"], x=sub["n"],
                name=tipo, orientation="h",
                marker_color=cor,
                hovertemplate=f"<b>{tipo}</b><br>%{{y}}: %{{x}}<extra></extra>",
            ))
        fig.update_layout(
            **_BASE, barmode="stack",
            height=max(280, len(profs_sorted)*28+60),
            xaxis=dict(gridcolor=_C["grid"], title="Registros"),
            yaxis=dict(gridcolor=_C["grid"], tickfont=dict(size=10)),
            legend=dict(orientation="h", y=-0.25, font=dict(size=9)),
            title=dict(text="Total por profissional (empilhado por tipo)",
                       font=dict(size=12), x=0),
        )
        st.plotly_chart(fig, use_container_width=True, config=_NI)

    with col2:
        st.markdown("### ️ Registros por Categoria de Obra")
        cnt2 = (df.groupby(["obra","tipo"]).size()
                   .reset_index(name="n"))
        obras_sorted = (df.groupby("obra").size()
                           .sort_values().index.tolist())
        fig2 = go.Figure()
        for tipo, cor in _COR_TIPO.items():
            sub = cnt2[cnt2["tipo"] == tipo]
            sub = sub.set_index("obra").reindex(obras_sorted, fill_value=0).reset_index()
            fig2.add_trace(go.Bar(
                y=sub["obra"], x=sub["n"],
                name=tipo, orientation="h",
                marker_color=cor,
                hovertemplate=f"<b>{tipo}</b><br>%{{y}}: %{{x}}<extra></extra>",
            ))
        fig2.update_layout(
            **_BASE, barmode="stack",
            height=max(280, len(obras_sorted)*28+60),
            xaxis=dict(gridcolor=_C["grid"], title="Registros"),
            yaxis=dict(gridcolor=_C["grid"], tickfont=dict(size=10)),
            legend=dict(orientation="h", y=-0.25, font=dict(size=9)),
            title=dict(text="Total por categoria (empilhado por tipo)",
                       font=dict(size=12), x=0),
        )
        st.plotly_chart(fig2, use_container_width=True, config=_NI)


def _dias_sem_registro(df: pd.DataFrame):
    st.markdown("### ️ Dias Úteis SEM Registro por Profissional")
    if df.empty or df["data_dt"].isna().all():
        st.info("Sem dados.")
        return

    d_ini  = df["data_dt"].min().date()
    d_fim  = df["data_dt"].max().date()
    # Gera todos os dias úteis (seg-sex) no período
    todos  = pd.date_range(d_ini, d_fim, freq="B")  # B = business days
    datas_uteis = set(d.strftime("%Y-%m-%d") for d in todos)
    profs  = sorted(df["profissional"].unique())

    ausencias = []
    for prof in profs:
        datas_prof = set(df[df["profissional"] == prof]["data_iso"].unique())
        faltando   = sorted(datas_uteis - datas_prof)
        for d in faltando:
            ausencias.append({"Profissional": prof, "Data": d})

    if not ausencias:
        st.success("Nenhum dia útil sem registro no período!")
        return

    df_aus = pd.DataFrame(ausencias).sort_values(["Profissional","Data"])
    df_aus["Data"] = pd.to_datetime(df_aus["Data"]).dt.strftime("%d/%m/%Y")

    # Contagem por profissional
    cnt_aus = df_aus.groupby("Profissional").size().reset_index(name="Dias faltando")
    cnt_aus = cnt_aus.sort_values("Dias faltando", ascending=True)

    col_a, col_b = st.columns([1, 2])
    with col_a:
        fig_aus = go.Figure(go.Bar(
            x=cnt_aus["Dias faltando"], y=cnt_aus["Profissional"],
            orientation="h",
            marker=dict(
                color=cnt_aus["Dias faltando"],
                colorscale=[[0,"#1a3a1a"],[0.5,"#F7B731"],[1,"#FF6B6B"]],
                line_width=0,
            ),
            text=cnt_aus["Dias faltando"].astype(str) + " dias",
            textposition="outside",
            textfont=dict(size=10, color=_C["text"]),
            hovertemplate="<b>%{y}</b>: %{x} dias sem registro<extra></extra>",
        ))
        fig_aus.update_layout(
            **_BASE,
            title=dict(text="Dias úteis faltando", font=dict(size=12), x=0),
            height=max(220, len(cnt_aus)*30+60),
            xaxis=dict(gridcolor=_C["grid"], zeroline=False),
            yaxis=dict(gridcolor=_C["grid"], tickfont=dict(size=10)),
        )
        st.plotly_chart(fig_aus, use_container_width=True, config=_NI)

    with col_b:
        st.dataframe(
            df_aus.rename(columns={"Profissional":"Profissional","Data":"Data ausente"}),
            use_container_width=True, hide_index=True,
            height=min(400, len(df_aus)*35+50),
        )


def _tabela_com_links(df: pd.DataFrame):
    st.markdown("### Tabela Completa com Links")
    f1, f2, f3, f4 = st.columns(4)
    with f1:
        f_obra = st.multiselect("Categoria:", sorted(df["obra"].unique()), key="ens_obra")
    with f2:
        f_tipo = st.multiselect("Tipo:", sorted(df["tipo"].unique()), key="ens_tipo")
    with f3:
        f_prof = st.multiselect("Profissional:", sorted(df["profissional"].unique()), key="ens_prof")
    with f4:
        datas_disp = sorted(df["data_dt"].dropna().dt.date.unique(), reverse=True)
        f_data = st.date_input("De:", value=datas_disp[-1] if datas_disp else date.today(),
                               key="ens_dini")

    dv = df.copy()
    if f_obra: dv = dv[dv["obra"].isin(f_obra)]
    if f_tipo: dv = dv[dv["tipo"].isin(f_tipo)]
    if f_prof: dv = dv[dv["profissional"].isin(f_prof)]
    if f_data: dv = dv[dv["data_dt"].dt.date >= f_data]

    dv_show = dv[["data","profissional","tipo","obra","url_completa"]].copy()
    dv_show.columns = ["Data","Profissional","Tipo","Categoria","Link"]
    dv_show = dv_show.reset_index(drop=True)

    st.dataframe(
        dv_show,
        use_container_width=True,
        hide_index=True,
        height=min(600, len(dv_show)*35+60),
        column_config={
            "Link": st.column_config.LinkColumn("Abrir relatório", display_text="↗ Abrir"),
        },
    )
    st.caption(f"{len(dv_show)} registro(s) de {len(df)} total")


# =============================================================================
# VISUALIZAÇÃO: LISTA POR SERVIÇO → PESSOA → PDFS
# =============================================================================

_COR_GRUPO = {
    "SST":              "#e6194b",
    "Pavimento":        "#3cb44b",
    "Topografia":       "#ffe119",
    "OAE / Terraplenos":"#4363d8",
    "Escritório":       "#911eb4",
    "Conserva":         "#42d4f4",
}

_CSS_LISTA = """
<style>
.srv-grupo-hdr {
    font-family:'Poppins',sans-serif; font-size:1.1rem; font-weight:700;
    padding:10px 14px; border-radius:8px 8px 0 0; margin-top:18px; margin-bottom:0;
    letter-spacing:.04em; text-transform:uppercase;
}
.srv-pessoa-blk {
    background:rgba(255,255,255,.04); border:1px solid rgba(255,255,255,.08);
    border-radius:0 0 8px 8px; margin-bottom:14px; padding:10px 14px;
}
.srv-pessoa-nome {
    font-family:'Poppins',sans-serif; font-size:.88rem; font-weight:600;
    color:#E8EFD8; margin-bottom:6px;
}
.srv-pdf-link {
    display:block; font-family:'Inter',sans-serif; font-size:.78rem;
    padding:3px 0; text-decoration:none; border-bottom:1px solid rgba(255,255,255,.05);
}
.srv-pdf-link:last-child { border-bottom:none; }
.srv-status-ok   { color:#3cb44b; }
.srv-status-pend { color:#F7B731; }
.srv-status-rep  { color:#e6194b; }
.srv-badge {
    display:inline-block; font-size:.65rem; padding:1px 6px;
    border-radius:4px; margin-left:6px; vertical-align:middle; font-weight:600;
}
</style>
"""


def _render_lista_servico(df: "pd.DataFrame"):
    """
    Exibe PDFs organizados por:
      SERVIÇO (SST / Pavimento / Topografia / Escritório)
        └── PESSOA
              └── Tipo — Data [link] [status]
    """
    col_lab = "lab" if "lab" in df.columns else "profissional"
    df = df.copy()

    def _obra_para_grupo(obra: str) -> str:
        o = (obra or "").lower()
        if "sst" in o or "segurança" in o: return "SST"
        if "topo" in o: return "Topografia"
        if "escrit" in o: return "Escritório"
        if "oae" in o or "terraplan" in o: return "OAE / Terraplenos"
        if "conserva" in o: return "Conserva"
        return "Pavimento"

    df["_grupo"] = df["obra"].fillna("").apply(_obra_para_grupo)

    st.markdown(_CSS_LISTA, unsafe_allow_html=True)

    ordem = ["SST", "Pavimento", "Topografia", "OAE / Terraplenos", "Escritório", "Conserva"]

    for grupo in ordem:
        df_g = df[df["_grupo"] == grupo]
        if df_g.empty:
            continue

        cor = _COR_GRUPO.get(grupo, "#8FA882")
        total_g = len(df_g)

        st.markdown(
            f'<div class="srv-grupo-hdr" style="background:{cor}22;color:{cor};'
            f'border-left:4px solid {cor}">'
            f'🏷️ {grupo} &nbsp;<span style="font-size:.75rem;font-weight:400;opacity:.7">'
            f'({total_g} registros)</span></div>',
            unsafe_allow_html=True,
        )

        pessoas = sorted(df_g[col_lab].dropna().unique())
        html_blk = ['<div class="srv-pessoa-blk">']

        for i, pessoa in enumerate(pessoas):
            df_p = df_g[df_g[col_lab] == pessoa].sort_values("data_dt", ascending=False)
            total_p = len(df_p)

            if i > 0:
                html_blk.append('<hr style="margin:10px 0;border:none;border-top:1px solid rgba(255,255,255,.07)">')

            html_blk.append(
                f'<div class="srv-pessoa-nome">👤 {pessoa}'
                f'<span style="font-size:.72rem;color:#8FA882;font-weight:400;margin-left:8px">'
                f'{total_p} registro{"s" if total_p != 1 else ""}</span></div>'
            )

            for _, row in df_p.iterrows():
                data_lbl = str(row.get("data", ""))[:5]  # dd/mm
                tipo     = row.get("tipo", "—")
                status   = str(row.get("status", "")).lower()
                url      = row.get("url_completa", "#") or "#"

                if "aprovado" in status:
                    st_cls, st_lbl = "srv-status-ok",   "✓ Aprovado"
                elif "reprovado" in status:
                    st_cls, st_lbl = "srv-status-rep",  "✗ Reprovado"
                else:
                    st_cls, st_lbl = "srv-status-pend", "⏳ Pendente"

                html_blk.append(
                    f'<a class="srv-pdf-link {st_cls}" href="{url}" target="_blank">'
                    f'📄 {data_lbl} — {tipo}'
                    f'<span class="srv-badge" style="background:{cor}22;color:{cor}">{st_lbl}</span>'
                    f'</a>'
                )

        html_blk.append('</div>')
        st.markdown("".join(html_blk), unsafe_allow_html=True)


# =============================================================================
# ENTRADA PRINCIPAL
# =============================================================================

_CSS_TABELA = """
<style>
.do-wrap{padding:0 2px}
.do-table{border-collapse:collapse;font-size:.68rem;font-family:Inter,sans-serif;width:100%;min-width:600px}
.do-table th{
  background:rgba(86,110,61,.2);color:#BFCF99;padding:4px 3px;
  text-align:center;font-weight:600;border:1px solid rgba(86,110,61,.15);
  font-size:.6rem;white-space:nowrap
}
.do-table td{
  padding:5px 3px;border:1px solid rgba(255,255,255,.05);
  text-align:center;white-space:nowrap;font-size:0.65rem;
}
.do-table td.do-nome{
  text-align:left;font-weight:600;color:#E8EFD8;padding-left:8px;
  min-width:140px;max-width:200px;white-space:normal;
  vertical-align:middle;line-height:1.2
}
.do-nome-cargo{font-size:.55rem;color:#8FA882;font-weight:400;
  display:block;margin-top:1px;white-space:nowrap;
  overflow:hidden;text-overflow:ellipsis;max-width:196px}
.do-pend{background:rgba(230,25,75,.2);color:#ff5577;font-weight:700}
.do-ok{background:rgba(60,180,75,.2);color:#3cb44b;font-weight:700}
.do-rep{background:rgba(230,25,75,.3);color:#e6194b;font-weight:700}
.do-vazio{color:#3a4a5e;background:transparent}
.do-hj{outline:2px solid #F7B731 !important;outline-offset:-1px}
.do-wrap-scroll{overflow-x:auto;-webkit-overflow-scrolling:touch;width:100%}
</style>
"""

def _render_por_frente_servico(df):
    """
    Agrupa os ensaios por Frente de Servico (SST / Pavimento / Topografia / Escritório)
    usando o modelo de tabela do Diário de Obra (Versão Limpa).
    """
    from collections import defaultdict
    col_lab = "lab" if "lab" in df.columns else ("profissional" if "profissional" in df.columns else None)
    if col_lab is None:
        st.warning("Campo de profissional nao encontrado.")
        return

    today = date.today()
    today_str = today.strftime("%Y-%m-%d")

    def _obra_para_grupo(obra: str) -> str:
        o = (obra or "").lower()
        if "sst" in o or "segurança" in o or "seguranca" in o: return "SST"
        if "topografia" in o: return "Topografia"
        if "escritório" in o or "escritorio" in o: return "Escritório"
        return "Pavimento"

    df = df.copy()
    df["_grupo"] = df["obra"].fillna("").apply(_obra_para_grupo) if "obra" in df.columns else "Pavimento"
    df["_dstr"]  = df["data_dt"].dt.strftime("%Y-%m-%d").fillna("")

    def _norm_status(s):
        s = str(s or "").lower()
        if "aprovado" in s: return "do-ok", "OK"
        if "reprovado" in s: return "do-rep", "REP"
        return "do-pend", "PND"
    df["_status"] = df["status"].fillna("").apply(_norm_status) if "status" in df.columns else [("do-pend", "PND")] * len(df)

    datas = sorted([d for d in df["_dstr"].unique() if d and d <= today_str])
    _DAY_ABBR = {0:"SEG",1:"TER",2:"QUA",3:"QUI",4:"SEX",5:"SÁB",6:"DOM"}

    st.markdown(_CSS_TABELA, unsafe_allow_html=True)

    for grupo in ORDEM_GRUPOS:
        df_g = df[df["_grupo"] == grupo]
        if df_g.empty: continue

        st.markdown(header_grupo(grupo), unsafe_allow_html=True)
        labs = sorted(df_g[col_lab].dropna().unique())

        html = ['<div class="do-wrap-scroll"><table class="do-table">']
        html.append('<thead><tr><th>Profissional</th>')
        for d in datas:
            dt = datetime.strptime(d, "%Y-%m-%d")
            is_hj = (d == today_str)
            sty = "color:#F7B731;font-weight:700" if is_hj else ""
            lbl = "HOJE" if is_hj else f"{dt.day:02d}"
            sub = _DAY_ABBR[dt.weekday()]
            html.append(f'<th style="{sty}">{lbl}<br>{sub}</th>')
        html.append('<th>Total</th></tr></thead><tbody>')

        for lab in labs:
            df_lab = df_g[df_g[col_lab] == lab]
            total_lab = len(df_lab)
            
            # Tenta pegar função se houver
            funcao = df_lab["funcao"].iloc[0] if "funcao" in df_lab.columns else ""
            cargo_html = f'<span class="do-nome-cargo">{funcao}</span>' if funcao else ""
            
            html.append(f'<tr><td class="do-nome">{lab}{cargo_html}</td>')
            
            for d in datas:
                is_hj = (d == today_str)
                hj_cls = " do-hj" if is_hj else ""
                recs_dia = df_lab[df_lab["_dstr"] == d]
                
                if recs_dia.empty:
                    html.append(f'<td class="do-vazio{hj_cls}">—</td>')
                else:
                    # Pega pior status do dia para colorir a célula
                    statuses = recs_dia["_status"].tolist()
                    st_classes = [s[0] for s in statuses]
                    st_labels  = [s[1] for s in statuses]
                    
                    pior_cls = ("do-rep" if "do-rep" in st_classes 
                                else "do-pend" if "do-pend" in st_classes 
                                else "do-ok")
                    
                    n = len(recs_dia)
                    lbl_cel = f"{n}" if n > 1 else st_labels[0]

                    tooltip = " | ".join(f"{t} - {o}" for t, o in zip(recs_dia["tipo"], recs_dia["obra"]))
                    if n == 1 and "url_completa" in recs_dia.columns:
                        _url = recs_dia["url_completa"].iloc[0]
                        html.append(f'<td class="{pior_cls}{hj_cls}" title="{tooltip}"><a href="{_url}" target="_blank" style="color:inherit;text-decoration:none;display:block">{lbl_cel}</a></td>')
                    else:
                        html.append(f'<td class="{pior_cls}{hj_cls}" title="{tooltip}">{lbl_cel}</td>')
            
            html.append(f'<td style="color:#8FA882;font-weight:600">{total_lab}</td></tr>')

        html.append('</tbody></table></div>')
        st.markdown("".join(html), unsafe_allow_html=True)

        # ── Expander de relatórios logo abaixo da tabela do mesmo grupo ──────
        with st.expander(
            f"Relatórios — {GRUPOS[grupo]['label']} ({len(labs)} pessoas)",
            expanded=False,
        ):
            for lab in labs:
                df_p = df_g[df_g[col_lab] == lab].sort_values("data_dt")
                st.markdown(
                    f'<div style="font-weight:700;color:#E8EFD8;font-family:Inter,sans-serif;'
                    f'font-size:.9rem;margin:10px 0 4px 0">{lab}</div>',
                    unsafe_allow_html=True,
                )
                _lines = []
                for _, row in df_p.iterrows():
                    d_lbl = row["data"][:5] if row.get("data") else "—"
                    _obra = row.get("obra", "—")
                    _stat = str(row.get("status", "")).lower()
                    _url  = row.get("url_completa", "#")
                    _clr  = "#FF6B6B" if "reprovado" in _stat or "pendente" in _stat else "#3cb44b"
                    _slbl = "Reprovado" if "reprovado" in _stat else ("Pendente" if "pendente" in _stat else "Aprovado")
                    _lines.append(
                        f'<a href="{_url}" target="_blank" '
                        f'style="display:block;color:{_clr};font-size:.82rem;'
                        f'padding:3px 2px;text-decoration:none;font-family:Inter,sans-serif;">'
                        f'{d_lbl} — {_obra} ({_slbl})</a>'
                    )
                st.markdown("".join(_lines), unsafe_allow_html=True)
                st.markdown(
                    "<hr style='margin:8px 0;border:none;border-top:1px solid rgba(255,255,255,.07)'>",
                    unsafe_allow_html=True,
                )


def _render_relatorios_expanders(df: "pd.DataFrame"):
    """Expanders 'Relatórios — [Grupo] (N pessoas)' com links clicáveis."""
    col_lab = "lab" if "lab" in df.columns else ("profissional" if "profissional" in df.columns else None)
    if col_lab is None or df.empty:
        return

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    def _obra_para_grupo(obra):
        o = (obra or "").upper()
        if o == "SST": return "SST"
        if "TOPOGRAFIA" in o: return "Topografia"
        if "ESCRIT" in o: return "Escritório"
        return "Pavimento"

    df = df.copy()
    df["_egrp"] = df["obra"].fillna("").apply(_obra_para_grupo) if "obra" in df.columns else "Pavimento"

    for grupo in ORDEM_GRUPOS:
        df_g = df[df["_egrp"] == grupo]
        if df_g.empty:
            continue
        g_info = GRUPOS[grupo]
        profs = sorted(df_g[col_lab].dropna().unique())

        with st.expander(
            f"Relatórios — {g_info['label']} ({len(profs)} pessoas)",
            expanded=True,
        ):
            for prof in profs:
                df_p = df_g[df_g[col_lab] == prof].sort_values("data_dt")
                st.markdown(
                    f'<div style="font-weight:700;color:#E8EFD8;font-family:Inter,sans-serif;'
                    f'font-size:.9rem;margin:10px 0 4px 0">{prof}</div>',
                    unsafe_allow_html=True,
                )
                lines = []
                for _, row in df_p.iterrows():
                    d_lbl = row["data"][:5] if row.get("data") else "—"
                    obra  = row.get("obra", "—")
                    stat  = str(row.get("status", "")).lower()
                    url   = row.get("url_completa", "#")
                    clr   = "#FF6B6B" if "reprovado" in stat or "pendente" in stat else "#3cb44b"
                    slbl  = "Reprovado" if "reprovado" in stat else ("Pendente" if "pendente" in stat else "Aprovado")
                    lines.append(
                        f'<a href="{url}" target="_blank" '
                        f'style="display:block;color:{clr};font-size:.82rem;'
                        f'padding:3px 2px;text-decoration:none;font-family:Inter,sans-serif;">'
                        f'{d_lbl} — {obra} ({slbl})</a>'
                    )
                st.markdown("".join(lines), unsafe_allow_html=True)
                st.markdown(
                    "<hr style='margin:8px 0;border:none;border-top:1px solid rgba(255,255,255,.07)'>",
                    unsafe_allow_html=True,
                )


def _aba_ensaios():
    try:
        st.image("Imagens/AE - Logo Hor Principal_2.png", width=220)
    except:
        pass

    # ── Cabeçalho + botão Atualizar ───────────────────────────────────────────
    c_titulo, c_btn = st.columns([6, 1])
    with c_titulo:
        st.markdown("## Ensaios AEVIAS — Dashboard de Produção")
        _ti = _b44_token_info()
        if _ti.get("expirado"):
            st.warning("⚠️ Token Base44 expirado. Atualize `base44_token` nos secrets do Streamlit Cloud.")
        else:
            st.caption(
                f"⚡ Dados em tempo real via API Base44 · "
                f"[aevias-controle.base44.app]({_AEVIAS_BASE}) · "
                f"Token válido por {_ti.get('dias_restantes', '?')} dias"
            )

    with c_btn:
        st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
        if st.button("↺ Atualizar", key="ens_atualizar", use_container_width=True,
                     help="Limpa o cache e busca dados atualizados da API"):
            st.cache_data.clear()
            st.rerun()

    # ── Carga dos dados via API ────────────────────────────────────────────────
    _mtime = None
    with st.spinner("Carregando dados da API Base44..."):
        dados = _carregar_ensaios_api()
        if dados:
            _mtime = datetime.now().strftime("%d/%m/%Y %H:%M")

    if not dados:
        # Fallback para JSON local/cache
        dados = _carregar_ensaios()
        if dados:
            _mtime = "cache local"

    if not dados:
        st.warning("Nenhum dado encontrado. Verifique a conexão com a API Base44 ou o token.")
        return

    df = _df_ensaios(dados)

    # ── Exclui Diário de Obra (tem aba própria) e dados antes de 01/03 ─────────
    _DATA_MIN = date(2026, 3, 1)
    df = df[df["tipo"] != "Diário de Obra"]
    if "data_dt" in df.columns:
        df = df[df["data_dt"].dt.date >= _DATA_MIN]

    # ── Filtro 1: Mês ─────────────────────────────────────────────────────────
    dts_valid = df["data_dt"].dropna()
    if not dts_valid.empty:
        meses_disp = (
            dts_valid.dt.to_period("M")
            .drop_duplicates()
            .sort_values(ascending=False)
        )
        _MESES_PT = {1:"Jan",2:"Fev",3:"Mar",4:"Abr",5:"Mai",6:"Jun",
                     7:"Jul",8:"Ago",9:"Set",10:"Out",11:"Nov",12:"Dez"}
        opcoes_mes = {f"{_MESES_PT[p.month]}/{p.year}": p for p in meses_disp}
        col_mes, col_obra, col_prof = st.columns([2, 2, 2])
        with col_mes:
            mes_sel_lbl = st.selectbox("Mes:", list(opcoes_mes.keys()), key="ens_mes_sel")
        per_sel = opcoes_mes[mes_sel_lbl]
        d_ini_g = per_sel.to_timestamp().date()
        d_fim_g = (per_sel + 1).to_timestamp().date() - timedelta(days=1)
        df = df[(df["data_dt"].dt.date >= d_ini_g) & (df["data_dt"].dt.date <= d_fim_g)]

        # ── Filtro 2: Tipo de Obra ─────────────────────────────────────────────
        obras_disp = sorted(df["obra"].dropna().unique().tolist()) if "obra" in df.columns else []
        with col_obra:
            obra_sel = st.selectbox("Tipo de Obra:", ["Todas"] + obras_disp, key="ens_obra_sel")
        if obra_sel != "Todas":
            df = df[df["obra"] == obra_sel]

        # ── Filtro 3: Profissional ─────────────────────────────────────────────
        col_lab = "lab" if "lab" in df.columns else ("profissional" if "profissional" in df.columns else None)
        profs_disp = sorted(df[col_lab].dropna().unique().tolist()) if col_lab else []
        with col_prof:
            prof_sel = st.selectbox("Profissional:", ["Todos"] + profs_disp, key="ens_prof_sel")
        if prof_sel != "Todos" and col_lab:
            df = df[df[col_lab] == prof_sel]

    if df.empty:
        st.info("Nenhum registro no filtro selecionado.")
        return

    # ── Cards de resumo ────────────────────────────────────────────────────────
    _cards_resumo(df, _mtime or "—")

    # ── Lista por Serviço → Pessoa → PDFs ────────────────────────────────────
    st.markdown("---")
    _render_lista_servico(df)

    # ── Exportar Todos ────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### Exportar Todos os Registros")

    if st.button(
        "Gerar PDF  —  Diário de Obra · Segurança do Trabalho · Pavimento",
        key="btn_gerar_pdf_ensaios",
        use_container_width=True,
    ):
        _dados_full = _carregar_ensaios()
        if not _dados_full:
            st.warning("Nenhum dado disponível para exportação.")
        else:
            import io as _io
            _df_full = _df_ensaios(_dados_full)

            def _gerar_pdf_seg(_df: pd.DataFrame) -> bytes:
                from reportlab.lib.pagesizes import A4, landscape as _ls
                from reportlab.lib import colors as _clr
                from reportlab.lib.units import cm
                from reportlab.lib.styles import ParagraphStyle as _PS
                from reportlab.platypus import (
                    SimpleDocTemplate, Table, TableStyle,
                    Paragraph, Spacer, HRFlowable,
                )
                _CINZA  = _clr.HexColor("#F5F5F5")
                _BRANCO = _clr.white
                _VERDE  = _clr.HexColor("#566E3D")
                _MUTED  = _clr.HexColor("#555555")
                _TEXTO  = _clr.HexColor("#1A1A2E")
                _s_t = _PS("t", fontName="Helvetica-Bold", fontSize=14,
                            textColor=_clr.HexColor("#1A3A1A"), spaceAfter=4)
                _s_s = _PS("s", fontName="Helvetica",      fontSize=8,
                            textColor=_MUTED, spaceAfter=10)
                _s_h = _PS("h", fontName="Helvetica-Bold", fontSize=7.5,
                            textColor=_clr.white)
                _s_c = _PS("c", fontName="Helvetica",      fontSize=7,
                            textColor=_TEXTO, leading=9)
                def _ss(h): return _PS("sec", fontName="Helvetica-Bold", fontSize=11,
                                        textColor=_clr.HexColor(h), spaceBefore=12, spaceAfter=4)
                def _tbl(dseg, ch):
                    if dseg.empty:
                        return Paragraph("<i>Sem registros.</i>",
                                         _PS("e", fontName="Helvetica-Oblique",
                                             fontSize=8, textColor=_MUTED))
                    hdr  = [Paragraph(t, _s_h)
                            for t in ["Data", "Profissional", "Tipo", "Categoria", "Status"]]
                    rows = [hdr] + [[
                        Paragraph(str(r.get("data",         "—")), _s_c),
                        Paragraph(str(r.get("profissional", "—")), _s_c),
                        Paragraph(str(r.get("tipo",         "—")), _s_c),
                        Paragraph(str(r.get("obra",         "—")), _s_c),
                        Paragraph(str(r.get("status",       "—")), _s_c),
                    ] for _, r in dseg.iterrows()]
                    t = Table(rows,
                              colWidths=[2.2*cm, 5.5*cm, 5.5*cm, 4.5*cm, 3.5*cm],
                              repeatRows=1)
                    t.setStyle(TableStyle([
                        ("BACKGROUND",    (0, 0), (-1,  0), _clr.HexColor(ch)),
                        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [_BRANCO, _CINZA]),
                        ("GRID",          (0, 0), (-1, -1), 0.3, _clr.HexColor("#CCCCCC")),
                        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
                        ("TOPPADDING",    (0, 0), (-1, -1), 3),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
                        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
                    ]))
                    return t
                m_do  = _df["tipo"] == "Diário de Obra"
                m_sst = _df["obra"].str.upper() == "SST"
                segs  = [
                    ("Diário de Obra",        _df[ m_do],           "#4CC9F0"),
                    ("Segurança do Trabalho", _df[ m_sst],          "#FFB347"),
                    ("Pavimento",             _df[~m_do & ~m_sst],  "#7BBF6A"),
                ]
                buf = _io.BytesIO()
                doc = SimpleDocTemplate(buf, pagesize=_ls(A4),
                                        leftMargin=1.5*cm, rightMargin=1.5*cm,
                                        topMargin=1.5*cm,  bottomMargin=1.5*cm,
                                        title="ECO Rodovias — Ensaios AEVIAS")
                story = [
                    Paragraph("ECO Rodovias — Ensaios AEVIAS", _s_t),
                    Paragraph(
                        f"Gerado em {date.today().strftime('%d/%m/%Y')}  ·  "
                        f"{len(_df)} registros  ·  "
                        "Diário de Obra  ·  Segurança do Trabalho  ·  Pavimento",
                        _s_s,
                    ),
                    HRFlowable(width="100%", thickness=1, color=_VERDE, spaceAfter=8),
                ]
                for sn, ds, ch in segs:
                    story += [Paragraph(f"{sn}  ({len(ds)} registro(s))", _ss(ch)),
                              _tbl(ds, ch), Spacer(1, 0.4*cm)]
                doc.build(story)
                return buf.getvalue()

            with st.spinner("Gerando PDF..."):
                try:
                    _pdf_bytes = _gerar_pdf_seg(_df_full)
                    st.session_state["_pdf_ensaios_bytes"] = _pdf_bytes
                    st.session_state["_pdf_ensaios_nome"]  = (
                        f"ensaios_eco_{date.today().strftime('%Y-%m-%d')}.pdf"
                    )
                except Exception as _err:
                    st.error(f"Erro ao gerar PDF: {_err}")

    if st.session_state.get("_pdf_ensaios_bytes"):
        st.download_button(
            label="⬇ Baixar PDF",
            data=st.session_state["_pdf_ensaios_bytes"],
            file_name=st.session_state.get("_pdf_ensaios_nome", "ensaios_eco.pdf"),
            mime="application/pdf",
            use_container_width=True,
            key="btn_download_pdf_ensaios",
        )
        st.caption("PDF com 3 seções: Diário de Obra · Segurança do Trabalho · Pavimento")
