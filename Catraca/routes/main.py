from flask import flash, g, redirect, render_template, request, session, url_for

from app import app
from utils.auth import buscar_acesso_por_credenciais, acesso_requerido
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

    session.clear()
    session["token_acesso"] = acesso["token_acesso"]
    endpoint = endpoint_do_dispositivo(acesso["tipo"])
    return redirect(url_for(endpoint))


@app.route("/cartao", methods=["GET", "POST"])
@acesso_requerido("usuario")
def visualizar_cartao():
    if g.acesso["tipo"] == "usuario":
        return redirect(url_for("usuario_meu_cartao"))
    return redirect(url_for("admin_cartoes"))


@app.get("/meu/<token_usuario>")
def acesso_rapido_usuario(token_usuario):
    flash("O acesso ao cartão exige login com as credenciais do passageiro.")
    return redirect(url_for("login"))


@app.post("/logout")
def logout():
    session.clear()
    flash("Sessão encerrada.")
    return redirect(url_for("login"))


@app.get("/health")
def health():
    return {"status": "ok"}
