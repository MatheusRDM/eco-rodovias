# -*- coding: utf-8 -*-
"""
_eco_colaboradores.py
=====================
Mapeamento completo dos colaboradores ECO Rodovias → concessão, cargo,
N. Folha, placa Logos e variantes de nome para correlação entre abas.

Concessões:
  CERRADO  → ECO Cerrado (ECO050/CERRADO) — BR-365 / Uberlândia-MG, GO
  MINAS    → ECO Minas Goiás              — BR-050 / Catalão-GO, Uberlândia-MG
  ECO135   → ECO-135 (outro contrato no Logos)

Logos usa nomes curtos (ex: "HUDSON BERNARDES") — campo 'logos_nome'.
PontoMais usa nomes completos — campo 'nome'.
Checklist pode usar variações — campo 'variantes'.
"""

from __future__ import annotations
import re
import unicodedata

# ---------------------------------------------------------------------------
# Tabela mestre de colaboradores
# ---------------------------------------------------------------------------
# Campos:
#   nome        → nome completo (padrão PontoMais)
#   concessao   → "CERRADO" | "MINAS" | "ECO135" | ""
#   cargo       → cargo/função
#   n_folha     → número de folha (int ou 0)
#   grupo       → SST | Pavimento | Topografia | Escritório
#   placa       → placa Logos (sem hífen, maiúscula) ou ""
#   logos_nome  → sobrenome/apelido usado no Logos (maiúscula parcial)
#   logos_id    → id do veículo no Logos (pos_idvei) ou 0
#   cidade      → cidade/região de atuação
#   variantes   → lista de grafias alternativas do nome

