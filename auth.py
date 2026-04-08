"""
Módulo de Autenticação e Controle de Acesso
Credenciais carregadas de st.secrets (cloud) ou fallback local (dev).
Suporte a login persistente via cookie (token HMAC).
"""
import hashlib
import hmac
import time

import streamlit as st
from cloud_config import get_usuarios, get_logo_path

# Usuários e senhas — carregados dinamicamente
USUARIOS = get_usuarios()

# Mapeamento de páginas para arquivos
PAGINA_ARQUIVO = {
    "Dashboard de Certificados": "pages/01_Dashboard_Certificados.py",
    "Cronograma de Ensaios": "pages/02_Cronograma_Relatorios.py",
    "EPR Litoral Pioneiro": "pages/03_EPR_Litoral_Pioneiro.py",
    "Mapeamento de Projetos CAUQ": "pages/04_Mapeamento_CAUQ.py",
    "Eco Rodovias": "pages/06_Eco_Rodovias.py"
}

# ── Cookie / token helpers ────────────────────────────────────────────────────
_COOKIE_NAME = "ae_auth_token"
_COOKIE_DAYS = 30          # validade do cookie
_SECRET_KEY  = "afirma-evias-2026-management"  # chave para HMAC

def _gerar_token(usuario: str) -> str:
    """Gera token HMAC: usuario:expiry:signature."""
    expiry = int(time.time()) + _COOKIE_DAYS * 86400
    payload = f"{usuario}:{expiry}"
    sig = hmac.new(_SECRET_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()[:24]
    return f"{payload}:{sig}"


def _validar_token(token: str) -> str | None:
    """Valida token e retorna username ou None."""
    try:
        parts = token.split(":")
        if len(parts) != 3:
            return None
        usuario, expiry_str, sig = parts
        expiry = int(expiry_str)
        if time.time() > expiry:
            return None
        expected = hmac.new(
            _SECRET_KEY.encode(), f"{usuario}:{expiry_str}".encode(), hashlib.sha256
        ).hexdigest()[:24]
        if not hmac.compare_digest(sig, expected):
            return None
        if usuario not in USUARIOS:
            return None
        return usuario
    except Exception:
        return None


def _js_set_cookie(token: str):
    """Injeta JS para definir cookie no navegador."""
    import streamlit.components.v1 as components
    max_age = _COOKIE_DAYS * 86400
    components.html(
        f"""<script>
        document.cookie = "{_COOKIE_NAME}={token}; path=/; max-age={max_age}; SameSite=Lax";
        </script>""",
        height=0,
    )


def _js_clear_cookie():
    """Remove cookie do navegador."""
    import streamlit.components.v1 as components
    components.html(
        f"""<script>
        document.cookie = "{_COOKIE_NAME}=; path=/; max-age=0; SameSite=Lax";
        </script>""",
        height=0,
    )


def _js_read_cookie_to_query():
    """
    Injeta JS que lê o cookie e, se encontrado, coloca o valor
    em ?ae_auth_token=... via query param para o Streamlit ler.
    Isso acontece APENAS no primeiro carregamento (sem session_state).
    """
    import streamlit.components.v1 as components
    components.html(
        f"""<script>
        (function() {{
            var match = document.cookie.match('(^|;)\\\\s*{_COOKIE_NAME}\\\\s*=\\\\s*([^;]+)');
            if (match) {{
                var token = match[2];
                var url = new URL(window.parent.location.href);
                if (!url.searchParams.has('{_COOKIE_NAME}')) {{
                    url.searchParams.set('{_COOKIE_NAME}', token);
                    window.parent.history.replaceState(null, '', url.toString());
                    window.parent.location.reload();
                }}
            }}
        }})();
        </script>""",
        height=0,
    )


def _tentar_auto_login() -> bool:
    """
    Tenta restaurar sessão a partir de cookie (via query params).
    Retorna True se conseguiu auto-login.
    """
    # Checa query params por token do cookie
    params = st.query_params
    token = params.get(_COOKIE_NAME)
    if not token:
        return False

    usuario = _validar_token(token)
    if not usuario:
        # Token inválido/expirado — limpa
        try:
            del st.query_params[_COOKIE_NAME]
        except Exception:
            pass
        return False

    # Auto-login bem-sucedido
    st.session_state['logado'] = True
    st.session_state['usuario'] = usuario
    st.session_state['paginas_permitidas'] = get_paginas_permitidas(usuario)
    # Limpa query param para URL ficar limpa
    try:
        del st.query_params[_COOKIE_NAME]
    except Exception:
        pass
    return True


# ── Funções públicas ──────────────────────────────────────────────────────────

def verificar_login(usuario, senha):
    """Verifica se o usuário e senha estão corretos"""
    if usuario in USUARIOS and USUARIOS[usuario]["senha"] == senha:
        return True
    return False

def get_paginas_permitidas(usuario):
    """Retorna a lista de páginas permitidas para o usuário"""
    if usuario in USUARIOS:
        return USUARIOS[usuario]["paginas"]
    return []

def tem_acesso_pagina(usuario, pagina):
    """Verifica se o usuário tem acesso à página específica"""
    paginas_permitidas = get_paginas_permitidas(usuario)
    return pagina in paginas_permitidas

def mostrar_tela_login():
    """Mostra a tela de login centralizada usando colunas do Streamlit"""

    # ── Tenta auto-login por cookie antes de mostrar o form ────────────────
    if _tentar_auto_login():
        st.rerun()
        return

    # Injeta JS para ler cookie uma vez (sem bloquear o render)
    if _COOKIE_NAME not in st.query_params and not st.session_state.get("_cookie_check_done"):
        st.session_state["_cookie_check_done"] = True
        _js_read_cookie_to_query()
        # Não chama st.stop() — continua renderizando o formulário normalmente

    # ── Tela de login normal ───────────────────────────────────────────────
    # CSS mínimo para esconder sidebar + rótulo dev fixo
    st.markdown("""
    <style>
        div[data-testid="stSidebar"] {
            display: none !important;
        }
        div[data-testid="collapsedControl"] {
            display: none !important;
        }
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
    </style>
    <div class="dev-label-fixed">Developed By: Matheus Resende</div>
    """, unsafe_allow_html=True)

    # Criar colunas para centralização [margem_esq, centro, margem_dir]
    col_esq, col_centro, col_dir = st.columns([1, 1.2, 1])

    with col_centro:
        # Espaço para descer o card na tela
        st.write("")
        st.write("")
        st.write("")

        # Logo centralizada
        _logo = get_logo_path("horizontal")
        if _logo:
            try:
                st.image(_logo, width=840, use_container_width=False)
            except Exception:
                _logo = None
        if not _logo:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #566E3D 0%, #6a8a4a 100%);
                        padding: 1.5rem; border-radius: 16px; border: 3px solid #BFCF99;
                        text-align: center; margin-bottom: 1.5rem;">
                <h2 style="color: white; margin: 0; font-size: 1.8rem;">AFIRMA E-VIAS</h2>
                <p style="color: #BFCF99; margin: 0.5rem 0 0 0;">Sistema de Gestão de Ensaios</p>
            </div>
            """, unsafe_allow_html=True)

        # Card de login
        with st.container():
            st.markdown("""
            <style>
            .login-card {
                background: linear-gradient(135deg, #566E3D 0%, #6a8a4a 100%);
                border-radius: 16px;
                border: 3px solid #BFCF99;
                padding: 2rem;
                box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                margin: 0 auto;
            }
            .login-title {
                color: white;
                text-align: center;
                margin-bottom: 1.5rem;
                font-size: 3.5rem;
            }
            </style>
            <div class="login-card">
                <h3 class="login-title"> Login</h3>
            </div>
            """, unsafe_allow_html=True)

            # Formulário dentro do card
            usuario = st.text_input("Usuário", placeholder="Digite seu usuário")
            senha = st.text_input("Senha", type="password", placeholder="Digite sua senha")

            if st.button("Entrar", use_container_width=True):
                if verificar_login(usuario, senha):
                    st.session_state['logado'] = True
                    st.session_state['usuario'] = usuario
                    st.session_state['paginas_permitidas'] = get_paginas_permitidas(usuario)
                    # Gera e salva cookie persistente
                    token = _gerar_token(usuario)
                    _js_set_cookie(token)
                    st.success("Login realizado com sucesso!")
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos!")

def verificar_autenticacao():
    """Verifica se o usuário está autenticado (session_state ou cookie)."""
    if st.session_state.get('logado', False):
        return True
    # Tenta restaurar via cookie/query param
    return _tentar_auto_login()

def fazer_logout():
    """Realiza o logout do usuário e limpa cookie."""
    _js_clear_cookie()
    for key in ['logado', 'usuario', 'paginas_permitidas', '_cookie_check_done']:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()
