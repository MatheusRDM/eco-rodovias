"""
=========================================================================
ESTILOS GLOBAIS - AFIRMA E-VIAS
=========================================================================
Sistema de Design Padronizado baseado no Manual de Marca
Alto Contraste | Fontes Poppins/Exo | Paleta Corporativa
=========================================================================
"""

import streamlit as st
import os

# ======================================================================================
# PALETA DE CORES CORPORATIVA OFICIAL - AFIRMA E-VIAS
# ======================================================================================
CORES = {
    # Cores Primárias (Extraídas da Paleta Oficial)
    'primario': '#00233B',           # Azul Escuro (Principal)
    'secundario': '#566E3D',         # Verde Oliva (Ação/Status)
    'destaque': '#BFCF99',           # Verde Claro (Destaques/Bordas)
    
    # Tons Neutros e Fundo
    'fundo_claro': '#EFEBDC',        # Bege Claro
    'neutro': '#F2F1EF',             # Cinza Acetinado
    'branco': '#FFFFFF',             # Branco Puro
    
    # Mapeamento para Interface do Usuário (UI)
    'fundo_escuro': '#00233B',       # Fundo principal
    'fundo_card': '#0a3d5f',         # Azul variante para elevação de cards
    'fundo_hover': '#0d4a6f',        # Azul sutil para estados de hover
    
    # Cores de Texto (Garantindo Alto Contraste)
    'texto_primario': '#FFFFFF',     # Branco puro
    'texto_secundario': '#F2F1EF',   # Cinza acetinado para textos de apoio
    'texto_destaque': '#BFCF99',     # Verde claro para títulos e ênfase
    'texto_escuro': '#00233B',       # Azul escuro para leitura em fundos claros
    
    # Cores de Status (Alinhadas à Identidade Visual)
    'sucesso': '#566E3D',            # Verde Oliva (Padronizado)
    'finalizado': '#566E3D',         # Verde Oliva
    'alerta': '#f59e0b',             # Amarelo Corporativo
    'erro': '#dc2626',               # Vermelho Corporativo
    'info': '#3b82f6',               # Azul Informativo
    'em_andamento': '#3b82f6',       
    'aguardando': '#f59e0b',         
    'urgente': '#dc2626',            
    'vencido': '#7f1d1d',            
    
    # Bordas e Divisores
    'borda_primaria': '#566E3D',     # Verde Oliva
    'borda_destaque': '#BFCF99',     # Verde Claro
    'borda_sutil': '#566E3D',        # Azul Marinho Médio
}

# ======================================================================================
# CONFIGURAÇÕES DE FONTE
# ======================================================================================
FONTES = {
    'primaria': 'Poppins',
    'secundaria': 'Exo',
    'fallback': 'sans-serif',
}

