from flask import redirect, render_template, request, url_for

from app import app
from utils.auth import acesso_requerido
from utils.queries import estacao_catraca_atual
from utils.config import valor_passagem_atual
from utils.validation import validar_entrada_por_token_privado, validar_entrada


@app.get("/catraca")
@acesso_requerido("catraca")
def catraca():
    return render_template(
        "catraca.html",
        valor_passagem=valor_passagem_atual(),
        estacao=estacao_catraca_atual(),
    )


@app.post("/validar-catraca")
@app.post("/catraca/validar")
@acesso_requerido("catraca")
def validar_catraca():
    token_privado = (request.form.get("cartao_id", "") or "").strip()
    resultado = validar_entrada_por_token_privado(token_privado)
    return render_template(
        "catraca.html",
        valor_passagem=valor_passagem_atual(),
        resultado=resultado,
        cartao_id=token_privado,
        estacao=estacao_catraca_atual(),
    )
