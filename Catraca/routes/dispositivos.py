from flask import flash, g, redirect, render_template, request, url_for

from app import app
from utils.auth import acesso_requerido
from utils.config import TIPOS_DISPOSITIVO
from utils.database import get_db
from utils.helpers import gerar_token_acesso
from utils.queries import estacoes_ativas
from utils.queries import estacao_padrao_id


@app.route("/dispositivos", methods=["GET", "POST"])
@app.route("/admin/dispositivos", methods=["GET", "POST"])
@acesso_requerido("admin")
def dispositivos():
    erro = None
    dados_form = {
        "nome_dispositivo": "",
        "tipo": "catraca",
        "cartao_id": "",
        "estacao_id": str(estacao_padrao_id() or ""),
    }

    if request.method == "POST":
        dados_form = {
            "nome_dispositivo": request.form.get("nome_dispositivo", "").strip(),
            "tipo": request.form.get("tipo", "").strip(),
            "cartao_id": request.form.get("cartao_id", "").strip(),
            "estacao_id": request.form.get("estacao_id", "").strip(),
        }
        if not dados_form["nome_dispositivo"]:
            erro = "Informe o nome do dispositivo."
        elif dados_form["tipo"] not in TIPOS_DISPOSITIVO:
            erro = "Informe um tipo de dispositivo valido."

        usuario_id = None
        cartao_id = None
        estacao_id = None
        if not erro and dados_form["tipo"] == "usuario" and dados_form["cartao_id"]:
            if not dados_form["cartao_id"].isdigit():
                erro = "Informe um cartao valido."
            else:
                cartao = get_db().execute(
                    "SELECT id, usuario_id FROM cartoes WHERE id = ?",
                    (int(dados_form["cartao_id"]),),
                ).fetchone()
                if not cartao:
                    erro = "O cartao informado nao existe."
                else:
                    usuario_id = cartao["usuario_id"]
                    cartao_id = cartao["id"]
        if not erro and dados_form["tipo"] == "catraca":
            estacao_id = int(dados_form["estacao_id"]) if dados_form["estacao_id"].isdigit() else estacao_padrao_id()

        if not erro:
            try:
                get_db().execute(
                    """
                    INSERT INTO dispositivos (
                        nome_dispositivo, tipo, token_acesso, ativo,
                        cartao_id, usuario_id, estacao_id
                    )
                    VALUES (?, ?, ?, 1, ?, ?, ?)
                    """,
                    (
                        dados_form["nome_dispositivo"],
                        dados_form["tipo"],
                        gerar_token_acesso(),
                        cartao_id,
                        usuario_id,
                        estacao_id,
                    ),
                )
                flash("Dispositivo criado. O link de acesso ja esta disponivel.")
                return redirect(url_for("dispositivos"))
            except Exception:
                erro = "Nao foi possivel criar o dispositivo."

    db = get_db()
    lista_dispositivos = db.execute(
        """
        SELECT
            dispositivos.*,
            cartoes.codigo_publico,
            usuarios.nome AS nome_passageiro,
            estacoes.nome AS estacao_nome
        FROM dispositivos
        LEFT JOIN cartoes ON cartoes.id = dispositivos.cartao_id
        LEFT JOIN usuarios ON usuarios.id = dispositivos.usuario_id
        LEFT JOIN estacoes ON estacoes.id = dispositivos.estacao_id
        ORDER BY dispositivos.id
        """
    ).fetchall()
    cartoes = db.execute(
        """
        SELECT cartoes.id, cartoes.codigo_publico, usuarios.nome AS nome_passageiro
        FROM cartoes
        JOIN usuarios ON usuarios.id = cartoes.usuario_id
        ORDER BY usuarios.nome, cartoes.id
        """
    ).fetchall()
    estacoes = estacoes_ativas()
    links_acesso = {
        dispositivo["id"]: url_for("login", _external=True)
        for dispositivo in lista_dispositivos
    }
    credenciais_login = {
        dispositivo["id"]: {
            "usuario": {
                "admin": "admin",
                "catraca": "catraca",
                "usuario": dispositivo["codigo_publico"]
                or dispositivo["nome_dispositivo"],
            }[dispositivo["tipo"]],
            "senha": dispositivo["token_acesso"],
        }
        for dispositivo in lista_dispositivos
    }

    return render_template(
        "dispositivos.html",
        lista_dispositivos=lista_dispositivos,
        cartoes=cartoes,
        estacoes=estacoes,
        links_acesso=links_acesso,
        credenciais_login=credenciais_login,
        erro=erro,
        dados_form=dados_form,
    )


@app.post("/dispositivos/<int:dispositivo_id>/vincular")
@acesso_requerido("admin")
def vincular_dispositivo(dispositivo_id):
    cartao_id_texto = request.form.get("cartao_id", "").strip()
    estacao_id_texto = request.form.get("estacao_id", "").strip()
    db = get_db()
    dispositivo = db.execute("SELECT id, tipo FROM dispositivos WHERE id = ?", (dispositivo_id,)).fetchone()

    if not dispositivo:
        flash("Dispositivo nao encontrado.")
    elif dispositivo["tipo"] == "usuario":
        if not cartao_id_texto.isdigit():
            flash("Informe um cartao valido.")
        else:
            cartao = db.execute(
                "SELECT id, usuario_id FROM cartoes WHERE id = ?", (int(cartao_id_texto),)
            ).fetchone()
            if not cartao:
                flash("O cartao informado nao existe.")
            else:
                db.execute(
                    "UPDATE dispositivos SET cartao_id = ?, usuario_id = ? WHERE id = ?",
                    (cartao["id"], cartao["usuario_id"], dispositivo_id),
                )
                flash("Usuario vinculado ao dispositivo.")
    elif dispositivo["tipo"] == "catraca":
        if not estacao_id_texto.isdigit():
            flash("Informe uma estacao valida.")
        else:
            db.execute(
                "UPDATE dispositivos SET estacao_id = ? WHERE id = ?",
                (int(estacao_id_texto), dispositivo_id),
            )
            flash("Estacao da catraca atualizada.")

    return redirect(url_for("dispositivos"))


@app.post("/dispositivos/<int:dispositivo_id>/alternar")
@acesso_requerido("admin")
def alternar_dispositivo(dispositivo_id):
    if dispositivo_id == g.acesso.get("id"):
        flash("O dispositivo administrativo em uso nao pode ser desativado.")
        return redirect(url_for("dispositivos"))

    dispositivo = get_db().execute(
        "SELECT id, ativo FROM dispositivos WHERE id = ?", (dispositivo_id,)
    ).fetchone()
    if not dispositivo:
        flash("Dispositivo nao encontrado.")
    else:
        novo_status = 0 if dispositivo["ativo"] else 1
        get_db().execute(
            "UPDATE dispositivos SET ativo = ? WHERE id = ?",
            (novo_status, dispositivo_id),
        )
        flash("Status do dispositivo atualizado.")

    return redirect(url_for("dispositivos"))
