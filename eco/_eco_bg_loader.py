"""
_eco_bg_loader.py — Background task loading utilities for ECO Rodovias.

Pattern:
  1. start_bg_task(key, fn, *args, **kwargs)  → starts fn in a daemon thread
  2. A @st.fragment(run_every=2) in 06_Eco_Rodovias.py polls every 2s
  3. Button shows pulsing green 'Carregando…' while task runs

Thread safety: st.session_state writes from background threads are supported
in Streamlit >= 1.33 (this project targets >= 1.32, tested on 1.49).
"""
import threading
import streamlit as st

_PFX = "_bg_"   # session_state key namespace

# ─── CSS do botão de carregando ──────────────────────────────────────────────
CSS_LOADING_BTN = """
<style>
.eco-loading-btn {
  display: flex; align-items: center; justify-content: center; gap: 6px;
  width: 100%; padding: 5px 12px; border-radius: 6px;
  background: #1b4332; border: 1px solid #2d6a4f;
  color: #95d5b2; font-size: .82rem; font-weight: 600;
  cursor: wait; white-space: nowrap; user-select: none;
  box-sizing: border-box; min-height: 38px; line-height: 1;
  animation: eco-btn-pulse 1.5s ease-in-out infinite;
}
@keyframes eco-btn-pulse {
  0%,100% { background:#1b4332; border-color:#2d6a4f; color:#95d5b2; }
  50%      { background:#2d6a4f; border-color:#52b788; color:#d8f3dc; }
}
</style>
"""


# ─── Core helpers ─────────────────────────────────────────────────────────────

def start_bg_task(key: str, fn, *args, **kwargs) -> bool:
    """
    Run fn(*args, **kwargs) in a daemon thread.

    On success → session_state[_bg_{key}_result] = return value
    On failure → session_state[_bg_{key}_error]  = str(exception)
    Always    → session_state[_bg_{key}_running] = False when done

    Returns False if a task with this key is already running.
    """
    if st.session_state.get(f"{_PFX}{key}_running"):
        return False
    st.session_state[f"{_PFX}{key}_running"] = True
    st.session_state[f"{_PFX}{key}_error"]   = None
    st.session_state.pop(f"{_PFX}{key}_result", None)

    def _worker():
        try:
            result = fn(*args, **kwargs)
            st.session_state[f"{_PFX}{key}_result"] = result
        except Exception as exc:
            st.session_state[f"{_PFX}{key}_error"] = str(exc)
        finally:
            st.session_state[f"{_PFX}{key}_running"] = False

    threading.Thread(target=_worker, daemon=True).start()
    return True


def is_loading(key: str) -> bool:
    return bool(st.session_state.get(f"{_PFX}{key}_running", False))


def has_result(key: str) -> bool:
    return f"{_PFX}{key}_result" in st.session_state


def has_error(key: str) -> bool:
    v = st.session_state.get(f"{_PFX}{key}_error")
    return v is not None


def pop_result(key: str):
    """Consume (remove) the result from session_state and return it."""
    return st.session_state.pop(f"{_PFX}{key}_result", None)


def pop_error(key: str) -> str | None:
    """Consume (remove) the error from session_state and return it."""
    v = st.session_state.pop(f"{_PFX}{key}_error", None)
    return v if v else None


# ─── UI helper ────────────────────────────────────────────────────────────────

def render_atualizar_btn(label: str, key: str, **btn_kwargs) -> bool:
    """
    Renders a normal Streamlit button when idle, or a pulsing green
    'Carregando…' HTML button when the background task `key` is running.
    Returns True only when the user freshly clicks the idle button.
    """
    if is_loading(key):
        st.markdown(
            CSS_LOADING_BTN +
            '<div class="eco-loading-btn">↺ Carregando…</div>',
            unsafe_allow_html=True,
        )
        return False
    return st.button(label, key=key, **btn_kwargs)