COLABORADORES: list[dict] = [

    # ── ECO CERRADO — Obras / Pavimento / Topografia ─────────────────────────
    {
        "nome":       "Clayton Marciano da Silva",
        "concessao":  "CERRADO",
        "cargo":      "Técnico de obras",
        "n_folha":    0,
        "grupo":      "Pavimento",
        "placa":      "STX0A31",
        "logos_nome": "CLAYTON",
        "logos_id":   0,
        "cidade":     "São Simão/GO",
        "variantes":  ["Clayton Marciano", "Clayton M. Silva"],
    },
    {
        "nome":       "Danilo Ramos Carvalho",
        "concessao":  "CERRADO",
        "cargo":      "Assistente de engenharia",
        "n_folha":    951,
        "grupo":      "Escritório",
        "placa":      "",
        "logos_nome": "DANILO RAMOS",
        "logos_id":   0,
        "cidade":     "Uberlândia/MG",
        "variantes":  ["Danilo R. Carvalho"],
    },
    {
        "nome":       "David Brendon S. Barbosa",
        "concessao":  "CERRADO",
        "cargo":      "Laboratorista",
        "n_folha":    0,
        "grupo":      "Pavimento",
        "placa":      "SEQ2J11",
        "logos_nome": "DAVID BRENO",
        "logos_id":   43797,
        "cidade":     "São Simão/GO",
        "variantes":  ["David Brendon Barbosa", "David Breno", "David B. Barbosa"],
    },
    {
        "nome":       "Hudson Bernardes Borges",
        "concessao":  "CERRADO",
        "cargo":      "Técnico de obras",
        "n_folha":    945,
        "grupo":      "Pavimento",
        "placa":      "TBR5G92",
        "logos_nome": "HUDSON BERNARDES",
        "logos_id":   48317,
        "cidade":     "Tupaciguara/MG",
        "variantes":  ["Hudson B. Borges", "Hudson Bernardes"],
    },
    {
        "nome":       "Jony Alves de Queiroz",
        "concessao":  "CERRADO",
        "cargo":      "Topógrafo",
        "n_folha":    944,
        "grupo":      "Topografia",
        "placa":      "TCP3H70",
        "logos_nome": "JONY QUEIROZ",
        "logos_id":   0,
        "cidade":     "Tupaciguara/MG",
        "variantes":  ["Jony A. Queiroz", "Jony Alves Queiroz"],
    },
    {
        "nome":       "Maria Clara Simões Cavecchia",
        "concessao":  "CERRADO",
        "cargo":      "Assistente de engenharia",
        "n_folha":    0,
        "grupo":      "Escritório",
        "placa":      "",
        "logos_nome": "MARIA CLARA",
        "logos_id":   0,
        "cidade":     "Uberlândia/MG",
        "variantes":  ["Maria Clara Cavecchia", "Maria Clara S. Cavecchia"],
    },
    {
        "nome":       "Mariana Odilia Souza",
        "concessao":  "CERRADO",
        "cargo":      "Técnico de obras",
        "n_folha":    955,
        "grupo":      "Pavimento",
        "placa":      "TBR5G85",
        "logos_nome": "MARIANA ODILIA",
        "logos_id":   48312,
        "cidade":     "Tupaciguara/MG",
        "variantes":  ["Mariana O. Souza"],
    },
    {
        "nome":       "Mariane de Paula Santos",
        "concessao":  "CERRADO",
        "cargo":      "Assistente de pessoas",
        "n_folha":    320,
        "grupo":      "Escritório",
        "placa":      "",
        "logos_nome": "MARIANE SANTOS",
        "logos_id":   0,
        "cidade":     "Uberlândia/MG",
        "variantes":  ["Mariane P. Santos"],
    },
    {
        "nome":       "Renato Nogueira dos Reis",
        "concessao":  "CERRADO",
        "cargo":      "Auxiliar de topografia",
        "n_folha":    938,
        "grupo":      "Topografia",
        "placa":      "",
        "logos_nome": "RENATO NOGUEIRA",
        "logos_id":   0,
        "cidade":     "Tupaciguara/MG",
        "variantes":  ["Renato N. Reis", "Renato Nogueira Reis"],
    },
    {
        "nome":       "Rhjan Victor Silva Soares",
        "concessao":  "CERRADO",
        "cargo":      "Auxiliar de laboratório",
        "n_folha":    938,
        "grupo":      "Pavimento",
        "placa":      "",
        "logos_nome": "RHJAN VICTOR",
        "logos_id":   0,
        "cidade":     "Tupaciguara/MG",
        "variantes":  ["Rhjan V. Soares", "Rhjan Victor Soares"],
    },
    {
        "nome":       "Suellen Carita S. A. Gomes",
        "concessao":  "CERRADO",
        "cargo":      "Assistente de engenharia",
        "n_folha":    0,
        "grupo":      "Escritório",
        "placa":      "",
        "logos_nome": "SUELLEN GOMES",
        "logos_id":   0,
        "cidade":     "Uberlândia/MG",
        "variantes":  ["Suellen Carita Gomes", "Suellen C. Gomes"],
    },
    {
        "nome":       "Thierry da Silva",
        "concessao":  "CERRADO",
        "cargo":      "Laboratorista",
        "n_folha":    941,
        "grupo":      "Pavimento",
        "placa":      "TBR5G61",
        "logos_nome": "THIERRY DA SILVA",
        "logos_id":   48412,
        "cidade":     "Tupaciguara/MG",
        "variantes":  ["Thierry Silva"],
    },
    {
        "nome":       "Warlton Ferreira Lima Sobrinho",
        "concessao":  "CERRADO",
        "cargo":      "Técnico de obras",
        "n_folha":    0,
        "grupo":      "Pavimento",
        "placa":      "TBU6F93",
        "logos_nome": "WARITON FERREIRA",
        "logos_id":   48444,
        "cidade":     "Tupaciguara/MG",
        "variantes":  ["Wariton Ferreira Lima", "Warlton F. Lima Sobrinho", "Wariton Sobrinho"],
    },
    {
        "nome":       "Ademar Dutra",
        "concessao":  "CERRADO",
        "cargo":      "Técnico de obras",
        "n_folha":    0,
        "grupo":      "Pavimento",
        "placa":      "TBR5G89",
        "logos_nome": "ADEMAR DUTRA",
        "logos_id":   48313,
        "cidade":     "Tupaciguara/MG",
        "variantes":  ["Ademar Dutra"],
    },

    # ── ECO CERRADO — SST ────────────────────────────────────────────────────
    {
        "nome":       "Ana Paula Xavier da Silva Martins",
        "concessao":  "CERRADO",
        "cargo":      "Técnico de Segurança",
        "n_folha":    0,
        "grupo":      "SST",
        "placa":      "TAI6B63",
        "logos_nome": "ANA PAULA MARTINS",
        "logos_id":   46603,
        "cidade":     "Uberlândia/MG",
        "variantes":  ["Ana Paula Martins", "Ana Paula X. Martins", "Ana Paula Xavier Martins"],
    },
    {
        "nome":       "Anderson Esteves da Fonseca",
        "concessao":  "CERRADO",
        "cargo":      "Técnico de Segurança",
        "n_folha":    956,
        "grupo":      "SST",
        "placa":      "TBR5G91",
        "logos_nome": "ANDERSON FONSECA",
        "logos_id":   48316,
        "cidade":     "Uberlândia/MG",
        "variantes":  ["Anderson E. Fonseca", "Anderson Esteves Fonseca"],
    },
    {
        "nome":       "Fernanda De Jesus Oliveira",
        "concessao":  "CERRADO",
        "cargo":      "Técnico de Segurança",
        "n_folha":    0,
        "grupo":      "SST",
        "placa":      "TKG7H42",
        "logos_nome": "FERNANDA OLIVEIRA",
        "logos_id":   0,
        "cidade":     "São Simão/GO",
        "variantes":  ["Fernanda J. Oliveira", "Fernanda De Jesus"],
    },
    {
        "nome":       "Gustavo Franco de Lima",
        "concessao":  "CERRADO",
        "cargo":      "Técnico de Segurança",
        "n_folha":    970,
        "grupo":      "SST",
        "placa":      "TBR5G88",
        "logos_nome": "GUSTAVO FRANCO",
        "logos_id":   48315,
        "cidade":     "Santa Vitória/MG",
        "variantes":  ["Gustavo F. Lima", "Gustavo Franco Lima"],
    },
    {
        "nome":       "Josiane Ferreira da Silva",
        "concessao":  "CERRADO",
        "cargo":      "Técnico de monitoramento",
        "n_folha":    976,
        "grupo":      "SST",
        "placa":      "",
        "logos_nome": "JOSIANE SILVA",
        "logos_id":   0,
        "cidade":     "Uberlândia/MG",
        "variantes":  ["Josiane F. Silva"],
    },

    # ── ECO MINAS GOIÁS — Obras / Pavimento / Topografia ────────────────────
    {
        "nome":       "Valmir Gomes da Silva",
        "concessao":  "MINAS",
        "cargo":      "Técnico de obras",
        "n_folha":    928,
        "grupo":      "Pavimento",
        "placa":      "TBR5G60",
        "logos_nome": "VALMIR GOMES",
        "logos_id":   48359,
        "cidade":     "Catalão/GO",
        "variantes":  ["Valmir G. Silva", "Valmir Gomes Silva"],
    },
    {
        "nome":       "Matheus Alves Da Silva",
        "concessao":  "MINAS",
        "cargo":      "Topógrafo",
        "n_folha":    935,
        "grupo":      "Topografia",
        "placa":      "TLC2D85",
        "logos_nome": "MATHEUS ALVES",
        "logos_id":   0,
        "cidade":     "Catalão/GO",
        "variantes":  ["Matheus Alves Silva", "Matheus A. Silva"],
    },
    {
        "nome":       "Samuel Elias Magalhães",
        "concessao":  "MINAS",
        "cargo":      "Topógrafo",
        "n_folha":    0,
        "grupo":      "Topografia",
        "placa":      "UBC4A87",
        "logos_nome": "SAMUEL MAGALHAES",
        "logos_id":   0,
        "cidade":     "São Simão/GO",
        "variantes":  ["Samuel E. Magalhães", "Samuel Magalhaes"],
    },
    {
        "nome":       "Vitor Rosa Silva",
        "concessao":  "MINAS",
        "cargo":      "Engenheiro Sala Técnica",
        "n_folha":    978,
        "grupo":      "Escritório",
        "placa":      "TBR5G87",
        "logos_nome": "VITOR ROSA",
        "logos_id":   48314,
        "cidade":     "Uberlândia/MG",
        "variantes":  ["Vitor R. Silva", "Vitor Rosa"],
    },
    {
        "nome":       "Alessandro Ribeiro Bueno",
        "concessao":  "MINAS",
        "cargo":      "Técnico de obras",
        "n_folha":    980,
        "grupo":      "Pavimento",
        "placa":      "TBR5G67",
        "logos_nome": "ALESSANDRO BUENO",
        "logos_id":   48360,
        "cidade":     "Uberlândia/MG",
        "variantes":  ["Alessandro R. Bueno", "Alessandro Bueno"],
    },
    {
        "nome":       "Sergio Reicher",
        "concessao":  "MINAS",
        "cargo":      "Técnico de obras",
        "n_folha":    0,
        "grupo":      "Pavimento",
        "placa":      "TBR5G64",
        "logos_nome": "SERGIO REICHARD",
        "logos_id":   48357,
        "cidade":     "Catalão/GO",
        "variantes":  ["Sergio Reichard", "Sergio R."],
    },
    {
        "nome":       "Josemar Oliveira da Silva",
        "concessao":  "MINAS",
        "cargo":      "Laboratorista",
        "n_folha":    0,
        "grupo":      "Pavimento",
        "placa":      "TAI7I64",
        "logos_nome": "JOSEMAR OLIVEIRA",
        "logos_id":   47634,
        "cidade":     "Catalão/GO",
        "variantes":  ["Josemar oliveira da Silva", "Josemar Oliveira"],
    },
    {
        "nome":       "Alexandre Rodrigues de Oliveira",
        "concessao":  "MINAS",
        "cargo":      "Laboratorista",
        "n_folha":    0,
        "grupo":      "Pavimento",
        "placa":      "TAI7I50",
        "logos_nome": "ALEXANDRE RODRIGUES",
        "logos_id":   41317,
        "cidade":     "Uberlândia/MG",
        "variantes":  ["Alexandre R. Oliveira", "Alexandre Rodrigues Oliveira"],
    },
    {
        "nome":       "Matheus Queiros da Silva",
        "concessao":  "MINAS",
        "cargo":      "Técnico de Campo",
        "n_folha":    0,
        "grupo":      "Pavimento",
        "placa":      "TBU6G09",
        "logos_nome": "MATHEUS QUEIROZ",
        "logos_id":   48447,
        "cidade":     "Uberlândia/MG",
        "variantes":  ["Matheus Queiroz da Silva", "Matheus Q. Silva", "Matheus Queiroz"],
    },
    {
        "nome":       "Pedro Alberto Alves",
        "concessao":  "MINAS",
        "cargo":      "Técnico de obras",
        "n_folha":    0,
        "grupo":      "Pavimento",
        "placa":      "",
        "logos_nome": "PEDRO ALBERTO",
        "logos_id":   0,
        "cidade":     "Uberlândia/MG",
        "variantes":  ["Pedro A. Alves"],
    },
    {
        "nome":       "Roberto de Melo Borges",
        "concessao":  "MINAS",
        "cargo":      "Técnico de Campo",
        "n_folha":    0,
        "grupo":      "Pavimento",
        "placa":      "",
        "logos_nome": "ROBERTO BORGES",
        "logos_id":   0,
        "cidade":     "Uberaba/MG",
        "variantes":  ["Roberto M. Borges", "Roberto Melo Borges"],
    },

    # ── ECO MINAS GOIÁS — SST ───────────────────────────────────────────────
    {
        "nome":       "Elisangela Maria Caixeta Soares",
        "concessao":  "MINAS",
        "cargo":      "Técnico de Segurança",
        "n_folha":    0,
        "grupo":      "SST",
        "placa":      "",
        "logos_nome": "ELISANGELA SOARES",
        "logos_id":   0,
        "cidade":     "Uberlândia/MG",
        "variantes":  ["Elisangela M. Soares", "Elisangela Caixeta"],
    },
    {
        "nome":       "Fernando Ricardo Da Silva Costa De Bessa",
        "concessao":  "MINAS",
        "cargo":      "Técnico de Segurança",
        "n_folha":    0,
        "grupo":      "SST",
        "placa":      "",
        "logos_nome": "FERNANDO BESSA",
        "logos_id":   0,
        "cidade":     "Uberlândia/MG",
        "variantes":  ["Fernando Ricardo Bessa", "Fernando R. Bessa", "Fernando Da Silva Bessa"],
    },
    {
        "nome":       "Hellen AP. Alcântara Soares",
        "concessao":  "MINAS",
        "cargo":      "Técnico de Segurança",
        "n_folha":    923,
        "grupo":      "SST",
        "placa":      "TDF9E16",
        "logos_nome": "HELLEN SOARES",
        "logos_id":   0,
        "cidade":     "Uberlândia/MG",
        "variantes":  ["Hellen Alcântara Soares", "Hellen A. Soares", "Hellen Alcantara"],
    },
    {
        "nome":       "Janáína Vanira Silva",
        "concessao":  "MINAS",
        "cargo":      "Técnico de Segurança",
        "n_folha":    952,
        "grupo":      "SST",
        "placa":      "RUD4D39",
        "logos_nome": "JANAINA",
        "logos_id":   47483,
        "cidade":     "Catalão/GO",
        "variantes":  ["Janaina Vanira Silva", "Janáina Silva", "Janaina Silva"],
    },
    {
        "nome":       "Leonardo Vitor Faria Martins",
        "concessao":  "MINAS",
        "cargo":      "Técnico de Segurança",
        "n_folha":    927,
        "grupo":      "SST",
        "placa":      "SSY7I46",
        "logos_nome": "LEONARDO MARTINS",
        "logos_id":   0,
        "cidade":     "Catalão/GO",
        "variantes":  ["Leonardo V. Martins", "Leonardo Faria Martins"],
    },
]

