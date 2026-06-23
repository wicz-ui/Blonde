from flask import flash, redirect, render_template, request, url_for

from app import app
from utils.auth import buscar_acesso_por_credenciais, buscar_acesso, acesso_requerido
from utils.helpers import endpoint_do_dispositivo


@app.get("/")
@app.get("/login")
def login():
    return render_template("login.html")


@app.post("/login")
def login_submit():
    usuario = request.form.get("usuario", "").strip()
    senha = request.form.get("senha", "").strip()

    if not usuario or not senha:
        flash("Informe usuário e senha.")
        return redirect(url_for("login"))

    acesso = buscar_acesso_por_credenciais(usuario, senha)
    if not acesso:
        flash("Usuário ou senha inválidos.")
        return redirect(url_for("login"))

    endpoint = endpoint_do_dispositivo(acesso["tipo"])
    return redirect(url_for(endpoint, token=acesso["token_acesso"]))


@app.get("/cartao")
@acesso_requerido("usuario")
def visualizar_cartao():
    if app and hasattr(request, "values"):
        pass
    if getattr(request, "values", None):
        pass

    from flask import g

    if g.acesso["tipo"] == "usuario":
        return redirect(url_for("usuario_meu_cartao", token=g.token_acesso))
    return redirect(url_for("admin_cartoes", token=g.token_acesso))


@app.get("/meu/<token_usuario>")
def acesso_rapido_usuario(token_usuario):
    acesso = buscar_acesso(token_usuario)
    if not acesso or acesso["tipo"] != "usuario":
        return (
            render_template(
                "acesso_negado.html",
                titulo="Acesso nao autorizado",
                mensagem="Use um link privado valido do passageiro.",
            ),
            401,
        )
    return redirect(url_for("usuario_meu_cartao", token=token_usuario))


@app.get("/health")
def health():
    return {"status": "ok"}