# ======================================================================================
# CSS GLOBAL - ALTO CONTRASTE E DESIGN PROFISSIONAL
# ======================================================================================
def get_css_global():
    """Retorna o CSS global padronizado para todas as páginas"""
    return f"""
<style>
    /* ==================== IMPORTAÇÃO DE FONTES ==================== */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Exo:wght@300;400;500;600;700;800&display=swap');

    /* ==================== RESET E CONFIGURAÇÕES BASE ==================== */
    .stApp {{
        background: linear-gradient(180deg, {CORES['primario']} 0%, #001829 100%);
        font-family: '{FONTES['primaria']}', '{FONTES['secundaria']}', {FONTES['fallback']};
        color: {CORES['texto_primario']};
        font-size: 16px;
        line-height: 1.6;
    }}

    /* OCULTAR NOME DO ARQUIVO NA SIDEBAR (app, pages, etc) */
    section[data-testid="stSidebar"] [data-testid="stSidebarNavItems"] {{
        display: none !important;
    }}
    
    /* Ocultar link de navegação do Streamlit */
    section[data-testid="stSidebar"] div[data-testid="stSidebarNav"] {{
        display: none !important;
    }}
    
    /* Ocultar header da sidebar */
    section[data-testid="stSidebar"] header {{
        display: none !important;
    }}

    /* ==================== TIPOGRAFIA - ALTO CONTRASTE ==================== */
    h1, h2, h3, h4, h5, h6,
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
        font-family: '{FONTES['primaria']}', {FONTES['fallback']};
        color: {CORES['texto_primario']} !important;
        font-weight: 700;
        letter-spacing: -0.02em;
    }}
    
    h1 {{
        font-size: 2.8rem !important;
        line-height: 1.2;
        text-shadow: 0 2px 4px rgba(0,0,0,0.3);
    }}
    
    h2 {{
        font-size: 2rem !important;
        line-height: 1.3;
        color: {CORES['texto_destaque']} !important;
    }}
    
    h3 {{
        font-size: 1.5rem !important;
        line-height: 1.4;
    }}

    /* Textos gerais com alto contraste */
    p, div, span, label, li {{
        font-family: '{FONTES['primaria']}', {FONTES['fallback']};
        color: {CORES['texto_primario']};
        font-size: 15px;
        line-height: 1.6;
    }}

    /* ==================== SIDEBAR - DESIGN PROFISSIONAL ==================== */
    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {CORES['primario']} 0%, #001829 100%);
        border-right: 3px solid {CORES['secundario']};
    }}
    
    section[data-testid="stSidebar"] > div {{
        padding-top: 1rem;
    }}
    
    /* Logo na Sidebar */
    section[data-testid="stSidebar"] img {{
        max-width: 200px !important;
        margin: 0 auto 1.5rem auto;
        display: block;
        filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));
    }}
    
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {{
        color: {CORES['texto_destaque']} !important;
        font-size: 1.3rem !important;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid {CORES['secundario']};
    }}
    
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] .stMarkdown,
    section[data-testid="stSidebar"] p {{
        color: {CORES['texto_secundario']} !important;
        font-size: 14px !important;
        font-weight: 500 !important;
    }}

    /* ==================== CARDS DE MÉTRICAS/KPI - INTERATIVOS ==================== */
    div[data-testid="stMetric"] {{
        background: linear-gradient(135deg, {CORES['secundario']} 0%, #6a8a4a 100%);
        border: 2px solid {CORES['borda_destaque']};
        border-radius: 12px;
        padding: 1.25rem;
        box-shadow: 0 4px 20px rgba(86, 110, 61, 0.4);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
    }}
    
    div[data-testid="stMetric"]:hover {{
        transform: translateY(-4px) scale(1.02);
        box-shadow: 0 12px 40px rgba(86, 110, 61, 0.6);
        border-color: {CORES['texto_primario']};
        background: linear-gradient(135deg, #6a8a4a 0%, #7da058 100%);
    }}
    
    div[data-testid="stMetric"]:active {{
        transform: translateY(-2px) scale(1.01);
    }}
    
    /* Labels dos KPIs */
    div[data-testid="stMetric"] label {{
        font-size: 14px !important;
        font-weight: 600 !important;
        color: {CORES['texto_destaque']} !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    
    /* Valores dos KPIs - ALTO CONTRASTE */
    div[data-testid="stMetric"] > div > div > div:nth-child(2) {{
        font-size: 2rem !important;
        font-weight: 800 !important;
        color: {CORES['texto_primario']} !important;
        text-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }}
    
    /* Delta dos KPIs */
    div[data-testid="stMetric"] > div > div > div:nth-child(3) {{
        font-size: 13px !important;
        font-weight: 600 !important;
    }}
    
    /* Cores das bordas laterais por posição */
    div[data-testid="column"]:nth-of-type(1) div[data-testid="stMetric"] {{ 
        border-left: 5px solid {CORES['primario']};
    }}
    div[data-testid="column"]:nth-of-type(2) div[data-testid="stMetric"] {{ 
        border-left: 5px solid {CORES['secundario']};
    }}
    div[data-testid="column"]:nth-of-type(3) div[data-testid="stMetric"] {{ 
        border-left: 5px solid {CORES['destaque']};
    }}
    div[data-testid="column"]:nth-of-type(4) div[data-testid="stMetric"] {{ 
        border-left: 5px solid {CORES['info']};
    }}
    div[data-testid="column"]:nth-of-type(5) div[data-testid="stMetric"] {{ 
        border-left: 5px solid {CORES['alerta']};
    }}
    div[data-testid="column"]:nth-of-type(6) div[data-testid="stMetric"] {{ 
        border-left: 5px solid {CORES['erro']};
    }}

    /* ==================== BOTÕES ==================== */
    div.stButton > button {{
        background: linear-gradient(135deg, {CORES['secundario']} 0%, #6a8a4a 100%);
        color: {CORES['texto_primario']};
        border: 2px solid {CORES['borda_destaque']};
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-family: '{FONTES['primaria']}', {FONTES['fallback']};
        font-weight: 600;
        font-size: 15px;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(86, 110, 61, 0.4);
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }}
    
    div.stButton > button:hover {{
        background: linear-gradient(135deg, #6a8a4a 0%, #7da058 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(86, 110, 61, 0.6);
        border-color: {CORES['texto_primario']};
    }}
    
    div.stButton > button:active {{
        transform: translateY(0);
    }}

    /* ==================== INPUTS E SELECTS ==================== */
    /* Selectbox na área principal */
    div[data-testid="stSelectbox"] > div > div {{
        background-color: {CORES['fundo_card']};
        border: 2px solid {CORES['borda_primaria']};
        border-radius: 8px;
        color: {CORES['texto_primario']};
        font-size: 14px;
    }}
    
    div[data-testid="stSelectbox"] > div > div:hover {{
        border-color: {CORES['borda_destaque']};
    }}
    
    /* Selectbox na Sidebar - FUNDO ESCURO COM FONTE CLARA */
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] > div > div {{
        background-color: {CORES['primario']} !important;
        border: 2px solid {CORES['borda_destaque']} !important;
        color: {CORES['texto_primario']} !important;
    }}
    
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] > div > div > div {{
        color: {CORES['texto_primario']} !important;
    }}
    
    section[data-testid="stSidebar"] div[data-testid="stSelectbox"] svg {{
        fill: {CORES['texto_primario']} !important;
    }}
    
    /* Label dos selectbox na sidebar */
    section[data-testid="stSidebar"] label {{
        color: {CORES['texto_primario']} !important;
    }}

    /* Multiselect */
    div[data-testid="stMultiSelect"] > div > div {{
        background-color: {CORES['fundo_card']};
        border: 2px solid {CORES['borda_primaria']};
        border-radius: 8px;
        color: {CORES['texto_primario']};
    }}
    
    div[data-testid="stMultiSelect"] > div > div:hover {{
        border-color: {CORES['borda_destaque']};
    }}
    
    /* Tags do Multiselect */
    div[data-testid="stMultiSelect"] span[data-baseweb="tag"] {{
        background-color: {CORES['secundario']} !important;
        color: {CORES['texto_primario']} !important;
        border-radius: 4px;
        font-weight: 500;
    }}
    
    /* Dropdown menu - POPUP DOS FILTROS */
    div[data-baseweb="popover"] {{
        background-color: {CORES['primario']} !important;
    }}
    
    div[data-baseweb="popover"] div[data-baseweb="menu"] {{
        background-color: {CORES['primario']} !important;
        border: 2px solid {CORES['borda_destaque']} !important;
        border-radius: 8px !important;
    }}
    
    /* Itens do dropdown */
    ul[data-baseweb="menu"] {{
        background-color: {CORES['primario']} !important;
    }}
    
    li[data-baseweb="menu-item"] {{
        background-color: {CORES['primario']} !important;
    }}
    
    li[data-baseweb="menu-item"] > div {{
        background-color: transparent !important;
        color: {CORES['texto_primario']} !important;
        padding: 10px 15px !important;
    }}
    
    li[data-baseweb="menu-item"]:hover {{
        background-color: {CORES['secundario']} !important;
    }}
    
    li[data-baseweb="menu-item"]:hover > div {{
        background-color: {CORES['secundario']} !important;
        color: {CORES['texto_primario']} !important;
    }}
    
    /* Highlight do item selecionado */
    li[data-baseweb="menu-item"][aria-selected="true"] {{
        background-color: {CORES['secundario']} !important;
    }}
    
    li[data-baseweb="menu-item"][aria-selected="true"] > div {{
        background-color: {CORES['secundario']} !important;
        color: {CORES['texto_primario']} !important;
    }}

    /* ==================== TABELAS E DATAFRAMES ==================== */
    [data-testid="stDataFrame"] {{
        background: linear-gradient(135deg, {CORES['primario']} 0%, {CORES['fundo_card']} 100%);
        border-radius: 12px;
        padding: 1rem;
        border: 2px solid {CORES['borda_primaria']};
        box-shadow: 0 4px 20px rgba(0, 35, 59, 0.4);
    }}
    
    .dataframe {{
        background-color: transparent;
        color: {CORES['texto_primario']};
    }}
    
    .dataframe th {{
        background-color: {CORES['secundario']} !important;
        color: {CORES['texto_primario']} !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        padding: 12px !important;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }}
    
    .dataframe td {{
        background-color: rgba(0, 35, 59, 0.6) !important;
        color: {CORES['texto_secundario']} !important;
        font-size: 13px !important;
        padding: 10px !important;
        border-bottom: 1px solid {CORES['borda_sutil']} !important;
    }}
    
    .dataframe tr:hover td {{
        background-color: rgba(86, 110, 61, 0.3) !important;
    }}

    /* ==================== GRÁFICOS PLOTLY ==================== */
    .stPlotlyChart {{
        background: linear-gradient(135deg, {CORES['primario']} 0%, {CORES['fundo_card']} 100%);
        border-radius: 12px;
        padding: 1rem;
        border: 2px solid {CORES['borda_primaria']};
        box-shadow: 0 4px 20px rgba(0, 35, 59, 0.4);
    }}

    /* ==================== EXPANDERS ==================== */
    .streamlit-expanderHeader {{
        background: linear-gradient(135deg, {CORES['secundario']} 0%, #6a8a4a 100%);
        color: {CORES['texto_primario']} !important;
        font-size: 15px !important;
        font-weight: 600 !important;
        padding: 1rem !important;
        border-radius: 8px;
        border: 2px solid {CORES['borda_destaque']};
    }}
    
    .streamlit-expanderContent {{
        background-color: rgba(0, 35, 59, 0.9);
        border: 2px solid {CORES['borda_primaria']};
        border-top: none;
        border-radius: 0 0 8px 8px;
        padding: 1rem;
    }}

    /* ==================== TABS ==================== */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
        background-color: transparent;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background-color: {CORES['fundo_card']};
        color: {CORES['texto_primario']};
        border-radius: 8px 8px 0 0;
        border: 2px solid {CORES['borda_primaria']};
        border-bottom: none;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: {CORES['secundario']} !important;
        border-color: {CORES['borda_destaque']} !important;
    }}

    /* ==================== ALERTAS ==================== */
    .stAlert {{
        background: linear-gradient(135deg, {CORES['primario']} 0%, {CORES['fundo_card']} 100%);
        color: {CORES['texto_primario']};
        border: 2px solid {CORES['borda_destaque']};
        border-radius: 8px;
    }}

    /* ==================== SEPARADORES ==================== */
    hr {{
        border-color: {CORES['borda_primaria']};
        margin: 2rem 0 !important;
        opacity: 0.6;
    }}

    /* ==================== SCROLLBAR PERSONALIZADA ==================== */
    ::-webkit-scrollbar {{
        width: 10px;
        height: 10px;
    }}
    
    ::-webkit-scrollbar-track {{
        background: {CORES['primario']};
    }}
    
    ::-webkit-scrollbar-thumb {{
        background: {CORES['secundario']};
        border-radius: 5px;
    }}
    
    ::-webkit-scrollbar-thumb:hover {{
        background: {CORES['destaque']};
    }}

    /* ==================== CARDS DE NAVEGAÇÃO ==================== */
    .nav-card {{
        background: linear-gradient(135deg, {CORES['primario']} 0%, {CORES['fundo_card']} 100%);
        border: 3px solid {CORES['borda_primaria']};
        border-radius: 16px;
        padding: 2rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0, 35, 59, 0.5);
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        cursor: pointer;
        text-align: center;
        min-height: 220px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
    }}
    
    .nav-card:hover {{
        transform: translateY(-10px) scale(1.02);
        box-shadow: 0 20px 60px rgba(86, 110, 61, 0.4);
        border-color: {CORES['borda_destaque']};
        background: linear-gradient(135deg, {CORES['secundario']} 0%, #6a8a4a 100%);
    }}
    
    .nav-card h3 {{
        font-size: 1.6rem !important;
        margin-bottom: 1rem;
        color: {CORES['texto_primario']};
    }}
    
    .nav-card p {{
        font-size: 1rem;
        color: {CORES['texto_secundario']};
        margin-bottom: 1.5rem;
        line-height: 1.6;
    }}
    
    .nav-card .icon {{
        font-size: 3.5rem;
        margin-bottom: 1rem;
    }}

    /* ==================== HEADER COM LOGO ==================== */
    .header-container {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 1rem 2rem;
        background: linear-gradient(135deg, {CORES['primario']} 0%, {CORES['fundo_card']} 100%);
        border-radius: 12px;
        margin-bottom: 2rem;
        border: 2px solid {CORES['borda_primaria']};
    }}
    
    .header-logo {{
        max-width: 180px;
        height: auto;
    }}
    
    .header-title {{
        color: {CORES['texto_primario']};
        font-size: 1.8rem;
        font-weight: 700;
        margin: 0;
    }}

    /* ==================== FOOTER ==================== */
    .footer {{
        text-align: center;
        margin-top: 3rem;
        padding: 1.5rem;
        border-top: 2px solid {CORES['borda_primaria']};
        color: {CORES['texto_destaque']};
        font-size: 0.85rem;
    }}
    
    .footer a {{
        color: {CORES['destaque']};
        text-decoration: none;
    }}

    /* ==================== ANIMAÇÕES ==================== */
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translateY(20px); }}
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    .fade-in {{
        animation: fadeIn 0.5s ease-out forwards;
    }}

    /* ==================== SLIDER ==================== */
    .stSlider > div > div > div {{
        background-color: {CORES['secundario']} !important;
    }}
    
    .stSlider > div > div > div > div {{
        background-color: {CORES['destaque']} !important;
    }}
    
    /* Slider thumb (bolinha) */
    .stSlider [role="slider"] {{
        background-color: {CORES['destaque']} !important;
        border-color: {CORES['secundario']} !important;
    }}
    
    /* Slider value text */
    .stSlider > div > div > div > div > div {{
        color: {CORES['destaque']} !important;
    }}
    
    /* Sidebar slider overrides */
    section[data-testid="stSidebar"] .stSlider > div > div > div {{
        background-color: {CORES['secundario']} !important;
    }}
    
    section[data-testid="stSidebar"] .stSlider > div > div > div > div {{
        background-color: {CORES['destaque']} !important;
    }}
    
    section[data-testid="stSidebar"] .stSlider [role="slider"] {{
        background-color: {CORES['destaque']} !important;
    }}

    /* ==================== CHECKBOX ==================== */
    .stCheckbox > label > div[data-testid="stCheckbox"] > div {{
        background-color: {CORES['fundo_card']};
        border-color: {CORES['borda_primaria']};
    }}
    
    .stCheckbox > label > div[data-testid="stCheckbox"] > div[aria-checked="true"] {{
        background-color: {CORES['secundario']} !important;
        border-color: {CORES['destaque']} !important;
    }}
    
    /* Sidebar checkbox overrides */
    section[data-testid="stSidebar"] .stCheckbox > label > div[data-testid="stCheckbox"] > div[aria-checked="true"] {{
        background-color: {CORES['secundario']} !important;
        border-color: {CORES['destaque']} !important;
    }}
    
    /* Checkbox SVG check mark */
    .stCheckbox svg {{
        fill: {CORES['texto_primario']} !important;
        stroke: {CORES['texto_primario']} !important;
    }}

    /* ==================== RADIO BUTTONS ==================== */
    /* Override radio button accent color */
    section[data-testid="stSidebar"] .stRadio > div > label > div:first-child {{
        color: {CORES['secundario']} !important;
    }}
    
    .stRadio [role="radiogroup"] label div[data-testid="stMarkdownContainer"] {{
        color: {CORES['texto_primario']} !important;
    }}

    /* ==================== STREAMLIT ACCENT OVERRIDE ==================== */
    /* Force Streamlit primary accent color to palette */
    :root {{
        --primary-color: {CORES['secundario']} !important;
    }}
    
    /* Override any remaining red accent colors */
    .st-emotion-cache-1inwz65 {{
        fill: {CORES['secundario']} !important;
    }}
    
    /* Generic accent override for checked states */
    [data-baseweb="checkbox"] [data-testid="stCheckbox"] {{
        --primaryColor: {CORES['secundario']} !important;
    }}

    /* ==================== DATE INPUT ==================== */
    .stDateInput > div > div {{
        background-color: {CORES['fundo_card']};
        border: 2px solid {CORES['borda_primaria']};
        color: {CORES['texto_primario']};
    }}

    /* ==================== TEXT INPUT ==================== */
    .stTextInput > div > div {{
        background-color: {CORES['fundo_card']};
        border: 2px solid {CORES['borda_primaria']};
        color: {CORES['texto_primario']};
        border-radius: 8px;
    }}
    
    .stTextInput > div > div:focus-within {{
        border-color: {CORES['destaque']};
    }}
    
    .stTextInput input {{
        color: {CORES['texto_primario']} !important;
    }}

    /* ==================== NUMBER INPUT ==================== */
    .stNumberInput > div > div {{
        background-color: {CORES['fundo_card']};
        border: 2px solid {CORES['borda_primaria']};
    }}
    
    .stNumberInput input {{
        color: {CORES['texto_primario']} !important;
    }}

    /* ==================== RADIO BUTTONS ==================== */
    .stRadio > div {{
        background-color: transparent;
    }}
    
    .stRadio label {{
        color: {CORES['texto_primario']} !important;
    }}

    /* ==================== PROGRESS BAR ==================== */
    .stProgress > div > div > div {{
        background-color: {CORES['secundario']};
    }}

    /* ==================== TOAST ==================== */
    .stToast {{
        background-color: {CORES['secundario']} !important;
        color: {CORES['texto_primario']} !important;
    }}

    /* ==================== FILE UPLOADER ==================== */
    .stFileUploader > div {{
        background-color: {CORES['fundo_card']};
        border: 2px dashed {CORES['borda_primaria']};
        border-radius: 12px;
    }}
    
    .stFileUploader > div:hover {{
        border-color: {CORES['destaque']};
    }}

    /* ==================== FILTROS INTERATIVOS - DESIGN REFINADO ==================== */
    /* Selectbox em expanders - fundo escuro, fonte clara */
    .streamlit-expanderContent div[data-testid="stSelectbox"] > div > div {{
        background-color: {CORES['fundo_card']} !important;
        border: 2px solid {CORES['borda_primaria']} !important;
        border-radius: 8px !important;
        color: {CORES['texto_primario']} !important;
        transition: all 0.3s ease !important;
    }}
    
    .streamlit-expanderContent div[data-testid="stSelectbox"] > div > div:hover {{
        border-color: {CORES['destaque']} !important;
        box-shadow: 0 4px 15px rgba(86, 110, 61, 0.3) !important;
    }}
    
    /* Multiselect em expanders */
    .streamlit-expanderContent div[data-testid="stMultiSelect"] > div > div {{
        background-color: {CORES['fundo_card']} !important;
        border: 2px solid {CORES['borda_primaria']} !important;
        border-radius: 8px !important;
        color: {CORES['texto_primario']} !important;
        transition: all 0.3s ease !important;
    }}
    
    .streamlit-expanderContent div[data-testid="stMultiSelect"] > div > div:hover {{
        border-color: {CORES['destaque']} !important;
        box-shadow: 0 4px 15px rgba(86, 110, 61, 0.3) !important;
    }}

    /* Expander com design clean */
    details[data-testid="stExpander"] {{
        border: 2px solid {CORES['borda_primaria']} !important;
        border-radius: 12px !important;
        background: linear-gradient(135deg, {CORES['primario']} 0%, {CORES['fundo_card']} 100%) !important;
        transition: all 0.3s ease !important;
    }}
    
    details[data-testid="stExpander"]:hover {{
        border-color: {CORES['destaque']} !important;
        box-shadow: 0 6px 20px rgba(86, 110, 61, 0.3) !important;
    }}
    
    details[data-testid="stExpander"] summary {{
        background: linear-gradient(135deg, {CORES['secundario']} 0%, #6a8a4a 100%) !important;
        color: {CORES['texto_primario']} !important;
        border-radius: 10px 10px 0 0 !important;
        padding: 1rem !important;
        font-weight: 600 !important;
    }}
    
    details[data-testid="stExpander"][open] summary {{
        border-radius: 10px 10px 0 0 !important;
    }}

    /* Container com scroll para expanders de dados */
    .scrollable-container {{
        max-height: 300px;
        overflow-y: auto;
        padding: 1rem;
        background: rgba(0, 35, 59, 0.5);
        border-radius: 8px;
    }}
    
    /* Scrollbar estilizada */
    .scrollable-container::-webkit-scrollbar {{
        width: 8px;
    }}
    
    .scrollable-container::-webkit-scrollbar-track {{
        background: {CORES['primario']};
        border-radius: 4px;
    }}
    
    .scrollable-container::-webkit-scrollbar-thumb {{
        background: {CORES['secundario']};
        border-radius: 4px;
    }}
    
    .scrollable-container::-webkit-scrollbar-thumb:hover {{
        background: {CORES['destaque']};
    }}
    
    /* Popup modal com scroll */
    .popup-content {{
        max-height: 400px;
        overflow-y: auto;
        padding: 1.5rem;
        background: linear-gradient(135deg, {CORES['primario']} 0%, {CORES['fundo_card']} 100%);
        border-radius: 12px;
        border: 2px solid {CORES['borda_destaque']};
    }}
    
    .popup-content::-webkit-scrollbar {{
        width: 8px;
    }}
    
    .popup-content::-webkit-scrollbar-track {{
        background: {CORES['primario']};
        border-radius: 4px;
    }}
    
    .popup-content::-webkit-scrollbar-thumb {{
        background: {CORES['secundario']};
        border-radius: 4px;
    }}

    /* Sidebar logo maior */
    section[data-testid="stSidebar"] img {{
        max-width: 100% !important;
        margin: 0 auto 1rem auto;
        display: block;
        filter: drop-shadow(0 4px 12px rgba(0,0,0,0.4));
    }}
    
    /* KPI Labels brancos */
    div[data-testid="stMetric"] label {{
        color: {CORES['texto_primario']} !important;
    }}

    /* ============================================================
       RESPONSIVE DESIGN — TABLET (≤ 768px) & MOBILE (≤ 480px)
       Técnica principal: colunas Streamlit empilham via flex-wrap
    ============================================================ */

    /* ── Tablet: ≤ 768px ── */
    /* ══════════════════════════════════════════════════════════════
       TABLET: ≤ 768px
       ══════════════════════════════════════════════════════════════ */
    @media (max-width: 768px) {{

        /* Colunas: empilhamento em pares (50% cada) */
        [data-testid="stHorizontalBlock"] {{
            flex-wrap: wrap !important;
            gap: 0.5rem !important;
        }}
        [data-testid="column"] {{
            min-width: min(200px, 100%) !important;
            flex: 1 1 calc(50% - 0.5rem) !important;
        }}

        /* Tipografia reduzida */
        h1 {{ font-size: 1.8rem !important; }}
        h2 {{ font-size: 1.35rem !important; }}
        h3 {{ font-size: 1.05rem !important; }}

        /* Container principal */
        .main-container {{ padding: 0.8rem 0.4rem !important; }}
        .block-container {{ padding: 1.2rem 0.8rem !important; }}

        /* Nav-cards compactos */
        .nav-card {{
            min-height: 140px !important;
            padding: 1rem !important;
        }}
        .nav-card .icon {{ font-size: 2.2rem !important; margin-bottom: 0.4rem !important; }}
        .nav-card h3 {{ font-size: 1.1rem !important; }}
        .nav-card:hover {{ transform: none !important; }}

        /* Header container em coluna */
        .header-container {{
            flex-direction: column !important;
            padding: 0.6rem 0.8rem !important;
            text-align: center !important;
        }}
        .header-logo {{ max-width: 110px !important; margin-bottom: 0.4rem !important; }}
        .header-title {{ font-size: 1.2rem !important; }}

        /* KPIs: forçar wrap em 3 cols */
        div[data-testid="stMetric"] {{
            padding: 0.4rem !important;
        }}
        div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
            font-size: 1.3rem !important;
        }}
        div[data-testid="stMetric"] label {{
            font-size: 0.68rem !important;
        }}

        /* Graficos: scroll horizontal + altura maxima */
        .stPlotlyChart {{
            overflow-x: auto !important;
        }}
        .stPlotlyChart > div {{
            max-height: 400px !important;
        }}
        .plot-container.plotly {{ max-width: 100% !important; }}

        /* Tabelas: scroll horizontal */
        [data-testid="stDataFrame"] {{
            overflow-x: auto !important;
            max-width: 100% !important;
        }}
        [data-testid="stDataFrame"] table {{
            font-size: 12px !important;
        }}

        /* Scrollable containers adaptativos */
        .scrollable-container {{ max-height: 55vh !important; }}

        /* Dev label: menor em tablet */
        .dev-label-fixed {{ font-size: 9px !important; opacity: 0.5 !important; }}

        /* Modebar oculta em telas pequenas */
        .modebar-container {{ display: none !important; }}

        /* Eixos: fontes menores para caber */
        .xtick text, .ytick text {{ font-size: 9px !important; }}
        .gtitle {{ font-size: 13px !important; }}
        .legend text {{ font-size: 10px !important; }}

        /* ── Mapa Folium: iframe reduzido em tablet ── */
        iframe[title*="st_folium"],
        .stCustomComponentV1 iframe {{
            height: 420px !important;
        }}

        /* ── Folium LayerControl colapsado em tablet ── */
        .leaflet-control-layers:not(.leaflet-control-layers-expanded) {{
            max-width: 36px !important;
        }}
        .leaflet-control-layers-expanded {{
            max-width: 200px !important;
            font-size: 12px !important;
        }}

        /* ── Plotly containers fixos ── */
        .st-emotion-cache-1wbqy5l,
        .stContainer {{
            max-height: 220px !important;
        }}
    }}

    /* ══════════════════════════════════════════════════════════════
       SMARTPHONE: ≤ 480px
       ══════════════════════════════════════════════════════════════ */
    @media (max-width: 480px) {{

        /* Empilhamento total — todas as colunas em 100% */
        [data-testid="column"] {{
            min-width: 100% !important;
            flex: 1 1 100% !important;
        }}

        /* Tipografia compacta */
        .stApp {{ font-size: 13px !important; line-height: 1.45 !important; }}
        h1 {{ font-size: 1.35rem !important; }}
        h2 {{ font-size: 1.1rem !important; }}
        h3 {{ font-size: 0.95rem !important; }}
        p, label, span {{ font-size: 12px !important; }}

        /* Padding geral mínimo */
        .main-container {{ padding: 0.3rem 0.2rem !important; }}
        .block-container {{ padding: 0.6rem 0.3rem !important; }}

        /* Nav-cards mínimos */
        .nav-card {{
            min-height: 100px !important;
            padding: 0.8rem !important;
        }}
        .nav-card .icon {{ font-size: 1.8rem !important; }}
        .nav-card h3 {{ font-size: 0.9rem !important; margin-bottom: 0.3rem !important; }}
        .nav-card p {{ font-size: 11px !important; }}

        /* Métricas ultra-compactas */
        div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
            font-size: 1.05rem !important;
        }}
        div[data-testid="stMetric"] label {{
            font-size: 0.6rem !important;
        }}

        /* Botões full width */
        .stButton > button {{
            width: 100% !important;
            padding: 0.5rem !important;
            font-size: 12px !important;
        }}

        /* Inputs full width */
        .stSelectbox > div,
        .stTextInput > div,
        .stDateInput > div {{
            width: 100% !important;
        }}

        /* Sidebar em overlay */
        section[data-testid="stSidebar"] {{
            z-index: 9999 !important;
            max-width: min(85vw, 300px) !important;
        }}

        /* Header image menor */
        .header-logo {{ max-width: 60px !important; }}

        /* Scrollable containers menores */
        .scrollable-container {{ max-height: 40vh !important; }}

        /* Expanders ocupam 100% */
        .stExpander {{ width: 100% !important; }}

        /* Tabs scrolláveis em mobile */
        .stTabs [data-baseweb="tab-list"] {{
            overflow-x: auto !important;
            flex-wrap: nowrap !important;
        }}
        .stTabs [data-baseweb="tab"] {{
            font-size: 12px !important;
            padding: 0.4rem 0.6rem !important;
        }}

        /* Dev label: ocultar em phone */
        .dev-label-fixed {{ display: none !important; }}

        /* ── Plotly: fontes menores em phone ── */
        .xtick text, .ytick text {{ font-size: 7px !important; }}
        .gtitle {{ font-size: 11px !important; }}
        .legend text {{ font-size: 8px !important; }}
        .modebar-container {{ display: none !important; }}
        .stPlotlyChart > div {{
            max-height: 320px !important;
        }}

        /* ── Mapa Folium: compacto em mobile ── */
        iframe[title*="st_folium"],
        .stCustomComponentV1 iframe {{
            height: 340px !important;
            max-height: 50vh !important;
        }}

        /* ── Folium LayerControl colapsado ── */
        .leaflet-control-layers {{
            max-width: 34px !important;
            max-height: 34px !important;
            overflow: hidden !important;
            border-radius: 5px !important;
        }}
        .leaflet-control-layers-expanded {{
            max-width: 180px !important;
            max-height: 55vh !important;
            overflow-y: auto !important;
            font-size: 11px !important;
        }}
        .leaflet-control-layers-toggle {{
            width: 32px !important;
            height: 32px !important;
            background-size: 18px !important;
        }}

        /* ── Legenda do mapa: wrap em mobile ── */
        div[style*="display:flex"][style*="gap:1"] {{
            gap: 0.4rem !important;
            font-size: 11px !important;
        }}
    }}

    /* ══════════════════════════════════════════════════════════════
       ULTRA-WIDE: ≥ 1440px — Aproveitar espaço
       ══════════════════════════════════════════════════════════════ */
    @media (min-width: 1440px) {{
        .block-container {{ max-width: 1280px !important; margin: 0 auto !important; }}
        h1 {{ font-size: 2.6rem !important; }}
    }}
</style>
"""

