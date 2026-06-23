from flask import g

from .database import get_db
from .helpers import agora_formatado
from .config import expira_em_formatado, recarga_expira_em_formatado, valor_passagem_atual


def estacoes_ativas():
    return get_db().execute(
        "SELECT id, nome, regiao FROM estacoes WHERE ativa = 1 ORDER BY nome"
    ).fetchall()


def estacao_padrao_id():
    row = get_db().execute(
        """
        SELECT id FROM estacoes
        WHERE ativa = 1
        ORDER BY CASE WHEN nome = 'Terminal Central' THEN 0 ELSE 1 END, nome
        LIMIT 1
        """
    ).fetchone()
    return row["id"] if row else None


def estacao_catraca_atual(acesso=None):
    acesso = acesso if acesso is not None else getattr(g, "acesso", None)
    estacao_id = acesso.get("estacao_id") if acesso else None
    if not estacao_id:
        estacao_id = estacao_padrao_id()
    return get_db().execute(
        "SELECT id, nome, regiao FROM estacoes WHERE id = ?",
        (estacao_id,),
    ).fetchone()


def cartao_do_usuario(usuario_id):
    return get_db().execute(
        """
        SELECT
            cartoes.*,
            usuarios.nome AS nome_usuario,
            usuarios.token_usuario
        FROM cartoes
        JOIN usuarios ON usuarios.id = cartoes.usuario_id
        WHERE cartoes.usuario_id = ?
        ORDER BY cartoes.id
        LIMIT 1
        """,
        (usuario_id,),
    ).fetchone()


def rota_planejada_ativa(usuario_id, cartao_id):
    return get_db().execute(
        """
        SELECT * FROM rotas_viagem
        WHERE usuario_id = ? AND cartao_id = ? AND status = 'planejada'
        ORDER BY id DESC
        LIMIT 1
        """,
        (usuario_id, cartao_id),
    ).fetchone()


def trechos_da_rota(rota_id):
    return get_db().execute(
        """
        SELECT
            trechos_viagem.*,
            origem.nome AS origem_nome,
            destino.nome AS destino_nome
        FROM trechos_viagem
        JOIN estacoes origem ON origem.id = trechos_viagem.origem_id
        JOIN estacoes destino ON destino.id = trechos_viagem.destino_id
        WHERE rota_id = ?
        ORDER BY ordem
        """,
        (rota_id,),
    ).fetchall()


def trechos_preview(trechos):
    if not trechos:
        return []

    ids = sorted({estacao_id for trecho in trechos for estacao_id in trecho})
    placeholders = ",".join("?" for _ in ids)
    linhas = get_db().execute(
        f"SELECT id, nome FROM estacoes WHERE id IN ({placeholders})", ids
    ).fetchall()
    nomes = {linha["id"]: linha["nome"] for linha in linhas}
    return [
        {
            "ordem": indice,
            "origem_id": origem_id,
            "destino_id": destino_id,
            "origem_nome": nomes.get(origem_id, "-"),
            "destino_nome": nomes.get(destino_id, "-"),
        }
        for indice, (origem_id, destino_id) in enumerate(trechos, start=1)
    ]


def trecho_compativel_com_estacao(cartao, estacao_id):
    rota = rota_planejada_ativa(cartao["usuario_id"], cartao["id"])
    if not rota or not estacao_id:
        return None, None

    trecho = get_db().execute(
        """
        SELECT * FROM trechos_viagem
        WHERE rota_id = ? AND origem_id = ?
        ORDER BY ordem
        LIMIT 1
        """,
        (rota["id"], estacao_id),
    ).fetchone()
    return rota, trecho


def cartao_usuario_atual_ou_erro(usuario_id):
    if not usuario_id:
        return None, "Este acesso de usuario ainda nao foi vinculado a um passageiro."
    cartao = cartao_do_usuario(usuario_id)
    if not cartao:
        return None, "Nenhum cartao foi encontrado para este usuario."
    return cartao, None


def gerar_id_cartao(db):
    row = db.execute(
        """
        SELECT
            CASE
                WHEN MAX(id) IS NULL OR MAX(id) < 1000 THEN 1001
                ELSE MAX(id) + 1
            END AS proximo_id
        FROM cartoes
        """
    ).fetchone()
    return int(row["proximo_id"])


def registrar_passagem(
    db,
    cartao_id,
    cartao_digitado,
    status,
    motivo,
    valor_cobrado,
    origem_id=None,
    destino_id=None,
):
    db.execute(
        """
        INSERT INTO passagens (
            cartao_id, cartao_digitado, origem_id, destino_id, data_hora,
            status, motivo, valor_cobrado, expira_em
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            cartao_id,
            cartao_digitado,
            origem_id,
            destino_id,
            agora_formatado(),
            status,
            motivo,
            float(valor_cobrado),
            expira_em_formatado(),
        ),
    )


def registrar_recarga(db, usuario_id, cartao_id, valor, saldo_anterior, saldo_novo):
    db.execute(
        """
        INSERT INTO recargas (
            usuario_id, cartao_id, valor, saldo_anterior, saldo_novo,
            data_hora, status, expira_em
        )
        VALUES (?, ?, ?, ?, ?, ?, 'confirmada', ?)
        """,
        (
            usuario_id,
            cartao_id,
            float(valor),
            float(saldo_anterior),
            float(saldo_novo),
            agora_formatado(),
            recarga_expira_em_formatado(),
        ),
    )
