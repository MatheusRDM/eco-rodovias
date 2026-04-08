"""
_eco_funcoes.py
Correlação de funções → grupos de trabalho (SST / Pavimento / Topografia / Escritório).
Importado por todas as abas de Eco Rodovias.
"""

# ---------------------------------------------------------------------------
# Grupos e suas propriedades visuais
# ---------------------------------------------------------------------------
GRUPOS = {
    "SST": {
        "label": "Segurança do Trabalho",
        "cor": "#FFB347",
        "bg": "#2A1F0A",
        "borda": "#FFB347",
        "icone": "SST",
    },
    "Pavimento": {
        "label": "Pavimento",
        "cor": "#4CC9F0",
        "bg": "#0A1A2A",
        "borda": "#4CC9F0",
        "icone": "PAV",
    },
    "Topografia": {
        "label": "Topografia",
        "cor": "#7BBF6A",
        "bg": "#0F1F0F",
        "borda": "#7BBF6A",
        "icone": "TOP",
    },
    "Escritório": {
        "label": "Escritório / Engenharia",
        "cor": "#A29BFE",
        "bg": "#1A1030",
        "borda": "#A29BFE",
        "icone": "ESC",
    },
}

# Ordem de exibição dos grupos
ORDEM_GRUPOS = ["SST", "Pavimento", "Topografia", "Escritório"]

# ---------------------------------------------------------------------------
# Palavras-chave por grupo (case-insensitive, busca parcial)
# ---------------------------------------------------------------------------
_KW_SST = [
    "segurança", "seguranca", "sst", "cipa", "saúde ocupacional",
    "saude ocupacional", "prevenção", "prevencao",
]
_KW_TOPOGRAFIA = [
    "topógrafo", "topografo", "topografia", "auxiliar de topografia",
]
_KW_ESCRITORIO = [
    "desenhista", "engenheiro sala", "assistente de engenharia",
    "assistente de eng", "escritório", "escritorio", "administrativo",
    "auxiliar administrativo",
]

# Pavimento = tudo que não se encaixa nos acima
_KW_PAVIMENTO = [
    "laboratorista", "laboratório", "laboratorio",
    "técnico de obras", "tecnico de obras",
    "técnico de campo", "tecnico de campo",
    "encarregado", "auxiliar geral", "fabrica de placas",
    "auxiliar de obras",
]


def cargo_para_grupo(cargo: str) -> str:
    """
    Recebe o cargo/funcao de um colaborador e retorna o grupo (SST, Pavimento,
    Topografia ou Escritório). Retorna 'Pavimento' como fallback.
    """
    if not cargo:
        return "Pavimento"
    c = cargo.lower().strip()
    for kw in _KW_SST:
        if kw in c:
            return "SST"
    for kw in _KW_TOPOGRAFIA:
        if kw in c:
            return "Topografia"
    for kw in _KW_ESCRITORIO:
        if kw in c:
            return "Escritório"
    return "Pavimento"


def grupo_permite_tipo(grupo: str, tipo_registro: str) -> bool:
    """
    Valida se um grupo pode gerar determinado tipo de registro.

    Regras:
    - SST          → somente registros de SST (nao faz checklist de usina, etc.)
    - Laboratorista/Pavimento → nao faz registro SST
    - Topografia   → nao faz registro SST
    - Escritório   → pode visualizar tudo, mas nao faz ensaios de campo
    """
    t = (tipo_registro or "").lower()
    if grupo == "SST":
        return "sst" in t or "segurança" in t or "seguranca" in t or "safety" in t
    if grupo in ("Pavimento", "Topografia", "Escritório"):
        # Nao pode fazer registro SST
        return "sst" not in t and "segurança" not in t and "seguranca" not in t
    return True


def enriquecer_df(df, col_cargo: str = "funcao", col_grupo: str = "grupo"):
    """
    Adiciona coluna 'grupo' a um DataFrame baseado na coluna de cargo.
    Retorna o DataFrame modificado.
    """
    import pandas as pd
    if col_cargo in df.columns:
        df[col_grupo] = df[col_cargo].fillna("").apply(cargo_para_grupo)
    else:
        df[col_grupo] = "Pavimento"
    return df


def badge_grupo(grupo: str, tamanho: str = ".65rem") -> str:
    """Retorna HTML de um badge colorido para o grupo."""
    g = GRUPOS.get(grupo, GRUPOS["Pavimento"])
    return (
        f'<span style="background:{g["bg"]};color:{g["cor"]};border:1px solid {g["borda"]}22;'
        f'font-size:{tamanho};border-radius:4px;padding:1px 6px;font-weight:600;'
        f'font-family:Inter,sans-serif">{g["icone"]}</span>'
    )


def header_grupo(grupo: str) -> str:
    """Retorna HTML do cabeçalho de seção de grupo."""
    g = GRUPOS.get(grupo, GRUPOS["Pavimento"])
    return (
        f'<div style="border-left:4px solid {g["cor"]};padding:4px 0 4px 12px;'
        f'margin:16px 0 8px 0;background:{g["bg"]};border-radius:0 6px 6px 0">'
        f'<span style="color:{g["cor"]};font-weight:700;font-size:.9rem;'
        f'font-family:Inter,sans-serif">{g["label"]}</span></div>'
    )
