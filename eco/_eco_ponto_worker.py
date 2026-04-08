"""
_eco_ponto_worker.py — Worker isolado para automação PontoMais via Playwright.
Executado em subprocess separado pelo Streamlit para evitar conflito de file descriptors.

Usage:
    python _eco_ponto_worker.py LOGIN SENHA DATA_INI DATA_FIM OUTPUT_PATH
"""
import sys
import os

# Garante que o diretório pages/ está no sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _eco_pontomais_sync import baixar_espelho_ponto

if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Uso: python _eco_ponto_worker.py LOGIN SENHA DATA_INI DATA_FIM OUTPUT_PATH", file=sys.stderr)
        sys.exit(1)

    login, senha, data_ini, data_fim, out_path = sys.argv[1:6]

    def _prog(msg: str):
        print(msg, flush=True)   # capturado pelo processo pai via stdout

    try:
        df = baixar_espelho_ponto(
            login=login,
            senha=senha,
            data_ini=data_ini,
            data_fim=data_fim,
            progresso_cb=_prog,
        )
        df.to_excel(out_path, index=False)
        print(f"DONE:{len(df)}", flush=True)
        sys.exit(0)
    except Exception as e:
        print(f"ERRO: {e}", file=sys.stderr, flush=True)
        sys.exit(1)