# ======================================================================================
# FUNÇÃO PARA APLICAR ESTILOS GLOBAIS
# ======================================================================================
def _get_js_responsivo():
    """JavaScript que relayouta gráficos Plotly:
    - Em TODAS as telas: desabilita zoom/drag (fixedrange + dragmode: false)
    - Em telas pequenas (<=768px): ajusta altura, margens e legenda via Plotly.relayout()
    Plotly injeta width/height como atributos SVG inline — CSS não sobrescreve."""
    return """
<script>
(function() {
    // --- DESABILITAR ZOOM em todas as telas ---
    function desabilitarZoom(el) {
        if (!window.Plotly || !el._fullLayout) return;
        var updates = { 'dragmode': false };
        // Detecta todos os eixos presentes (xaxis, yaxis, xaxis2, yaxis2, ...)
        var layout = el._fullLayout;
        Object.keys(layout).forEach(function(k) {
            if (/^[xy]axis\d*$/.test(k)) {
                updates[k + '.fixedrange'] = true;
            }
        });
        try { Plotly.relayout(el, updates); } catch(e) {}
    }

    // --- ADAPTAR PARA MOBILE (<=768px) ---
    function adaptarMobile(el) {
        var vw = window.innerWidth;
        if (vw > 768 || !window.Plotly || !el._fullLayout) return;
        var isPhone = vw <= 480;
        var alturaAtual = el._fullLayout.height || 400;
        var alturaMax = isPhone ? 290 : 370;
        var updates = {
            height: Math.min(alturaAtual, alturaMax),
            'margin.r': 10,
            'margin.l': 8,
            'margin.t': isPhone ? 42 : 56,
            'margin.b': 65,
            'legend.orientation': 'h',
            'legend.x': 0,
            'legend.y': -0.28,
            'legend.xanchor': 'left',
            'legend.yanchor': 'top',
            'legend.font.size': isPhone ? 9 : 10,
            'title.font.size': isPhone ? 13 : 15
        };
        try { Plotly.relayout(el, updates); } catch(e) {}
    }

    // --- HOVER ROSCA: atualiza anotação central com valor do slice hovered ---
    function configurarHoverRosca(el) {
        // Se Plotly ainda não inicializou o elemento, agendar retry
        if (!window.Plotly || !el._fullData || !el.on) {
            if (!el._roscaOk) {
                var tentativas = el._roscaTentativas || 0;
                if (tentativas < 20) {
                    el._roscaTentativas = tentativas + 1;
                    setTimeout(function() { configurarHoverRosca(el); }, 200);
                }
            }
            return;
        }

        // Verifica se é gráfico de pizza/donut
        var isPie = el._fullData.some(function(d) { return d.type === 'pie'; });
        if (!isPie) return;

        // Se já configurado, só atualiza annoOriginal (caso re-render do Streamlit)
        if (el._roscaOk) {
            if (el._fullLayout && el._fullLayout.annotations && el._fullLayout.annotations[0]) {
                el._roscaAnnoOriginal = el._fullLayout.annotations[0].text;
            }
            return;
        }

        el._roscaOk = true;

        // Captura o texto original da anotação central
        el._roscaAnnoOriginal = (el._fullLayout && el._fullLayout.annotations && el._fullLayout.annotations[0])
            ? el._fullLayout.annotations[0].text : null;

        // Ao passar o mouse num slice: exibe valor + percentual no centro
        el.on('plotly_hover', function(data) {
            var pt = data.points[0];
            if (!pt) return;
            var pct = pt.percent !== undefined ? (pt.percent * 100).toFixed(1) + '%' : '';
            var novoTexto = '<b>' + pt.value + '</b>'
                + (pct ? '<br><span style="font-size:13px;opacity:0.85">' + pct + '</span>' : '');
            try { Plotly.relayout(el, {'annotations[0].text': novoTexto}); } catch(e) {}
        });

        // Ao sair do mouse: restaura o texto original
        el.on('plotly_unhover', function() {
            if (el._roscaAnnoOriginal != null) {
                try { Plotly.relayout(el, {'annotations[0].text': el._roscaAnnoOriginal}); } catch(e) {}
            }
        });

        // Após cada re-render do Plotly: re-captura annoOriginal
        el.on('plotly_afterplot', function() {
            if (el._fullLayout && el._fullLayout.annotations && el._fullLayout.annotations[0]) {
                el._roscaAnnoOriginal = el._fullLayout.annotations[0].text;
            }
        });
    }

    // Processa todos os gráficos presentes na página
    function processarTodos() {
        if (!window.Plotly) return;
        document.querySelectorAll('.js-plotly-plot').forEach(function(el) {
            desabilitarZoom(el);
            adaptarMobile(el);
            configurarHoverRosca(el);
        });
    }

    // Debounce para evitar chamadas excessivas
    var debounce;
    function agendar(delay) {
        clearTimeout(debounce);
        debounce = setTimeout(processarTodos, delay || 350);
    }

    // Reexecuta ao redimensionar janela
    window.addEventListener('resize', function() { agendar(300); });

    // MutationObserver: detecta novos gráficos adicionados dinamicamente pelo Streamlit
    var observer = new MutationObserver(function(mutations) {
        var temPlotly = mutations.some(function(m) {
            return Array.from(m.addedNodes).some(function(n) {
                return n.nodeType === 1 && (
                    n.classList && n.classList.contains('js-plotly-plot') ||
                    n.querySelector && n.querySelector('.js-plotly-plot')
                );
            });
        });
        if (temPlotly) { agendar(500); }
    });
    observer.observe(document.body, { childList: true, subtree: true });

    // Primeira execução — aguarda Plotly estar carregado
    function iniciar() {
        if (window.Plotly) {
            agendar(400);
        } else {
            setTimeout(iniciar, 200);
        }
    }
    if (document.readyState === 'complete') {
        iniciar();
    } else {
        window.addEventListener('load', iniciar);
    }
})();
</script>
"""

