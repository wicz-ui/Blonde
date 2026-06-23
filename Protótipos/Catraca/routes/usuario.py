from flask import flash, redirect, render_template, request, url_for

from app import app
from utils.auth import acesso_requerido
from utils.config import (
    CONFIG_PADRAO,
    config_bool,
    dias_retencao_recargas,
    valor_minimo_recarga,
    valor_maximo_recarga,
    valor_passagem_atual,
)
from utils.helpers import (
    codificar_trechos,
    decodificar_trechos,
    formatar_moeda,
    parse_valor,
    valores_recarga_padrao,
)
from utils.migrate import limpar_historico_expirado
from utils.queries import (
    cartao_do_usuario,
    cartao_usuario_atual_ou_erro,
    rota_planejada_ativa,
    trechos_da_rota,
    trechos_preview,
)


@app.get("/usuario/meu-cartao")
@acesso_requerido("usuario")
def usuario_meu_cartao():
    cartao = None
    erro = None
    if not hasattr(__import__("flask").flask.g, "acesso") or not __import__("flask").flask.g.acesso.get("usuario_id"):
        erro = "Este acesso de usuario ainda nao foi vinculado a um passageiro."
    else:
        cartao = cartao_do_usuario(__import__("flask").flask.g.acesso["usuario_id"])
        if not cartao:
            erro = "Nenhum cartao foi encontrado para este usuario."

    return render_template(
        "meu_cartao.html",
        cartao=cartao,
        erro=erro,
        valor_passagem=valor_passagem_atual(),
        permitir_pdf=config_bool("permitir_download_pdf", CONFIG_PADRAO["permitir_download_pdf"]),
        link_rapido=(
            url_for("acesso_rapido_usuario", token_usuario=cartao["token_usuario"], _external=True)
            if cartao
            else None
        ),
    )


@app.route("/usuario/recarregar-cartao", methods=["GET", "POST"])
@app.post("/usuario/recarregar-cartao/confirmar")
@acesso_requerido("usuario")
def usuario_recarregar_cartao():
    cartao, erro = cartao_usuario_atual_ou_erro(__import__("flask").flask.g.acesso.get("usuario_id"))
    sucesso = None
    valor_escolhido = ""
    minimo = valor_minimo_recarga()
    maximo = valor_maximo_recarga()

    if request.method == "POST" and cartao:
        valor_escolhido = request.form.get("valor_recarga", "")
        valor_texto = (
            request.form.get("outro_valor", "")
            if valor_escolhido == "outro"
            else valor_escolhido
        )
        valor = parse_valor(valor_texto)

        if valor is None or valor <= 0:
            erro = "Informe um valor de recarga valido."
        elif valor < minimo:
            erro = f"O valor minimo de recarga e {formatar_moeda(minimo)}."
        elif valor > maximo:
            erro = f"O valor maximo de recarga e {formatar_moeda(maximo)}."
        else:
            from utils.database import get_db
            from utils.queries import registrar_recarga
            db = get_db()
            db.execute("BEGIN IMMEDIATE")
            try:
                cartao_atual = db.execute(
                    "SELECT saldo FROM cartoes WHERE id = ? AND usuario_id = ?",
                    (cartao["id"], cartao["usuario_id"]),
                ).fetchone()
                if not cartao_atual:
                    erro = "Cartao nao encontrado para este usuario."
                    db.execute("ROLLBACK")
                else:
                    saldo_anterior = __import__("decimal").Decimal(str(cartao_atual["saldo"])).quantize(__import__("decimal").Decimal("0.01"))
                    saldo_novo = saldo_anterior + valor
                    db.execute(
                        """
                        UPDATE cartoes
                        SET saldo = ?, atualizado_em = ?
                        WHERE id = ? AND usuario_id = ?
                        """,
                        (
                            float(saldo_novo),
                            __import__("utils.helpers").helpers.agora_formatado(),
                            cartao["id"],
                            cartao["usuario_id"],
                        ),
                    )
                    registrar_recarga(
                        db,
                        cartao["usuario_id"],
                        cartao["id"],
                        valor,
                        saldo_anterior,
                        saldo_novo,
                    )
                    limpar_historico_expirado(db)
                    db.execute("COMMIT")
                    cartao = cartao_do_usuario(__import__("flask").flask.g.acesso["usuario_id"])
                    sucesso = {
                        "valor": valor,
                        "saldo_anterior": saldo_anterior,
                        "saldo_novo": saldo_novo,
                    }
            except Exception:
                db.execute("ROLLBACK")
                erro = "Nao foi possivel confirmar a recarga."

    return render_template(
        "recarregar_cartao.html",
        cartao=cartao,
        erro=erro,
        sucesso=sucesso,
        valores_recarga=valores_recarga_padrao(),
        valor_escolhido=valor_escolhido,
        minimo=minimo,
        maximo=maximo,
    )


