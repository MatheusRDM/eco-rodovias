"""
Proteção de autenticação para páginas individuais.
A senha só é solicitada ao abrir o app pela primeira vez ou após clicar em Sair.
Navegação entre páginas não requer nova autenticação (session_state persiste).
"""
import streamlit as st
from auth import verificar_autenticacao, tem_acesso_pagina, fazer_logout

def proteger_pagina(nome_pagina):
    """
    Protege uma página verificando autenticação e permissão.
    Se não autenticado, redireciona automaticamente para o login (app.py).
    """
    # Se não estiver autenticado, redireciona silenciosamente para o login
    if not verificar_autenticacao():
        st.switch_page("app.py")
        st.stop()

    # Verificar permissão para a página específica
    usuario = st.session_state.get('usuario', '')
    if not tem_acesso_pagina(usuario, nome_pagina):
        st.error(f"Sem permissão para acessar: {nome_pagina}")
        if st.button("Voltar ao Menu"):
            st.switch_page("app.py")
        st.stop()

    # Info do usuário + botão Sair na sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown(
        f"<span style='font-size:0.82rem;color:#BFCF99;'>👤 {usuario}</span>"
        f"<br><span style='font-size:0.75rem;color:#aaa;'>{nome_pagina}</span>",
        unsafe_allow_html=True,
    )
    st.sidebar.markdown("")
    if st.sidebar.button("SAIR", use_container_width=True, key=f"logout_{nome_pagina}"):
        fazer_logout()
