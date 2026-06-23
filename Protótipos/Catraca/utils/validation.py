import sqlite3
from decimal import Decimal

from .database import get_db
from .helpers import extrair_codigo_publico
from .queries import estacao_catraca_atual, trecho_compativel_com_estacao, registrar_passagem
from .config import valor_passagem_atual
from .migrate import limpar_historico_expirado


def _negado(cartao_id, cartao_digitado, motivo, origem_id, destino_id=None):
    return {
        "aprovado": False,
        "titulo": "Entrada negada.",
        "mensagem": motivo,
        "codigo_publico": None,
    }


def _aprovado(codigo_publico):
    return {
        "aprovado": True,
        "titulo": "Entrada aprovada.",
        "mensagem": "Boa viagem!",
        "codigo_publico": codigo_publico,
    }


def validar_entrada(cartao_digitado):
    db = get_db()
    token = extrair_codigo_publico(cartao_digitado)
    estacao = estacao_catraca_atual()
    origem_id = estacao["id"] if estacao else None
    valor_passagem = valor_passagem_atual()
    db.execute("BEGIN IMMEDIATE")
    try:
        if not token:
            registrar_passagem(
                db,
                None,
                cartao_digitado,
                "negado",
                "Token privado nao informado.",
                Decimal("0.00"),
                origem_id=origem_id,
            )
            db.execute("COMMIT")
            return _negado(None, cartao_digitado, "Token privado nao informado.", origem_id)

        cartao = db.execute(
            """
            SELECT
                cartoes.*,
                usuarios.nome AS nome_usuario
            FROM cartoes
            JOIN usuarios ON usuarios.id = cartoes.usuario_id
            WHERE cartoes.codigo_publico = ?
            """,
            (token,),
        ).fetchone()

        if cartao is None:
            registrar_passagem(
                db,
                None,
                cartao_digitado,
                "negado",
                "Cartao nao encontrado.",
                Decimal("0.00"),
                origem_id=origem_id,
            )
            db.execute("COMMIT")
            return _negado(None, cartao_digitado, "Cartao nao encontrado.", origem_id)

        destino_id = None
        rota, trecho = trecho_compativel_com_estacao(cartao, origem_id)
        if rota and not trecho:
            registrar_passagem(
                db,
                cartao["id"],
                cartao_digitado,
                "negado",
                "Estacao fora da rota planejada.",
                Decimal("0.00"),
                origem_id=origem_id,
            )
            db.execute("COMMIT")
            return {
                "aprovado": False,
                "titulo": "Entrada negada.",
                "mensagem": "Estacao fora da rota planejada.",
                "codigo_publico": cartao["codigo_publico"],
            }
        if trecho:
            destino_id = trecho["destino_id"]

        saldo_atual = Decimal(str(cartao["saldo"])).quantize(Decimal("0.01"))
        if cartao["status"] != "ativo":
            registrar_passagem(
                db,
                cartao["id"],
                cartao_digitado,
                "negado",
                "Cartao bloqueado.",
                Decimal("0.00"),
                origem_id=origem_id,
                destino_id=destino_id,
            )
            db.execute("COMMIT")
            return {
                "aprovado": False,
                "titulo": "Entrada negada.",
                "mensagem": "Cartao bloqueado.",
                "codigo_publico": cartao["codigo_publico"],
            }

        if saldo_atual < valor_passagem:
            registrar_passagem(
                db,
                cartao["id"],
                cartao_digitado,
                "negado",
                "Saldo insuficiente.",
                Decimal("0.00"),
                origem_id=origem_id,
                destino_id=destino_id,
            )
            db.execute("COMMIT")
            return {
                "aprovado": False,
                "titulo": "Entrada negada.",
                "mensagem": "Saldo insuficiente.",
                "codigo_publico": cartao["codigo_publico"],
            }

        novo_saldo = saldo_atual - valor_passagem
        db.execute("UPDATE cartoes SET saldo = ? WHERE id = ?", (float(novo_saldo), cartao["id"]))
        registrar_passagem(
            db,
            cartao["id"],
            cartao_digitado,
            "aprovado",
            "Entrada liberada.",
            valor_passagem,
            origem_id=origem_id,
            destino_id=destino_id,
        )
        limpar_historico_expirado(db)
        db.execute("COMMIT")
        response = _aprovado(cartao["codigo_publico"])
        response["codigo_publico"] = cartao["codigo_publico"]
        return response
    except sqlite3.Error:
        db.execute("ROLLBACK")
        return {"aprovado": False, "titulo": "Entrada negada.", "mensagem": "Falha ao validar. Tente novamente."}


