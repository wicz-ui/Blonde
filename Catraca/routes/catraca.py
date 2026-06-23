from flask import redirect, render_template, request, url_for

from app import app
from utils.auth import acesso_requerido
from utils.queries import estacao_catraca_atual
from utils.config import valor_passagem_atual
from utils.validation import validar_entrada, validar_entrada_por_token_privado


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
    identificador_cartao = (request.form.get("cartao_id", "") or "").strip()
    tipo_leitura = request.form.get("tipo_leitura", "token_privado")
    if tipo_leitura == "qr_publico":
        resultado = validar_entrada(identificador_cartao)
    else:
        resultado = validar_entrada_por_token_privado(identificador_cartao)
    return render_template(
        "catraca.html",
        valor_passagem=valor_passagem_atual(),
        resultado=resultado,
        cartao_id=identificador_cartao,
        estacao=estacao_catraca_atual(),
    )