# ---------------------------------------------------------------------------
# Índices rápidos
# ---------------------------------------------------------------------------

# placa (sem hífen, maiúscula) → colaborador
_IDX_PLACA: dict[str, dict] = {
    c["placa"].upper().replace("-", ""): c
    for c in COLABORADORES if c.get("placa")
}

# logos_id → colaborador
_IDX_LOGOS_ID: dict[int, dict] = {
    c["logos_id"]: c
    for c in COLABORADORES if c.get("logos_id")
}

# concessão → lista de colaboradores
_IDX_CONCESSAO: dict[str, list[dict]] = {}
for _c in COLABORADORES:
    _IDX_CONCESSAO.setdefault(_c["concessao"], []).append(_c)


def _normalize(s: str) -> str:
    """Remove acentos, lowercase, colapsa espaços."""
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s).strip().lower()


def _score(a: str, b: str) -> float:
    """Score de similaridade simples entre dois nomes normalizados (0-1)."""
    wa = set(a.split())
    wb = set(b.split())
    if not wa or not wb:
        return 0.0
    inter = wa & wb
    # Boost se os sobrenomes batem
    last_a = a.split()[-1] if a.split() else ""
    last_b = b.split()[-1] if b.split() else ""
    boost = 0.2 if last_a and last_a == last_b else 0.0
    return len(inter) / max(len(wa), len(wb)) + boost


