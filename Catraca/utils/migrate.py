import sqlite3
from datetime import timedelta

from .database import get_db
from .helpers import agora_formatado, gerar_token_usuario
from .config import CONFIG_PADRAO, DISPOSITIVOS_PADRAO, ESTACOES_PADRAO, DATABASE


def colunas_tabela(db, tabela):
    return {coluna[1] for coluna in db.execute(f"PRAGMA table_info({tabela})").fetchall()}


def garantir_coluna(db, tabela, coluna, definicao):
    if coluna not in colunas_tabela(db, tabela):
        db.execute(f"ALTER TABLE {tabela} ADD COLUMN {definicao}")


def migrar_cartoes_antigos(db):
    cartoes = db.execute(
        """
        SELECT id, usuario_id, codigo_publico, nome_passageiro, data_criacao, criado_em
        FROM cartoes
        ORDER BY id
        """
    ).fetchall()
    for cartao in cartoes:
        criado_em = cartao["criado_em"] or cartao["data_criacao"] or agora_formatado()
        usuario_id = cartao["usuario_id"]
        if not usuario_id:
            token = gerar_token_usuario(db)
            cursor = db.execute(
                """
                INSERT INTO usuarios (nome, token_usuario, criado_em, ativo)
                VALUES (?, ?, ?, 1)
                """,
                (cartao["nome_passageiro"], token, criado_em),
            )
            usuario_id = cursor.lastrowid

        codigo_publico = cartao["codigo_publico"] or str(cartao["id"])
        db.execute(
            """
            UPDATE cartoes
            SET usuario_id = ?, codigo_publico = ?, criado_em = COALESCE(criado_em, data_criacao)
            WHERE id = ?
            """,
            (usuario_id, codigo_publico, cartao["id"]),
        )


def migrar_dispositivos_antigos(db):
    dispositivos = db.execute(
        "SELECT id, tipo, cartao_id, usuario_id FROM dispositivos"
    ).fetchall()
    for dispositivo in dispositivos:
        if dispositivo["usuario_id"] or not dispositivo["cartao_id"]:
            continue
        cartao = db.execute(
            "SELECT usuario_id FROM cartoes WHERE id = ?",
            (dispositivo["cartao_id"],),
        ).fetchone()
        if cartao:
            db.execute(
                "UPDATE dispositivos SET usuario_id = ? WHERE id = ?",
                (cartao["usuario_id"], dispositivo["id"]),
            )


def limpar_historico_expirado(db=None):
    from .config import dias_retencao_recargas, horas_retencao_historico
    from .helpers import agora_dt, formatar_data

    banco = db or get_db()
    agora = formatar_data(agora_dt())
    corte = formatar_data(agora_dt() - timedelta(hours=horas_retencao_historico(db=banco)))
    banco.execute(
        """
        DELETE FROM passagens
        WHERE (expira_em IS NOT NULL AND expira_em < ?)
           OR (expira_em IS NULL AND data_hora < ?)
        """,
        (agora, corte),
    )
    corte_recargas = formatar_data(
        agora_dt() - timedelta(days=dias_retencao_recargas(db=banco))
    )
    banco.execute(
        """
        DELETE FROM recargas
        WHERE (expira_em IS NOT NULL AND expira_em < ?)
           OR (expira_em IS NULL AND data_hora < ?)
        """,
        (agora, corte_recargas),
    )