@st.cache_resource
def _cached_css():
    """Gera e cacheia o CSS global (1x por sessão, não toda rerun)."""
    return get_css_global()

@st.cache_resource
def _cached_js():
    """Gera e cacheia o JS responsivo (1x por sessão)."""
    return _get_js_responsivo()

@st.cache_resource
def _cached_dev_label():
    """Rótulo fixo 'Developed By: Matheus Resende' — aparece em todas as páginas."""
    return """
<style>
    .dev-label-fixed {
        position: fixed;
        bottom: 12px;
        left: 16px;
        font-size: 11px;
        color: #BFCF99;
        font-family: 'Poppins', sans-serif;
        font-weight: 500;
        opacity: 0.55;
        z-index: 99999;
        letter-spacing: 0.5px;
        text-shadow: 0 0 6px rgba(191,207,153,0.3);
        transition: opacity 0.25s ease;
        pointer-events: none;
    }
    .dev-label-fixed:hover {
        opacity: 1;
        text-shadow: 0 0 12px rgba(191,207,153,0.7);
    }
</style>
<div class="dev-label-fixed">Developed By: Matheus Resende</div>
"""

def aplicar_estilos():
    """Aplica os estilos CSS globais, JS responsivo e rótulo dev em todas as páginas."""
    st.markdown(_cached_css(), unsafe_allow_html=True)
    st.markdown(_cached_js(), unsafe_allow_html=True)
    st.markdown(_cached_dev_label(), unsafe_allow_html=True)
    # PWA: injeta ícone e manifest no <head> via JS (st.markdown vai pro body)
    st.markdown("""
        <script>
        (function() {
            function _inject() {
                // apple-touch-icon (iOS)
                if (!document.querySelector('link[rel="apple-touch-icon"]')) {
                    var l = document.createElement('link');
                    l.rel = 'apple-touch-icon'; l.sizes = '180x180';
                    l.href = '/app/static/icon-180.png';
                    document.head.appendChild(l);
                }
                // manifest (Android PWA)
                if (!document.querySelector('link[rel="manifest"]')) {
                    var m = document.createElement('link');
                    m.rel = 'manifest';
                    m.href = '/app/static/manifest.json';
                    document.head.appendChild(m);
                }
                // metas
                var metas = {
                    'mobile-web-app-capable': 'yes',
                    'apple-mobile-web-app-capable': 'yes',
                    'apple-mobile-web-app-status-bar-style': 'black-translucent',
                    'apple-mobile-web-app-title': 'AE',
                    'theme-color': '#00233B'
                };
                Object.keys(metas).forEach(function(name) {
                    if (!document.querySelector('meta[name="' + name + '"]')) {
                        var t = document.createElement('meta');
                        t.name = name; t.content = metas[name];
                        document.head.appendChild(t);
                    }
                });
            }
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', _inject);
            } else {
                _inject();
            }
        })();
        </script>
    """, unsafe_allow_html=True)

