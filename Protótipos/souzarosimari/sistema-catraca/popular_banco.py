"""
popular_banco.py
=================
Script utilitário que recria o banco de dados do zero e o popula com 5
cartões de teste prontos para a demonstração (saldo cheio, saldo baixo e
cartão bloqueado), permitindo validar todas as regras de negócio do
sistema sem precisar cadastrar nada manualmente.

Uso:
    python popular_banco.py

Atenção: este script APAGA o arquivo database.db existente antes de
recriá-lo. Pare o servidor Flask (Ctrl+C) antes de executá-lo.
"""

import os
import sqlite3
from datetime import datetime

DB_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database.db")

CARTOES_TESTE = [
    ("Carlos Alberto", 50.00, "ativo"),     # Aprova normalmente
    ("Mariana Souza", 15.00, "ativo"),      # Aprova normalmente
    ("Pedro Henrique", 2.50, "ativo"),      # Nega por saldo insuficiente
    ("Ana Beatriz", 20.00, "bloqueado"),    # Nega por bloqueio (mesmo com saldo)
    ("Lucas Oliveira", 100.00, "ativo"),    # Aprova normalmente
]


def popular():
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print("Banco de dados antigo removido.")

    conn = sqlite3.connect(DB_FILE)
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

    # Faz os cartões de teste começarem no ID 1001
    cursor.execute("INSERT INTO sqlite_sequence (name, seq) VALUES ('cartoes', 1000)")

    data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for nome, saldo, status in CARTOES_TESTE:
        cursor.execute(
            "INSERT INTO cartoes (nome_passageiro, saldo, status, data_criacao) "
            "VALUES (?, ?, ?, ?)",
            (nome, saldo, status, data_atual),
        )

    conn.commit()
    conn.close()

    print("\nBanco de dados populado com sucesso para a apresentação!")
    print("\nIDs prontos para testar na catraca:")
    print("-" * 56)
    print("1001 -> Carlos Alberto  | Saldo R$ 50,00 | ATIVO      (aprova)")
    print("1002 -> Mariana Souza   | Saldo R$ 15,00 | ATIVO      (aprova)")
    print("1003 -> Pedro Henrique  | Saldo R$  2,50 | ATIVO      (nega: saldo)")
    print("1004 -> Ana Beatriz     | Saldo R$ 20,00 | BLOQUEADO  (nega: bloqueio)")
    print("1005 -> Lucas Oliveira  | Saldo R$100,00 | ATIVO      (aprova)")
    print("9999 -> (não existe)    |        —       |     —      (nega: inexistente)")
    print("-" * 56)


if __name__ == "__main__":
    popular()