def validar_entrada_por_token_privado(token_privado):
    db = get_db()
    token = (token_privado or "").strip()
    estacao = estacao_catraca_atual()
    origem_id = estacao["id"] if estacao else None
    valor_passagem = valor_passagem_atual()
    db.execute("BEGIN IMMEDIATE")
    try:
        if not token:
            registrar_passagem(
                db,
                None,
                token,
                "negado",
                "Token privado nao informado.",
                Decimal("0.00"),
                origem_id=origem_id,
            )
            db.execute("COMMIT")
            return _negado(None, token, "Token privado nao informado.", origem_id)

        cartao = db.execute(
            """
            SELECT
                cartoes.*,
                usuarios.nome AS nome_usuario,
                usuarios.token_usuario
            FROM cartoes
            JOIN usuarios ON usuarios.id = cartoes.usuario_id
            WHERE usuarios.token_usuario = ?
            """,
            (token,),
        ).fetchone()

        if cartao is None:
            registrar_passagem(
                db,
                None,
                token,
                "negado",
                "Cartao nao encontrado.",
                Decimal("0.00"),
                origem_id=origem_id,
            )
            db.execute("COMMIT")
            return _negado(None, token, "Cartao nao encontrado.", origem_id)

        destino_id = None
        rota, trecho = trecho_compativel_com_estacao(cartao, origem_id)
        if rota and not trecho:
            registrar_passagem(
                db,
                cartao["id"],
                token,
                "negado",
                "Estacao fora da rota planejada.",
                Decimal("0.00"),
                origem_id=origem_id,
            )
            db.execute("COMMIT")
            return {
                "aprovado": False,
                "titulo": "Entrada negada.",
                "mensagem": "Estacao fora da rota planejada.",
                "codigo_publico": cartao["codigo_publico"],
            }
        if trecho:
            destino_id = trecho["destino_id"]

        saldo_atual = Decimal(str(cartao["saldo"])).quantize(Decimal("0.01"))
        if cartao["status"] != "ativo":
            registrar_passagem(
                db,
                cartao["id"],
                token,
                "negado",
                "Cartao bloqueado.",
                Decimal("0.00"),
                origem_id=origem_id,
                destino_id=destino_id,
            )
            db.execute("COMMIT")
            return {
                "aprovado": False,
                "titulo": "Entrada negada.",
                "mensagem": "Cartao bloqueado.",
                "codigo_publico": cartao["codigo_publico"],
            }

        if saldo_atual < valor_passagem:
            registrar_passagem(
                db,
                cartao["id"],
                token,
                "negado",
                "Saldo insuficiente.",
                Decimal("0.00"),
                origem_id=origem_id,
                destino_id=destino_id,
            )
            db.execute("COMMIT")
            return {
                "aprovado": False,
                "titulo": "Entrada negada.",
                "mensagem": "Saldo insuficiente.",
                "codigo_publico": cartao["codigo_publico"],
            }

        novo_saldo = saldo_atual - valor_passagem
        db.execute("UPDATE cartoes SET saldo = ? WHERE id = ?", (float(novo_saldo), cartao["id"]))
        registrar_passagem(
            db,
            cartao["id"],
            token,
            "aprovado",
            "Entrada liberada.",
            valor_passagem,
            origem_id=origem_id,
            destino_id=destino_id,
        )
        limpar_historico_expirado(db)
        db.execute("COMMIT")
        response = _aprovado(cartao["codigo_publico"])
        response["codigo_publico"] = cartao["codigo_publico"]
        return response
    except sqlite3.Error:
        db.execute("ROLLBACK")
        return {"aprovado": False, "titulo": "Entrada negada.", "mensagem": "Falha ao validar. Tente novamente."}
