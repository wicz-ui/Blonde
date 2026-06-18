"""
Sistema de Catraca Virtual para Ônibus
=======================================Como funciona a demonstração
01
O passageiro cria um cartão e recebe um ID.
02
O operador abre a tela da catraca em outro celular.
03
O ID é digitado e validado contra o banco SQLite.
04
A entrada é aprovada ou negada e fica registrada no histórico.
Projeto acadêmico que simula o funcionamento de uma catraca de transporte
público usando cartões virtuais, sem necessidade de hardware físico.

Stack:
    - Back-end:   Python 3 + Flask
    - Banco:      SQLite (arquivo local database.db)
    - Front-end:  HTML + CSS + JavaScript (templates Jinja2)

Fluxo geral (ver README.md para detalhes):
    1. Passageiro cria um cartão virtual em /criar.
    2. Passageiro consulta seu cartão em /buscar.
    3. Operador valida a entrada em /catraca, digitando o ID do cartão.
    4. Toda tentativa (aprovada ou negada) é registrada e pode ser
       consultada em /historico.
"""

import os
import sqlite3
from datetime import datetime

from flask import Flask, flash, redirect, render_template, request, url_for

# ---------------------------------------------------------------------------
# Configuração geral da aplicação
# ---------------------------------------------------------------------------

app = Flask(__name__)
app.secret_key = "chave-secreta-projeto-academico-catraca"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "database.db")

VALOR_TARIFARIO = 5.00  # Valor fixo da passagem, em reais (PRD seção 11)


# ---------------------------------------------------------------------------
# Banco de dados
# ---------------------------------------------------------------------------

def get_db_connection():
    """Abre uma conexão com o SQLite retornando linhas no formato dict-like."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Cria as tabelas 'cartoes' e 'passagens' caso ainda não existam."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS cartoes (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_passageiro TEXT NOT NULL,
            saldo           REAL NOT NULL DEFAULT 0,
            status          TEXT NOT NULL DEFAULT 'ativo',
            data_criacao    TEXT NOT NULL
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS passagens (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            cartao_id     INTEGER,
            data_hora     TEXT NOT NULL,
            status        TEXT NOT NULL,
            motivo        TEXT NOT NULL,
            valor_cobrado REAL NOT NULL DEFAULT 0
        )
        """
    )

    # Faz os IDs dos cartões começarem em 1001 (estética acadêmica) -
    # só roda na primeiríssima execução, antes de qualquer cartão existir.
    cursor.execute("SELECT COUNT(*) FROM sqlite_sequence WHERE name = 'cartoes'")
    se_ainda_nao_configurado = cursor.fetchone()[0] == 0
    cursor.execute("SELECT COUNT(*) FROM cartoes")
    nenhum_cartao_criado = cursor.fetchone()[0] == 0

    if se_ainda_nao_configurado and nenhum_cartao_criado:
        cursor.execute(
            "INSERT INTO sqlite_sequence (name, seq) VALUES ('cartoes', 1000)"
        )

    conn.commit()
    conn.close()


@app.context_processor
def injetar_variaveis_globais():
    """Disponibiliza variáveis comuns em todos os templates automaticamente."""
    return {"valor_tarifario": VALOR_TARIFARIO}


# ---------------------------------------------------------------------------
# Rotas
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/criar", methods=["GET", "POST"])
def criar_cartao():
    if request.method == "POST":
        nome = request.form.get("nome_passageiro", "").strip()
        try:
            saldo_inicial = float(request.form.get("saldo", 0))
        except ValueError:
            saldo_inicial = 0.0

        if not nome:
            flash("Informe o nome do passageiro.", "danger")
            return render_template("criar_cartao.html")

        if saldo_inicial < 0:
            flash("O saldo inicial não pode ser negativo.", "danger")
            return render_template("criar_cartao.html")

        data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO cartoes (nome_passageiro, saldo, status, data_criacao) "
            "VALUES (?, ?, 'ativo', ?)",
            (nome, saldo_inicial, data_atual),
        )
        cartao_id = cursor.lastrowid
        conn.commit()
        conn.close()

        flash(f"Cartão criado com sucesso! Guarde o ID: {cartao_id}", "success")
        return redirect(url_for("buscar_cartao", cartao_id=cartao_id))

    return render_template("criar_cartao.html")