@app.get("/usuario/recargas")
@acesso_requerido("usuario")
def usuario_recargas():
    limpar_historico_expirado()
    cartao, erro = cartao_usuario_atual_ou_erro(__import__("flask").flask.g.acesso.get("usuario_id"))
    recargas = []
    if cartao:
        recargas = __import__("utils.database").database.get_db().execute(
            """
            SELECT * FROM recargas
            WHERE usuario_id = ? AND cartao_id = ?
            ORDER BY id DESC
            LIMIT 100
            """,
            (cartao["usuario_id"], cartao["id"]),
        ).fetchall()
    return render_template(
        "usuario_recargas.html",
        cartao=cartao,
        erro=erro,
        recargas=recargas,
        retencao_dias=dias_retencao_recargas(),
    )


@app.get("/usuario/cartao/pdf")
@acesso_requerido("usuario")
def usuario_cartao_pdf():
    if not config_bool("permitir_download_pdf", CONFIG_PADRAO["permitir_download_pdf"]):
        return (
            render_template(
                "acesso_negado.html",
                titulo="Download indisponivel",
                mensagem="O download do cartao em PDF esta desativado pelo administrador.",
            ),
            403,
        )

    cartao, erro = cartao_usuario_atual_ou_erro(__import__("flask").flask.g.acesso.get("usuario_id"))
    if not cartao:
        return (
            render_template(
                "acesso_negado.html",
                titulo="Cartao nao encontrado",
                mensagem=erro,
            ),
            404,
        )

    from utils.pdf import gerar_pdf_cartao

    pdf = gerar_pdf_cartao(
        cartao,
        exibir_saldo=config_bool("exibir_saldo_no_pdf", CONFIG_PADRAO["exibir_saldo_no_pdf"]),
    )
    nome_arquivo = f"cartao-{cartao['codigo_publico']}.pdf"
    from flask import Response

    return Response(
        pdf,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={nome_arquivo}"},
    )