def buscar_colaborador(nome: str, threshold: float = 0.45) -> dict | None:
    """
    Busca o colaborador mais próximo pelo nome (fuzzy).
    Verifica nome canônico + variantes.
    Retorna o dict do colaborador ou None se abaixo do threshold.
    """
    n = _normalize(nome)
    best_score = 0.0
    best = None
    for c in COLABORADORES:
        candidates = [c["nome"]] + c.get("variantes", []) + [c["logos_nome"]]
        for cand in candidates:
            s = _score(n, _normalize(cand))
            if s > best_score:
                best_score = s
                best = c
    return best if best_score >= threshold else None


def buscar_por_placa(placa: str) -> dict | None:
    """Busca colaborador pela placa (ignora hífen e maiúsc/minúsc)."""
    key = placa.upper().replace("-", "").replace(" ", "")
    return _IDX_PLACA.get(key)


def buscar_por_logos_id(logos_id: int) -> dict | None:
    """Busca colaborador pelo id do veículo no Logos."""
    return _IDX_LOGOS_ID.get(logos_id)


def concessao_label(concessao: str) -> str:
    """Retorna label legível da concessão."""
    return {
        "CERRADO": "ECO Cerrado",
        "MINAS":   "ECO Minas Goiás",
        "ECO135":  "ECO-135",
    }.get(concessao, concessao or "—")