@app.route("/buscar", methods=["GET"])
def buscar_cartao():
    cartao_id = request.args.get("cartao_id", "").strip()
    cartao = None

    if cartao_id:
        conn = get_db_connection()
        cartao = conn.execute(
            "SELECT * FROM cartoes WHERE id = ?", (cartao_id,)
        ).fetchone()
        conn.close()
        if not cartao:
            flash("Nenhum cartão encontrado com esse ID.", "danger")

    return render_template("buscar_cartao.html", cartao=cartao)


@app.route("/catraca", methods=["GET", "POST"])
def catraca():
    if request.method == "POST":
        cartao_id = request.form.get("cartao_id", "").strip()
        data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_db_connection()
        cursor = conn.cursor()

        cartao = None
        if cartao_id.isdigit():
            cartao = cursor.execute(
                "SELECT * FROM cartoes WHERE id = ?", (cartao_id,)
            ).fetchone()

        # Regra 10.2 — cartão inexistente
        if not cartao:
            cursor.execute(
                "INSERT INTO passagens (cartao_id, data_hora, status, motivo, valor_cobrado) "
                "VALUES (?, ?, 'negado', 'Cartão inexistente', 0)",
                (cartao_id or None, data_atual),
            )
            conn.commit()
            conn.close()
            return render_template(
                "resultado.html",
                status="negado",
                motivo="Cartão não encontrado no sistema.",
                cartao_id=cartao_id,
            )

        # Regra 10.1 — cartão precisa estar ativo
        if cartao["status"] != "ativo":
            cursor.execute(
                "INSERT INTO passagens (cartao_id, data_hora, status, motivo, valor_cobrado) "
                "VALUES (?, ?, 'negado', 'Cartão bloqueado', 0)",
                (cartao_id, data_atual),
            )
            conn.commit()
            conn.close()
            return render_template(
                "resultado.html",
                status="negado",
                motivo="Cartão bloqueado. Procure a empresa de transporte.",
                cartao=cartao,
            )

        # Regra 10.3 — saldo precisa ser suficiente
        if cartao["saldo"] < VALOR_TARIFARIO:
            cursor.execute(
                "INSERT INTO passagens (cartao_id, data_hora, status, motivo, valor_cobrado) "
                "VALUES (?, ?, 'negado', 'Saldo insuficiente', 0)",
                (cartao_id, data_atual),
            )
            conn.commit()
            conn.close()
            return render_template(
                "resultado.html",
                status="negado",
                motivo="Saldo insuficiente para pagar a passagem.",
                cartao=cartao,
            )

        # Regra 10.4 — desconto do saldo e aprovação
        novo_saldo = round(cartao["saldo"] - VALOR_TARIFARIO, 2)
        cursor.execute(
            "UPDATE cartoes SET saldo = ? WHERE id = ?", (novo_saldo, cartao_id)
        )
        cursor.execute(
            "INSERT INTO passagens (cartao_id, data_hora, status, motivo, valor_cobrado) "
            "VALUES (?, ?, 'aprovado', 'Entrada liberada', ?)",
            (cartao_id, data_atual, VALOR_TARIFARIO),
        )
        conn.commit()
        conn.close()

        return render_template(
            "resultado.html",
            status="aprovado",
            motivo="Entrada liberada. Boa viagem!",
            saldo=novo_saldo,
            cartao=cartao,
        )

    return render_template("catraca.html")


@app.route("/historico")
def historico():
    conn = get_db_connection()
    historico_dados = conn.execute(
        """
        SELECT p.id, p.cartao_id, p.data_hora, p.status, p.motivo,
               p.valor_cobrado, c.nome_passageiro
        FROM passagens p
        LEFT JOIN cartoes c ON p.cartao_id = c.id
        ORDER BY p.id DESC
        LIMIT 100
        """
    ).fetchall()
    conn.close()
    return render_template("historico.html", historico=historico_dados)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
