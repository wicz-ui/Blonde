from flask import flash, redirect, render_template, request, url_for

from app import app
from utils.auth import acesso_requerido
from utils.config import (
    CONFIG_PADRAO,
    config_bool,
    dias_retencao_recargas,
    horas_retencao_historico,
    set_config,
    valor_maximo_recarga,
    valor_minimo_recarga,
    valor_passagem_atual,
)
from utils.database import get_db
from utils.helpers import gerar_token_usuario, parse_int_positivo, parse_valor
from utils.migrate import limpar_historico_expirado
from utils.queries import gerar_id_cartao


@app.get("/admin")
@acesso_requerido("admin")
def admin_home():
    limpar_historico_expirado()
    db = get_db()
    contadores = {
        "cartoes": db.execute("SELECT COUNT(*) AS total FROM cartoes").fetchone()["total"],
        "usuarios": db.execute("SELECT COUNT(*) AS total FROM usuarios").fetchone()["total"],
        "recargas": db.execute("SELECT COUNT(*) AS total FROM recargas").fetchone()["total"],
        "estacoes": db.execute(
            "SELECT COUNT(*) AS total FROM estacoes WHERE ativa = 1"
        ).fetchone()["total"],
        "historico": db.execute("SELECT COUNT(*) AS total FROM passagens").fetchone()["total"],
    }
    return render_template(
        "index.html",
        valor_passagem=valor_passagem_atual(),
        retencao_horas=horas_retencao_historico(),
        contadores=contadores,
    )