# ======================================================================================
# FUNÇÃO PARA RENDERIZAR SIDEBAR PADRÃO
# ======================================================================================
def renderizar_sidebar(pagina_atual="Dashboard"):
    """
    Renderiza a sidebar padrão com logo e navegação
    
    Args:
        pagina_atual: Nome da página atual para destacar na navegação
    """
    with st.sidebar:
        # Logo grande no topo
        try:
            logo_path = os.path.join(os.path.dirname(__file__), "Imagens", "AE - Logo Hor Principal_2.png")
            if os.path.exists(logo_path):
                st.image(logo_path, use_container_width=True)
            else:
                st.image("Imagens/AE - Logo Hor Principal_2.png", use_container_width=True)
        except Exception:
            st.markdown(f"""
            <div style="text-align: center; padding: 1.5rem; background: {CORES['secundario']}; border-radius: 12px; margin-bottom: 1rem;">
                <h2 style="color: {CORES['texto_primario']}; margin: 0;">AFIRMA E-VIAS</h2>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Título da sidebar
        st.markdown(f"""
        <h3 style="color: {CORES['texto_destaque']}; text-align: center; margin-bottom: 1rem;">AE - Dashboard's</h3>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        st.caption(f"© 2026 Afirma E-vias")

# ======================================================================================
# FUNÇÃO PARA RENDERIZAR HEADER COM LOGO
# ======================================================================================
def renderizar_header(titulo, subtitulo=""):
    """
    Renderiza o header padrão com logo e título
    
    Args:
        titulo: Título principal da página
        subtitulo: Subtítulo opcional
    """
    col1, col2 = st.columns([1, 4])
    
    with col1:
        try:
            from cloud_config import get_logo_path
            _selo = get_logo_path("selo")
            if _selo:
                st.image(_selo, use_container_width=True)
        except Exception:
            pass
    
    with col2:
        st.markdown(f"""
        <div style="padding-left: 1rem;">
            <h1 style="margin: 0; color: {CORES['texto_primario']};">{titulo}</h1>
            {"<p style='color: " + CORES['texto_destaque'] + "; font-size: 1.1rem; margin-top: 0.5rem;'>" + subtitulo + "</p>" if subtitulo else ""}
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")

# ======================================================================================
# FUNÇÃO PARA RENDERIZAR FOOTER
# ======================================================================================
def renderizar_footer():
    """Renderiza o footer padrão e o rótulo fixo no rodapé"""
    # Footer padrão
    st.markdown(f"""
    <div class="footer">
        <p>© 2026 Afirma E-vias | Laboratório Central | Sistema de Gestão de Ensaios</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Rótulo já injetado globalmente via aplicar_estilos() — sem duplicar aqui

# ======================================================================================
# CONFIGURAÇÃO DE GRÁFICOS PLOTLY - ALTO CONTRASTE
# ======================================================================================
PLOTLY_LAYOUT = {
    'font': {
        'family': 'Poppins, sans-serif',
        'color': '#FFFFFF',
        'size': 14
    },
    'paper_bgcolor': 'rgba(0,0,0,0)',
    'plot_bgcolor': 'rgba(0,0,0,0)',
    
    # CONFIGURAÇÕES GLOBAIS DE INTERATIVIDADE
    'dragmode': False,  # Desabilita arrastar/zoom
    'hovermode': 'closest',  # Tooltip segue o cursor
    'hoverlabel': {
        'bgcolor': '#00233B',
        'bordercolor': '#BFCF99',
        'font': {
            'family': 'Poppins, sans-serif',
            'size': 14,
            'color': '#FFFFFF'
        }
    },
    
    'title': {
        'font': {
            'family': 'Poppins, sans-serif',
            'size': 20,
            'color': CORES['texto_primario']
        },
        'x': 0.5,
        'xanchor': 'center'
    },
    'legend': {
        'bgcolor': 'rgba(0, 35, 59, 0.8)',
        'bordercolor': CORES['borda_primaria'],
        'font': {'color': CORES['texto_primario'], 'size': 12}
    },
    'xaxis': {
        'gridcolor': 'rgba(255,255,255,0.1)',
        'tickcolor': '#BFCF99',
        'tickfont': {'color': '#FFFFFF', 'size': 12},
        'title_font': {'color': '#BFCF99', 'size': 14},
        'fixedrange': True
    },
    'yaxis': {
        'gridcolor': 'rgba(255,255,255,0.1)',
        'tickcolor': '#BFCF99',
        'tickfont': {'color': '#FFFFFF', 'size': 12},
        'title_font': {'color': '#BFCF99', 'size': 14},
        'fixedrange': True
    }
}

# Configuração padrão para st.plotly_chart - USE EM TODOS OS GRÁFICOS
PLOTLY_CONFIG = {
    'displayModeBar': False,
    'scrollZoom': False,
    'doubleClick': False,
    'displaylogo': False,
    'staticPlot': False
}

# Cores para gráficos - paleta corporativa vibrante
CORES_GRAFICOS = [
    '#566E3D',  # Verde Oliva (Principal)
    '#BFCF99',  # Verde Claro
    '#00233B',  # Azul Escuro
    '#EFEBDC',  # Bege Claro
    '#F2F1EF',  # Cinza Acetinado
    '#6a8a4a',  # Verde Médio
    '#7da058',  # Verde Claro 2
    '#0a3d5f',  # Azul Médio
]

# Escala de cores para heatmaps e gradientes
ESCALA_CORES = [
    [0, CORES['destaque']],
    [0.5, CORES['secundario']],
    [1, CORES['primario']]
]