@app.route("/usuario/planejar-viagem", methods=["GET", "POST"])
@acesso_requerido("usuario")
def usuario_planejar_viagem():
    cartao = cartao_do_usuario(__import__("flask").flask.g.acesso.get("usuario_id")) if __import__("flask").flask.g.acesso.get("usuario_id") else None
    if not cartao:
        return render_template(
            "planejar_viagem.html",
            erro="Vincule este acesso a um cartao antes de planejar viagens.",
            cartao=None,
            estacoes=[],
            trechos=[],
            trechos_serializados="",
            valor_passagem=valor_passagem_atual(),
        )

    erro = None
    trechos = decodificar_trechos(request.form.get("trechos", ""))
    if request.method == "GET" and request.args.get("editar") == "atual":
        rota_atual = rota_planejada_ativa(cartao["usuario_id"], cartao["id"])
        if rota_atual:
            trechos = [
                (trecho["origem_id"], trecho["destino_id"])
                for trecho in trechos_da_rota(rota_atual["id"])
            ]
    if request.method == "POST":
        acao = request.form.get("acao")
        indice_da_acao = ""
        if acao and ":" in acao:
            acao, indice_da_acao = acao.split(":", 1)
        origem_id = request.form.get("origem_id", "")
        destino_id = request.form.get("destino_id", "")
        indice_texto = indice_da_acao or request.form.get("indice", "")

        if acao == "adicionar":
            if not origem_id.isdigit() or not destino_id.isdigit():
                erro = "Selecione origem e destino."
            elif origem_id == destino_id:
                erro = "Origem e destino devem ser diferentes."
            else:
                trechos.append((int(origem_id), int(destino_id)))
        elif acao == "remover":
            if indice_texto.isdigit() and int(indice_texto) < len(trechos):
                trechos.pop(int(indice_texto))
        elif acao == "subir":
            if indice_texto.isdigit():
                indice = int(indice_texto)
                if 0 < indice < len(trechos):
                    trechos[indice - 1], trechos[indice] = trechos[indice], trechos[indice - 1]
        elif acao == "descer":
            if indice_texto.isdigit():
                indice = int(indice_texto)
                if 0 <= indice < len(trechos) - 1:
                    trechos[indice + 1], trechos[indice] = trechos[indice], trechos[indice + 1]
        elif acao == "limpar":
            trechos = []
        elif acao == "confirmar":
            if not trechos:
                erro = "Adicione pelo menos um trecho antes de confirmar."
            else:
                from utils.database import get_db
                db = get_db()
                db.execute("BEGIN IMMEDIATE")
                try:
                    db.execute(
                        """
                        UPDATE rotas_viagem
                        SET status = 'cancelada'
                        WHERE usuario_id = ? AND cartao_id = ? AND status = 'planejada'
                        """,
                        (cartao["usuario_id"], cartao["id"]),
                    )
                    rota_cursor = db.execute(
                        """
                        INSERT INTO rotas_viagem (usuario_id, cartao_id, criado_em, status)
                        VALUES (?, ?, ?, 'planejada')
                        """,
                        (cartao["usuario_id"], cartao["id"], __import__("utils.helpers").helpers.agora_formatado()),
                    )
                    rota_id = rota_cursor.lastrowid
                    valor = float(valor_passagem_atual())
                    for indice, (origem, destino) in enumerate(trechos, start=1):
                        db.execute(
                            """
                            INSERT INTO trechos_viagem (
                                rota_id, origem_id, destino_id, ordem, valor
                            )
                            VALUES (?, ?, ?, ?, ?)
                            """,
                            (rota_id, origem, destino, indice, valor),
                        )
                    db.execute("COMMIT")
                    flash("Viagem planejada com sucesso.")
                    return redirect(url_for("usuario_minha_viagem", token=request.values.get("token", "")))
                except Exception:
                    db.execute("ROLLBACK")
                    erro = "Nao foi possivel salvar a viagem."

    return render_template(
        "planejar_viagem.html",
        cartao=cartao,
        erro=erro,
        estacoes=__import__("utils.queries").queries.estacoes_ativas(),
        trechos=__import__("utils.helpers").helpers.trechos_preview(trechos),
        trechos_serializados=codificar_trechos(trechos),
        valor_passagem=valor_passagem_atual(),
    )


@app.get("/usuario/minha-viagem")
@acesso_requerido("usuario")
def usuario_minha_viagem():
    cartao = cartao_do_usuario(__import__("flask").flask.g.acesso.get("usuario_id")) if __import__("flask").flask.g.acesso.get("usuario_id") else None
    rota = None
    trechos = []
    if cartao:
        rota = rota_planejada_ativa(cartao["usuario_id"], cartao["id"])
        if rota:
            trechos = trechos_da_rota(rota["id"])
    return render_template("minha_viagem.html", cartao=cartao, rota=rota, trechos=trechos)


@app.post("/usuario/minha-viagem/cancelar")
@acesso_requerido("usuario")
def usuario_cancelar_viagem():
    cartao = cartao_do_usuario(__import__("flask").flask.g.acesso.get("usuario_id")) if __import__("flask").flask.g.acesso.get("usuario_id") else None
    if not cartao:
        flash("Nenhum cartao encontrado para este usuario.")
    else:
        __import__("utils.database").database.get_db().execute(
            """
            UPDATE rotas_viagem
            SET status = 'cancelada'
            WHERE usuario_id = ? AND cartao_id = ? AND status = 'planejada'
            """,
            (cartao["usuario_id"], cartao["id"]),
        )
        flash("Rota cancelada.")
    return redirect(url_for("usuario_minha_viagem", token=request.values.get("token", "")))