@app.route("/criar-cartao", methods=["GET", "POST"])
@acesso_requerido("admin")
def criar_cartao():
    erro = None
    cartao_criado = None
    dados_form = {"nome_passageiro": "", "saldo": "20,00", "status": "ativo"}

    if request.method == "POST":
        dados_form = {
            "nome_passageiro": request.form.get("nome_passageiro", "").strip(),
            "saldo": request.form.get("saldo", "").strip(),
            "status": request.form.get("status", "ativo"),
        }
        saldo = parse_valor(dados_form["saldo"])

        if not dados_form["nome_passageiro"]:
            erro = "Informe o nome ficticio do passageiro."
        elif saldo is None:
            erro = "Informe um saldo inicial valido."
        elif dados_form["status"] not in {"ativo", "bloqueado"}:
            erro = "Informe um status valido para o cartao."
        else:
            db = get_db()
            db.execute("BEGIN IMMEDIATE")
            try:
                token_usuario = gerar_token_usuario(db)
                criado_em = __import__("utils.helpers").helpers.agora_formatado()
                usuario_cursor = db.execute(
                    """
                    INSERT INTO usuarios (nome, token_usuario, criado_em, ativo)
                    VALUES (?, ?, ?, 1)
                    """,
                    (dados_form["nome_passageiro"], token_usuario, criado_em),
                )
                usuario_id = usuario_cursor.lastrowid
                cartao_id = gerar_id_cartao(db)
                codigo_publico = str(cartao_id)
                db.execute(
                    """
                    INSERT INTO cartoes (
                        id, usuario_id, codigo_publico, nome_passageiro,
                        saldo, status, data_criacao, criado_em
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        cartao_id,
                        usuario_id,
                        codigo_publico,
                        dados_form["nome_passageiro"],
                        float(saldo),
                        dados_form["status"],
                        criado_em,
                        criado_em,
                    ),
                )
                db.execute(
                    """
                    INSERT INTO dispositivos (
                        nome_dispositivo, tipo, token_acesso, ativo,
                        usuario_id, cartao_id
                    ) VALUES (?, 'usuario', ?, 1, ?, ?)
                    """,
                    (
                        dados_form["nome_passageiro"],
                        token_usuario,
                        usuario_id,
                        cartao_id,
                    ),
                )
                db.execute("COMMIT")
                cartao_criado = db.execute(
                    """
                    SELECT
                        cartoes.*,
                        usuarios.nome AS nome_usuario,
                        usuarios.token_usuario
                    FROM cartoes
                    JOIN usuarios ON usuarios.id = cartoes.usuario_id
                    WHERE cartoes.id = ?
                    """,
                    (cartao_id,),
                ).fetchone()
                dados_form = {"nome_passageiro": "", "saldo": "20,00", "status": "ativo"}
            except Exception:
                db.execute("ROLLBACK")
                erro = "Nao foi possivel criar o cartao. Tente novamente."

    return render_template(
        "criar_cartao.html",
        erro=erro,
        cartao_criado=cartao_criado,
        dados_form=dados_form,
    )


@app.get("/admin/historico")
@app.get("/historico")
@acesso_requerido("admin")
def historico():
    limpar_historico_expirado()
    passagens = get_db().execute(
        """
        SELECT
            passagens.id,
            passagens.cartao_id,
            passagens.cartao_digitado,
            passagens.data_hora,
            passagens.status,
            passagens.motivo,
            passagens.valor_cobrado,
            passagens.expira_em,
            cartoes.codigo_publico,
            usuarios.nome AS nome_passageiro,
            origem.nome AS origem_nome,
            destino.nome AS destino_nome
        FROM passagens
        LEFT JOIN cartoes ON cartoes.id = passagens.cartao_id
        LEFT JOIN usuarios ON usuarios.id = cartoes.usuario_id
        LEFT JOIN estacoes origem ON origem.id = passagens.origem_id
        LEFT JOIN estacoes destino ON destino.id = passagens.destino_id
        ORDER BY passagens.id DESC
        LIMIT 100
        """
    ).fetchall()
    return render_template(
        "historico.html",
        passagens=passagens,
        retencao_horas=horas_retencao_historico(),
    )


@app.get("/admin/recargas")
@acesso_requerido("admin")
def admin_recargas():
    limpar_historico_expirado()
    recargas = get_db().execute(
        """
        SELECT
            recargas.*,
            cartoes.codigo_publico,
            usuarios.nome AS nome_passageiro
        FROM recargas
        JOIN cartoes ON cartoes.id = recargas.cartao_id
        JOIN usuarios ON usuarios.id = recargas.usuario_id
        ORDER BY recargas.id DESC
        LIMIT 200
        """
    ).fetchall()
    return render_template(
        "admin_recargas.html",
        recargas=recargas,
        retencao_dias=dias_retencao_recargas(),
    )


@app.get("/admin/cartoes")
@acesso_requerido("admin")
def admin_cartoes():
    cartoes = get_db().execute(
        """
        SELECT
            cartoes.*,
            usuarios.nome AS nome_usuario,
            usuarios.token_usuario,
            usuarios.ativo AS usuario_ativo
        FROM cartoes
        JOIN usuarios ON usuarios.id = cartoes.usuario_id
        ORDER BY cartoes.id DESC
        """
    ).fetchall()
    links_usuario = {
        cartao["id"]: url_for(
            "usuario_meu_cartao", token=cartao["token_usuario"], _external=True
        )
        for cartao in cartoes
    }
    return render_template("admin_cartoes.html", cartoes=cartoes, links_usuario=links_usuario)


@app.post("/admin/cartoes/<int:cartao_id>/status")
@acesso_requerido("admin")
def admin_alterar_status_cartao(cartao_id):
    status = request.form.get("status", "")
    if status not in {"ativo", "bloqueado"}:
        flash("Status invalido.")
    else:
        get_db().execute("UPDATE cartoes SET status = ? WHERE id = ?", (status, cartao_id))
        flash("Status do cartao atualizado.")
    return redirect(url_for("admin_cartoes", token=request.values.get("token", "")))


@app.route("/admin/estacoes", methods=["GET", "POST"])
@acesso_requerido("admin")
def admin_estacoes():
    erro = None
    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        regiao = request.form.get("regiao", "").strip()
        if not nome:
            erro = "Informe o nome da estacao."
        else:
            try:
                get_db().execute(
                    "INSERT INTO estacoes (nome, regiao, ativa) VALUES (?, ?, 1)",
                    (nome, regiao),
                )
                flash("Estacao cadastrada.")
                return redirect(url_for("admin_estacoes", token=request.values.get("token", "")))
            except Exception:
                erro = "Ja existe uma estacao com esse nome."
    estacoes = get_db().execute("SELECT * FROM estacoes ORDER BY ativa DESC, nome").fetchall()
    return render_template("admin_estacoes.html", estacoes=estacoes, erro=erro)


@app.post("/admin/estacoes/<int:estacao_id>/alternar")
@acesso_requerido("admin")
def admin_alternar_estacao(estacao_id):
    estacao = get_db().execute("SELECT id, ativa FROM estacoes WHERE id = ?", (estacao_id,)).fetchone()
    if not estacao:
        flash("Estacao nao encontrada.")
    else:
        get_db().execute(
            "UPDATE estacoes SET ativa = ? WHERE id = ?",
            (0 if estacao["ativa"] else 1, estacao_id),
        )
        flash("Status da estacao atualizado.")
    return redirect(url_for("admin_estacoes", token=request.values.get("token", "")))


@app.route("/admin/configuracoes", methods=["GET", "POST"])
@acesso_requerido("admin")
def admin_configuracoes():
    erro = None
    if request.method == "POST":
        retencao = request.form.get("historico_retencao_horas", "").strip()
        retencao_recargas = request.form.get("historico_recargas_retencao_dias", "").strip()
        passagem = parse_valor(request.form.get("valor_passagem_padrao", ""))
        minimo_recarga = parse_valor(request.form.get("valor_minimo_recarga", ""))
        maximo_recarga = parse_valor(request.form.get("valor_maximo_recarga", ""))
        if parse_int_positivo(retencao, 0) <= 0:
            erro = "Informe uma retencao em horas maior que zero."
        elif parse_int_positivo(retencao_recargas, 0) <= 0:
            erro = "Informe uma retencao de recargas em dias maior que zero."
        elif passagem is None:
            erro = "Informe um valor de passagem valido."
        elif minimo_recarga is None or minimo_recarga <= 0:
            erro = "Informe um valor minimo de recarga valido."
        elif maximo_recarga is None or maximo_recarga <= 0:
            erro = "Informe um valor maximo de recarga valido."
        elif minimo_recarga > maximo_recarga:
            erro = "O valor minimo de recarga nao pode ser maior que o maximo."
        else:
            set_config("historico_retencao_horas", parse_int_positivo(retencao, 24))
            set_config(
                "historico_recargas_retencao_dias",
                parse_int_positivo(retencao_recargas, 30),
            )
            set_config("valor_passagem_padrao", str(passagem))
            set_config("valor_minimo_recarga", str(minimo_recarga))
            set_config("valor_maximo_recarga", str(maximo_recarga))
            set_config(
                "permitir_download_pdf",
                "true" if request.form.get("permitir_download_pdf") == "on" else "false",
            )
            set_config(
                "exibir_saldo_no_pdf",
                "true" if request.form.get("exibir_saldo_no_pdf") == "on" else "false",
            )
            limpar_historico_expirado()
            flash("Configuracoes atualizadas.")
            return redirect(url_for("admin_configuracoes", token=request.values.get("token", "")))

    return render_template(
        "admin_configuracoes.html",
        erro=erro,
        retencao_horas=horas_retencao_historico(),
        retencao_recargas_dias=dias_retencao_recargas(),
        valor_passagem=valor_passagem_atual(),
        minimo_recarga=valor_minimo_recarga(),
        maximo_recarga=valor_maximo_recarga(),
        permitir_pdf=config_bool("permitir_download_pdf", CONFIG_PADRAO["permitir_download_pdf"]),
        exibir_saldo_pdf=config_bool("exibir_saldo_no_pdf", CONFIG_PADRAO["exibir_saldo_no_pdf"]),
    )
