from functools import wraps
from flask import flash, g, redirect, render_template, request, session, url_for

from .database import get_db
from .helpers import extrair_codigo_publico


def token_da_requisicao():
    return session.get("token_acesso", "").strip()


def buscar_acesso(token):
    if not token:
        return None

    dispositivo = get_db().execute(
        """
        SELECT
            dispositivos.id,
            dispositivos.nome_dispositivo,
            dispositivos.tipo,
            dispositivos.token_acesso,
            dispositivos.ativo,
            dispositivos.cartao_id,
            dispositivos.usuario_id,
            dispositivos.estacao_id
        FROM dispositivos
        WHERE token_acesso = ? AND ativo = 1
        """,
        (token,),
    ).fetchone()
    if dispositivo:
        acesso = dict(dispositivo)
        acesso["origem_token"] = "dispositivo"
        if acesso["tipo"] == "usuario" and not acesso.get("usuario_id") and acesso.get("cartao_id"):
            cartao = get_db().execute(
                "SELECT usuario_id FROM cartoes WHERE id = ?",
                (acesso["cartao_id"],),
            ).fetchone()
            if cartao:
                acesso["usuario_id"] = cartao["usuario_id"]
        return acesso

    usuario = get_db().execute(
        """
        SELECT id, nome, token_usuario, ativo
        FROM usuarios
        WHERE token_usuario = ? AND ativo = 1
        """,
        (token,),
    ).fetchone()
    if usuario:
        return {
            "id": None,
            "nome_dispositivo": f"Passageiro: {usuario['nome']}",
            "tipo": "usuario",
            "token_acesso": usuario["token_usuario"],
            "ativo": usuario["ativo"],
            "cartao_id": None,
            "usuario_id": usuario["id"],
            "estacao_id": None,
            "origem_token": "usuario",
        }
    return None


def buscar_acesso_por_credenciais(usuario, senha):
    if not usuario or not senha:
        return None

    usuario = usuario.strip()
    senha = senha.strip()
    usuario_lower = usuario.lower()

    if usuario_lower in {"admin", "catraca"}:
        dispositivo = get_db().execute(
            """
            SELECT
                dispositivos.id,
                dispositivos.nome_dispositivo,
                dispositivos.tipo,
                dispositivos.token_acesso,
                dispositivos.ativo,
                dispositivos.cartao_id,
                dispositivos.usuario_id,
                dispositivos.estacao_id
            FROM dispositivos
            WHERE tipo = ? AND token_acesso = ? AND ativo = 1
            """,
            (usuario_lower, senha),
        ).fetchone()
    else:
        dispositivo = get_db().execute(
            """
            SELECT
                dispositivos.id,
                dispositivos.nome_dispositivo,
                dispositivos.tipo,
                dispositivos.token_acesso,
                dispositivos.ativo,
                dispositivos.cartao_id,
                dispositivos.usuario_id,
                dispositivos.estacao_id
            FROM dispositivos
            LEFT JOIN cartoes ON cartoes.id = dispositivos.cartao_id
            WHERE dispositivos.tipo = 'usuario'
              AND dispositivos.token_acesso = ?
              AND dispositivos.ativo = 1
              AND (
                  LOWER(dispositivos.nome_dispositivo) = LOWER(?)
                  OR cartoes.codigo_publico = ?
              )
            """,
            (senha, usuario, usuario),
        ).fetchone()
    if not dispositivo:
        return None

    acesso = dict(dispositivo)
    acesso["origem_token"] = "dispositivo"
    if acesso["tipo"] == "usuario" and not acesso.get("usuario_id") and acesso.get("cartao_id"):
        cartao = get_db().execute(
            "SELECT usuario_id FROM cartoes WHERE id = ?",
            (acesso["cartao_id"],),
        ).fetchone()
        if cartao:
            acesso["usuario_id"] = cartao["usuario_id"]
    return acesso


def acesso_requerido(*tipos_permitidos):
    def decorar(funcao):
        @wraps(funcao)
        def autorizar(*args, **kwargs):
            token = token_da_requisicao()
            acesso = buscar_acesso(token)

            if acesso is None:
                flash("Faça login para acessar esta área.")
                return redirect(url_for("login"))

            g.acesso = acesso
            g.dispositivo = acesso

            if acesso["tipo"] != "admin" and acesso["tipo"] not in tipos_permitidos:
                return (
                    render_template(
                        "acesso_negado.html",
                        titulo="Área não permitida",
                        mensagem="Este acesso não possui permissão para abrir esta tela.",
                    ),
                    403,
                )

            return funcao(*args, **kwargs)

        return autorizar

    return decorar