def concessao_cor(concessao: str) -> str:
    return {
        "CERRADO": "#4CC9F0",
        "MINAS":   "#7BBF6A",
        "ECO135":  "#F7B731",
    }.get(concessao, "#8FA882")


def enriquecer_logos_veiculo(veiculo: dict) -> dict:
    """
    Recebe um dict de veículo do Logos e acrescenta campos:
      concessao, concessao_label, colaborador_nome, n_folha, grupo.
    Tenta matching por logos_id → placa → nome fuzzy.
    """
    logos_id = veiculo.get("idvei") or veiculo.get("pos_idvei") or 0
    placa     = (veiculo.get("placa") or veiculo.get("placavel") or "").replace("-", "")
    motorista = veiculo.get("motorista") or veiculo.get("descricaovel") or ""

    # Detecta concessão pelo prefixo do Logos
    desc_up = (veiculo.get("desc") or veiculo.get("descricaovel") or "").upper()
    if "ECO-135" in desc_up or "ECO135" in desc_up:
        concessao = "ECO135"
    else:
        concessao = ""  # será preenchido pelo colaborador

    colab = (buscar_por_logos_id(logos_id)
             or buscar_por_placa(placa)
             or buscar_colaborador(motorista))

    if colab:
        concessao = concessao or colab["concessao"]
        veiculo["concessao"]          = concessao
        veiculo["concessao_label"]    = concessao_label(concessao)
        veiculo["concessao_cor"]      = concessao_cor(concessao)
        veiculo["colaborador_nome"]   = colab["nome"]
        veiculo["n_folha"]            = colab["n_folha"]
        veiculo["grupo"]              = colab["grupo"]
        veiculo["cargo"]              = colab["cargo"]
    else:
        veiculo["concessao"]          = concessao or "CERRADO"
        veiculo["concessao_label"]    = concessao_label(concessao or "CERRADO")
        veiculo["concessao_cor"]      = concessao_cor(concessao or "CERRADO")
        veiculo["colaborador_nome"]   = motorista
        veiculo["n_folha"]            = 0
        veiculo["grupo"]              = ""
        veiculo["cargo"]              = ""

    return veiculo
