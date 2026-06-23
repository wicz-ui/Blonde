import os
import sys

from flask import Flask, g, url_for

from utils.config import STATIC_VERSION
from utils.database import close_db
from utils.helpers import (
    formatar_celular,
    formatar_cpf,
    formatar_moeda,
    status_cartao_filter,
)
from utils.migrate import init_db


app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "catraca-demo-secret")
app.teardown_appcontext(close_db)


@app.context_processor
def injetar_contexto_acesso():
    def url_acesso(endpoint, **valores):
        return url_for(endpoint, **valores)

    return {
        "dispositivo": getattr(g, "dispositivo", None),
        "acesso": getattr(g, "acesso", None),
        "static_version": STATIC_VERSION,
        "url_acesso": url_acesso,
    }


@app.template_filter("moeda")
def moeda_filter(valor):
    return formatar_moeda(valor)


@app.template_filter("status_cartao")
def status_cartao_template(status):
    return status_cartao_filter(status)


@app.template_filter("cpf")
def cpf_filter(valor):
    return formatar_cpf(valor)


@app.template_filter("celular")
def celular_filter(valor):
    return formatar_celular(valor)


init_db()

# Importar os módulos registra as rotas no objeto Flask compartilhado acima.
# Ao executar `python app.py`, este módulo se chama `__main__`. O alias evita
# que os módulos de rota importem uma segunda instância de `app`.
if __name__ == "__main__":
    sys.modules.setdefault("app", sys.modules[__name__])

from routes import admin, catraca, dispositivos, main, usuario  # noqa: E402, F401


if __name__ == "__main__":
    porta = int(os.getenv("PORT", "5000"))
    modo_debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=porta, debug=modo_debug)