def init_db():
    with sqlite3.connect(DATABASE) as db:
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=OFF")
        db.execute("PRAGMA journal_mode=WAL")
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                token_usuario TEXT NOT NULL UNIQUE,
                criado_em TEXT NOT NULL,
                ativo INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1))
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS cartoes (
                id INTEGER PRIMARY KEY,
                usuario_id INTEGER,
                codigo_publico TEXT,
                nome_passageiro TEXT NOT NULL,
                cpf TEXT,
                numero_celular TEXT,
                saldo REAL NOT NULL DEFAULT 0 CHECK (saldo >= 0),
                status TEXT NOT NULL DEFAULT 'ativo'
                    CHECK (status IN ('ativo', 'bloqueado')),
                data_criacao TEXT NOT NULL,
                criado_em TEXT,
                atualizado_em TEXT
            )
            """
        )
        garantir_coluna(db, "cartoes", "usuario_id", "usuario_id INTEGER")
        garantir_coluna(db, "cartoes", "codigo_publico", "codigo_publico TEXT")
        garantir_coluna(db, "cartoes", "cpf", "cpf TEXT")
        garantir_coluna(db, "cartoes", "numero_celular", "numero_celular TEXT")
        garantir_coluna(db, "cartoes", "criado_em", "criado_em TEXT")
        garantir_coluna(db, "cartoes", "atualizado_em", "atualizado_em TEXT")
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS estacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                regiao TEXT,
                ativa INTEGER NOT NULL DEFAULT 1 CHECK (ativa IN (0, 1))
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS passagens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cartao_id INTEGER,
                cartao_digitado TEXT,
                origem_id INTEGER,
                destino_id INTEGER,
                data_hora TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('aprovado', 'negado')),
                motivo TEXT NOT NULL,
                valor_cobrado REAL NOT NULL DEFAULT 0,
                expira_em TEXT
            )
            """
        )
        garantir_coluna(db, "passagens", "origem_id", "origem_id INTEGER")
        garantir_coluna(db, "passagens", "destino_id", "destino_id INTEGER")
        garantir_coluna(db, "passagens", "expira_em", "expira_em TEXT")
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS configuracoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chave TEXT NOT NULL UNIQUE,
                valor TEXT NOT NULL
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS recargas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                cartao_id INTEGER NOT NULL,
                valor REAL NOT NULL,
                saldo_anterior REAL NOT NULL,
                saldo_novo REAL NOT NULL,
                data_hora TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'confirmada',
                expira_em TEXT,
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
                FOREIGN KEY (cartao_id) REFERENCES cartoes(id)
            )
            """
        )
        garantir_coluna(db, "recargas", "expira_em", "expira_em TEXT")
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS rotas_viagem (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                cartao_id INTEGER NOT NULL,
                criado_em TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'planejada'
                    CHECK (status IN ('planejada', 'cancelada', 'concluida')),
                FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
                FOREIGN KEY (cartao_id) REFERENCES cartoes(id)
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS trechos_viagem (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rota_id INTEGER NOT NULL,
                origem_id INTEGER NOT NULL,
                destino_id INTEGER NOT NULL,
                ordem INTEGER NOT NULL,
                valor REAL NOT NULL DEFAULT 0,
                FOREIGN KEY (rota_id) REFERENCES rotas_viagem(id) ON DELETE CASCADE,
                FOREIGN KEY (origem_id) REFERENCES estacoes(id),
                FOREIGN KEY (destino_id) REFERENCES estacoes(id)
            )
            """
        )
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS dispositivos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_dispositivo TEXT NOT NULL,
                tipo TEXT NOT NULL CHECK (tipo IN ('catraca', 'usuario', 'admin')),
                token_acesso TEXT NOT NULL UNIQUE,
                ativo INTEGER NOT NULL DEFAULT 1 CHECK (ativo IN (0, 1)),
                cartao_id INTEGER,
                usuario_id INTEGER,
                estacao_id INTEGER
            )
            """
        )
        garantir_coluna(db, "dispositivos", "cartao_id", "cartao_id INTEGER")
        garantir_coluna(db, "dispositivos", "usuario_id", "usuario_id INTEGER")
        garantir_coluna(db, "dispositivos", "estacao_id", "estacao_id INTEGER")

        for chave, valor in CONFIG_PADRAO.items():
            db.execute(
                "INSERT OR IGNORE INTO configuracoes (chave, valor) VALUES (?, ?)",
                (chave, valor),
            )
        db.execute("DELETE FROM configuracoes WHERE chave = 'exibir_saldo_no_pdf'")

        for nome, regiao in ESTACOES_PADRAO:
            db.execute(
                "INSERT OR IGNORE INTO estacoes (nome, regiao, ativa) VALUES (?, ?, 1)",
                (nome, regiao),
            )

        migrar_cartoes_antigos(db)
        migrar_dispositivos_antigos(db)

        terminal = db.execute(
            "SELECT id FROM estacoes WHERE nome = 'Terminal Central'"
        ).fetchone()
        estacao_padrao_id = terminal["id"] if terminal else None
        for nome, tipo, token in DISPOSITIVOS_PADRAO:
            db.execute(
                """
                INSERT OR IGNORE INTO dispositivos (
                    nome_dispositivo, tipo, token_acesso, ativo, estacao_id
                )
                VALUES (?, ?, ?, 1, ?)
                """,
                (nome, tipo, token, estacao_padrao_id if tipo == "catraca" else None),
            )

        db.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_cartoes_codigo_publico ON cartoes(codigo_publico)"
        )
        db.execute(
            "CREATE INDEX IF NOT EXISTS idx_passagens_expira_em ON passagens(expira_em)"
        )
        db.execute(
            "CREATE INDEX IF NOT EXISTS idx_recargas_expira_em ON recargas(expira_em)"
        )
        limpar_historico_expirado(db)
