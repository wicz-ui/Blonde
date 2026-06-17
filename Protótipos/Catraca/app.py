import os
import secrets
import sqlite3
import string
from io import BytesIO
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from functools import wraps
from pathlib import Path
from zoneinfo import ZoneInfo

from flask import Flask, Response, flash, g, redirect, render_template, request, url_for
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.pdfgen import canvas


BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "database.db"
FUSO_HORARIO = ZoneInfo("America/Sao_Paulo")
TIPOS_DISPOSITIVO = {"catraca", "usuario", "admin"}
CONFIG_PADRAO = {
    "historico_retencao_horas": "24",
    "historico_recargas_retencao_dias": "30",
    "permitir_download_pdf": "true",
    "exibir_saldo_no_pdf": "true",
    "valor_maximo_recarga": "200.00",
    "valor_minimo_recarga": "5.00",
    "valor_passagem_padrao": "5.00",
}
STATIC_VERSION = "20260610-qr-camera"
DISPOSITIVOS_PADRAO = (
    ("Computador administrativo", "admin", os.getenv("ADMIN_TOKEN", "admin-demo-2026")),
    ("Catraca virtual principal", "catraca", os.getenv("CATRACA_TOKEN", "catraca-demo-2026")),
    ("Celular do passageiro", "usuario", os.getenv("USUARIO_TOKEN", "usuario-demo-2026")),
)
ESTACOES_PADRAO = (
    ("Terminal Central", "Centro"),
    ("Centro", "Centro"),
    ("Higienopolis", "Centro"),
    ("Ipiranga", "Centro"),
    ("Petropolis", "Centro"),
    ("Quebec", "Oeste"),
    ("Shangri-la", "Oeste"),
    ("Vila Brasil", "Centro"),
    ("Vila Casoni", "Norte"),
    ("Vila Nova", "Norte"),
    ("Gleba Palhano", "Sul"),
    ("Jardim Aeroporto", "Leste"),
    ("Jardim Leonor", "Oeste"),
    ("Jardim Bandeirantes", "Oeste"),
    ("Jardim Alvorada", "Oeste"),
    ("Jardim Sabara", "Oeste"),
    ("Jardim Interlagos", "Leste"),
    ("Cinco Conjuntos", "Norte"),
    ("Jardim Coliseu", "Norte"),
    ("Jardim Pacaembu", "Norte"),
    ("Jardim Cafezal", "Sul"),
    ("Terminal Oeste", "Oeste"),
    ("Terminal Norte", "Norte"),
    ("Terminal Sul", "Sul"),
    ("Terminal Acapulco", "Sul"),
    ("Cambe", "Regiao Metropolitana"),
    ("Ibipora", "Regiao Metropolitana"),
    ("Rolandia", "Regiao Metropolitana"),
    ("Paiquere", "Distrito"),
    ("Guaravera", "Distrito"),
    ("Warta", "Distrito"),
    ("Lerroville", "Distrito"),
    ("Irere", "Distrito"),
    ("Maravilha", "Distrito"),
    ("Sao Luiz", "Distrito"),
)


app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "catraca-demo-secret")


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE, timeout=30, isolation_level=None)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def colunas_tabela(db, tabela):
    return {coluna[1] for coluna in db.execute(f"PRAGMA table_info({tabela})").fetchall()}


def garantir_coluna(db, tabela, coluna, definicao):
    if coluna not in colunas_tabela(db, tabela):
        db.execute(f"ALTER TABLE {tabela} ADD COLUMN {definicao}")


def agora_dt():
    return datetime.now(FUSO_HORARIO)


def formatar_data(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def agora_formatado():
    return formatar_data(agora_dt())


def gerar_token_usuario(db=None):
    alfabeto = string.ascii_uppercase + string.digits
    while True:
        partes = ["".join(secrets.choice(alfabeto) for _ in range(4)) for _ in range(3)]
        token = "-".join(partes)
        if db is None:
            with sqlite3.connect(DATABASE) as banco:
                existe = banco.execute(
                    "SELECT 1 FROM usuarios WHERE token_usuario = ?", (token,)
                ).fetchone()
        else:
            existe = db.execute(
                "SELECT 1 FROM usuarios WHERE token_usuario = ?", (token,)
            ).fetchone()
        if not existe:
            return token


def gerar_token_acesso():
    return secrets.token_urlsafe(24)


def parse_valor(valor):
    texto = (valor or "").strip().replace(",", ".")
    try:
        numero = Decimal(texto).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    except (InvalidOperation, ValueError):
        return None

    if numero < 0:
        return None
    return numero


def parse_int_positivo(valor, padrao):
    try:
        numero = int(str(valor).strip())
    except (TypeError, ValueError):
        return padrao
    return numero if numero > 0 else padrao


def formatar_moeda(valor):
    numero = Decimal(str(valor or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return f"R$ {numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


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
            "SELECT usuario_id FROM cartoes WHERE id = ?", (dispositivo["cartao_id"],)
        ).fetchone()
        if cartao:
            db.execute(
                "UPDATE dispositivos SET usuario_id = ? WHERE id = ?",
                (cartao["usuario_id"], dispositivo["id"]),
            )


def get_config(chave, padrao=None, db=None):
    banco = db or get_db()
    row = banco.execute(
        "SELECT valor FROM configuracoes WHERE chave = ?", (chave,)
    ).fetchone()
    return row["valor"] if row else padrao


def set_config(chave, valor):
    get_db().execute(
        """
        INSERT INTO configuracoes (chave, valor)
        VALUES (?, ?)
        ON CONFLICT(chave) DO UPDATE SET valor = excluded.valor
        """,
        (chave, str(valor)),
    )


def valor_passagem_atual(db=None):
    valor = parse_valor(
        get_config("valor_passagem_padrao", CONFIG_PADRAO["valor_passagem_padrao"], db=db)
    )
    return valor or Decimal(CONFIG_PADRAO["valor_passagem_padrao"])


def valor_minimo_recarga(db=None):
    valor = parse_valor(
        get_config("valor_minimo_recarga", CONFIG_PADRAO["valor_minimo_recarga"], db=db)
    )
    return valor or Decimal(CONFIG_PADRAO["valor_minimo_recarga"])


def valor_maximo_recarga(db=None):
    valor = parse_valor(
        get_config("valor_maximo_recarga", CONFIG_PADRAO["valor_maximo_recarga"], db=db)
    )
    return valor or Decimal(CONFIG_PADRAO["valor_maximo_recarga"])


def horas_retencao_historico(db=None):
    return parse_int_positivo(
        get_config(
            "historico_retencao_horas",
            CONFIG_PADRAO["historico_retencao_horas"],
            db=db,
        ),
        int(CONFIG_PADRAO["historico_retencao_horas"]),
    )


def dias_retencao_recargas(db=None):
    return parse_int_positivo(
        get_config(
            "historico_recargas_retencao_dias",
            CONFIG_PADRAO["historico_recargas_retencao_dias"],
            db=db,
        ),
        int(CONFIG_PADRAO["historico_recargas_retencao_dias"]),
    )


def config_bool(chave, padrao="true", db=None):
    valor = str(get_config(chave, padrao, db=db)).strip().lower()
    return valor in {"1", "true", "sim", "yes", "on"}


def expira_em_formatado():
    return formatar_data(agora_dt() + timedelta(hours=horas_retencao_historico()))


def recarga_expira_em_formatado():
    return formatar_data(agora_dt() + timedelta(days=dias_retencao_recargas()))


def limpar_historico_expirado(db=None):
    banco = db or get_db()
    agora = agora_formatado()
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


def gerar_pdf_cartao(cartao, exibir_saldo=True):
    largura = 242.65
    altura = 153.0
    emitido_em = agora_dt().strftime("%d/%m/%Y %H:%M")
    codigo = str(cartao["codigo_publico"])
    qr_valor = f"CARD:{codigo}"

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=(largura, altura))

    pdf.setFillColor(colors.HexColor("#f4f7f5"))
    pdf.roundRect(0, 0, largura, altura, 10, stroke=0, fill=1)
    pdf.setFillColor(colors.white)
    pdf.roundRect(7, 7, largura - 14, altura - 14, 9, stroke=0, fill=1)

    pdf.setFillColor(colors.HexColor("#0f766e"))
    pdf.roundRect(7, altura - 40, largura - 14, 33, 9, stroke=0, fill=1)
    pdf.setFillColor(colors.white)
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(18, altura - 22, "CATRACA VIRTUAL")
    pdf.setFont("Helvetica", 6.8)
    pdf.drawString(18, altura - 33, "Cartao do Passageiro")

    pdf.setFillColor(colors.HexColor("#18241f"))
    pdf.setFont("Helvetica-Bold", 12)
    nome = str(cartao["nome_usuario"])[:26]
    pdf.drawString(18, 96, nome)

    pdf.setFont("Helvetica", 6.5)
    pdf.setFillColor(colors.HexColor("#61736b"))
    pdf.drawString(18, 82, "CODIGO PUBLICO")
    pdf.setFillColor(colors.HexColor("#10231c"))
    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawString(18, 58, codigo)

    pdf.setFont("Helvetica", 7)
    pdf.setFillColor(colors.HexColor("#18241f"))
    pdf.drawString(18, 42, f"Status: {status_cartao_filter(cartao['status'])}")
    if exibir_saldo:
        pdf.drawString(18, 30, f"Saldo: {formatar_moeda(cartao['saldo'])}")
    pdf.setFont("Helvetica", 5.8)
    pdf.setFillColor(colors.HexColor("#61736b"))
    pdf.drawString(18, 17, f"Emitido em {emitido_em}")

    qr_size = 82
    qr = QrCodeWidget(qr_valor)
    bounds = qr.getBounds()
    qr_width = bounds[2] - bounds[0]
    qr_height = bounds[3] - bounds[1]
    drawing = Drawing(
        qr_size,
        qr_size,
        transform=[qr_size / qr_width, 0, 0, qr_size / qr_height, 0, 0],
    )
    drawing.add(qr)
    renderPDF.draw(drawing, pdf, largura - qr_size - 15, 29)

    pdf.setFillColor(colors.HexColor("#0f766e"))
    pdf.setFont("Helvetica-Bold", 6.2)
    pdf.drawCentredString(largura - 56, 18, qr_valor)

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def extrair_codigo_publico(valor):
    texto = (valor or "").strip()
    if texto.upper().startswith("CARD:"):
        return texto.split(":", 1)[1].strip()
    return texto


def token_da_requisicao():
    return request.values.get("token", "").strip()


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
                "SELECT usuario_id FROM cartoes WHERE id = ?", (acesso["cartao_id"],)
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


def acesso_requerido(*tipos_permitidos):
    def decorar(funcao):
        @wraps(funcao)
        def autorizar(*args, **kwargs):
            token = token_da_requisicao()
            acesso = buscar_acesso(token)

            if acesso is None:
                return (
                    render_template(
                        "acesso_negado.html",
                        titulo="Acesso não autorizado",
                        mensagem="Use o link autorizado fornecido para este dispositivo ou passageiro.",
                    ),
                    401,
                )

            g.acesso = acesso
            g.dispositivo = acesso
            g.token_acesso = token

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


def endpoint_do_dispositivo(tipo):
    return {
        "admin": "admin_home",
        "catraca": "catraca",
        "usuario": "usuario_meu_cartao",
    }[tipo]


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


def estacao_catraca_atual():
    estacao_id = g.acesso.get("estacao_id") if hasattr(g, "acesso") else None
    if not estacao_id:
        estacao_id = estacao_padrao_id()
    return get_db().execute(
        "SELECT id, nome, regiao FROM estacoes WHERE id = ?", (estacao_id,)
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


@app.context_processor
def injetar_contexto_acesso():
    def url_acesso(endpoint, **valores):
        token = getattr(g, "token_acesso", None)
        if token:
            valores.setdefault("token", token)
        return url_for(endpoint, **valores)

    return {
        "dispositivo": getattr(g, "dispositivo", None),
        "acesso": getattr(g, "acesso", None),
        "token_acesso": getattr(g, "token_acesso", ""),
        "static_version": STATIC_VERSION,
        "url_acesso": url_acesso,
    }


@app.template_filter("moeda")
def moeda_filter(valor):
    return formatar_moeda(valor)


@app.template_filter("status_cartao")
def status_cartao_filter(status):
    return "Ativo" if status == "ativo" else "Bloqueado"


@app.get("/")
@app.get("/admin")
@acesso_requerido("admin")
def admin_home():
    limpar_historico_expirado()
    contadores = {
        "cartoes": get_db().execute("SELECT COUNT(*) AS total FROM cartoes").fetchone()["total"],
        "usuarios": get_db().execute("SELECT COUNT(*) AS total FROM usuarios").fetchone()["total"],
        "recargas": get_db().execute("SELECT COUNT(*) AS total FROM recargas").fetchone()["total"],
        "estacoes": get_db().execute(
            "SELECT COUNT(*) AS total FROM estacoes WHERE ativa = 1"
        ).fetchone()["total"],
        "historico": get_db().execute("SELECT COUNT(*) AS total FROM passagens").fetchone()["total"],
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
                criado_em = agora_formatado()
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
                db.execute("COMMIT")
                cartao_criado = get_db().execute(
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
            except sqlite3.Error:
                db.execute("ROLLBACK")
                erro = "Nao foi possivel criar o cartao. Tente novamente."

    return render_template(
        "criar_cartao.html",
        erro=erro,
        cartao_criado=cartao_criado,
        dados_form=dados_form,
    )


@app.route("/cartao", methods=["GET", "POST"])
@acesso_requerido("usuario")
def visualizar_cartao():
    if g.acesso["tipo"] == "usuario":
        return redirect(url_for("usuario_meu_cartao", token=g.token_acesso))
    return redirect(url_for("admin_cartoes", token=g.token_acesso))


@app.get("/meu/<token_usuario>")
def acesso_rapido_usuario(token_usuario):
    acesso = buscar_acesso(token_usuario)
    if not acesso or acesso["tipo"] != "usuario":
        return (
            render_template(
                "acesso_negado.html",
                titulo="Acesso nao autorizado",
                mensagem="Use um link privado valido do passageiro.",
            ),
            401,
        )
    return redirect(url_for("usuario_meu_cartao", token=token_usuario))


@app.get("/usuario/meu-cartao")
@acesso_requerido("usuario")
def usuario_meu_cartao():
    cartao = None
    erro = None
    if not g.acesso.get("usuario_id"):
        erro = "Este acesso de usuario ainda nao foi vinculado a um passageiro."
    else:
        cartao = cartao_do_usuario(g.acesso["usuario_id"])
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


def valores_recarga_padrao():
    return [Decimal("10.00"), Decimal("20.00"), Decimal("50.00"), Decimal("100.00")]


def cartao_usuario_atual_ou_erro():
    if not g.acesso.get("usuario_id"):
        return None, "Este acesso de usuario ainda nao foi vinculado a um passageiro."
    cartao = cartao_do_usuario(g.acesso["usuario_id"])
    if not cartao:
        return None, "Nenhum cartao foi encontrado para este usuario."
    return cartao, None


@app.route("/usuario/recarregar-cartao", methods=["GET", "POST"])
@app.post("/usuario/recarregar-cartao/confirmar")
@acesso_requerido("usuario")
def usuario_recarregar_cartao():
    cartao, erro = cartao_usuario_atual_ou_erro()
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
                    saldo_anterior = Decimal(str(cartao_atual["saldo"])).quantize(Decimal("0.01"))
                    saldo_novo = saldo_anterior + valor
                    db.execute(
                        """
                        UPDATE cartoes
                        SET saldo = ?, atualizado_em = ?
                        WHERE id = ? AND usuario_id = ?
                        """,
                        (
                            float(saldo_novo),
                            agora_formatado(),
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
                    cartao = cartao_do_usuario(g.acesso["usuario_id"])
                    sucesso = {
                        "valor": valor,
                        "saldo_anterior": saldo_anterior,
                        "saldo_novo": saldo_novo,
                    }
            except sqlite3.Error:
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
    cartao, erro = cartao_usuario_atual_ou_erro()
    recargas = []
    if cartao:
        recargas = get_db().execute(
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

    cartao, erro = cartao_usuario_atual_ou_erro()
    if not cartao:
        return (
            render_template(
                "acesso_negado.html",
                titulo="Cartao nao encontrado",
                mensagem=erro,
            ),
            404,
        )

    pdf = gerar_pdf_cartao(
        cartao,
        exibir_saldo=config_bool("exibir_saldo_no_pdf", CONFIG_PADRAO["exibir_saldo_no_pdf"]),
    )
    nome_arquivo = f"cartao-{cartao['codigo_publico']}.pdf"
    return Response(
        pdf,
        mimetype="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={nome_arquivo}"},
    )


def decodificar_trechos(valor):
    trechos = []
    for parte in (valor or "").split(";"):
        if not parte or "-" not in parte:
            continue
        origem, destino = parte.split("-", 1)
        if origem.isdigit() and destino.isdigit():
            trechos.append((int(origem), int(destino)))
    return trechos


def codificar_trechos(trechos):
    return ";".join(f"{origem}-{destino}" for origem, destino in trechos)


def trechos_preview(trechos):
    if not trechos:
        return []
    ids = sorted({item for trecho in trechos for item in trecho})
    placeholders = ",".join("?" for _ in ids)
    linhas = get_db().execute(
        f"SELECT id, nome FROM estacoes WHERE id IN ({placeholders})", ids
    ).fetchall()
    nomes = {linha["id"]: linha["nome"] for linha in linhas}
    return [
        {
            "ordem": indice + 1,
            "origem_id": origem,
            "destino_id": destino,
            "origem_nome": nomes.get(origem, "-"),
            "destino_nome": nomes.get(destino, "-"),
        }
        for indice, (origem, destino) in enumerate(trechos)
    ]


@app.route("/usuario/planejar-viagem", methods=["GET", "POST"])
@acesso_requerido("usuario")
def usuario_planejar_viagem():
    cartao = cartao_do_usuario(g.acesso.get("usuario_id")) if g.acesso.get("usuario_id") else None
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
                        (cartao["usuario_id"], cartao["id"], agora_formatado()),
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
                    return redirect(url_for("usuario_minha_viagem", token=g.token_acesso))
                except sqlite3.Error:
                    db.execute("ROLLBACK")
                    erro = "Nao foi possivel salvar a viagem."

    return render_template(
        "planejar_viagem.html",
        cartao=cartao,
        erro=erro,
        estacoes=estacoes_ativas(),
        trechos=trechos_preview(trechos),
        trechos_serializados=codificar_trechos(trechos),
        valor_passagem=valor_passagem_atual(),
    )


@app.get("/usuario/minha-viagem")
@acesso_requerido("usuario")
def usuario_minha_viagem():
    cartao = cartao_do_usuario(g.acesso.get("usuario_id")) if g.acesso.get("usuario_id") else None
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
    cartao = cartao_do_usuario(g.acesso.get("usuario_id")) if g.acesso.get("usuario_id") else None
    if not cartao:
        flash("Nenhum cartao encontrado para este usuario.")
    else:
        get_db().execute(
            """
            UPDATE rotas_viagem
            SET status = 'cancelada'
            WHERE usuario_id = ? AND cartao_id = ? AND status = 'planejada'
            """,
            (cartao["usuario_id"], cartao["id"]),
        )
        flash("Rota cancelada.")
    return redirect(url_for("usuario_minha_viagem", token=g.token_acesso))


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
    cartao_digitado = extrair_codigo_publico(request.form.get("cartao_id", ""))
    resultado = validar_entrada(cartao_digitado)
    return render_template(
        "catraca.html",
        valor_passagem=valor_passagem_atual(),
        resultado=resultado,
        cartao_id=cartao_digitado,
        estacao=estacao_catraca_atual(),
    )


def validar_entrada(cartao_digitado):
    db = get_db()
    cartao_digitado = extrair_codigo_publico(cartao_digitado)
    estacao = estacao_catraca_atual()
    origem_id = estacao["id"] if estacao else None
    valor_passagem = valor_passagem_atual()
    db.execute("BEGIN IMMEDIATE")
    try:
        if not cartao_digitado:
            registrar_passagem(
                db,
                None,
                cartao_digitado,
                "negado",
                "ID publico nao informado.",
                Decimal("0.00"),
                origem_id=origem_id,
            )
            db.execute("COMMIT")
            return {"aprovado": False, "titulo": "Entrada negada.", "mensagem": "ID publico nao informado."}

        cartao = db.execute(
            """
            SELECT
                cartoes.*,
                usuarios.nome AS nome_usuario
            FROM cartoes
            JOIN usuarios ON usuarios.id = cartoes.usuario_id
            WHERE cartoes.codigo_publico = ?
            """,
            (cartao_digitado,),
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
            return {"aprovado": False, "titulo": "Entrada negada.", "mensagem": "Cartao nao encontrado."}

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
        return {
            "aprovado": True,
            "titulo": "Entrada aprovada.",
            "mensagem": "Boa viagem!",
            "codigo_publico": cartao["codigo_publico"],
        }
    except sqlite3.Error:
        db.execute("ROLLBACK")
        return {"aprovado": False, "titulo": "Entrada negada.", "mensagem": "Falha ao validar. Tente novamente."}


@app.get("/historico")
@app.get("/admin/historico")
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
    return redirect(url_for("admin_cartoes", token=g.token_acesso))


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
                return redirect(url_for("admin_estacoes", token=g.token_acesso))
            except sqlite3.IntegrityError:
                erro = "Ja existe uma estacao com esse nome."
    estacoes = get_db().execute("SELECT * FROM estacoes ORDER BY ativa DESC, nome").fetchall()
    return render_template("admin_estacoes.html", estacoes=estacoes, erro=erro)


@app.post("/admin/estacoes/<int:estacao_id>/alternar")
@acesso_requerido("admin")
def admin_alternar_estacao(estacao_id):
    estacao = get_db().execute(
        "SELECT id, ativa FROM estacoes WHERE id = ?", (estacao_id,)
    ).fetchone()
    if not estacao:
        flash("Estacao nao encontrada.")
    else:
        get_db().execute(
            "UPDATE estacoes SET ativa = ? WHERE id = ?",
            (0 if estacao["ativa"] else 1, estacao_id),
        )
        flash("Status da estacao atualizado.")
    return redirect(url_for("admin_estacoes", token=g.token_acesso))


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
            return redirect(url_for("admin_configuracoes", token=g.token_acesso))

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
                cartao_id = int(dados_form["cartao_id"])
                cartao = get_db().execute(
                    "SELECT id, usuario_id FROM cartoes WHERE id = ?", (cartao_id,)
                ).fetchone()
                if not cartao:
                    erro = "O cartao informado nao existe."
                else:
                    usuario_id = cartao["usuario_id"]
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
                return redirect(url_for("dispositivos", token=g.token_acesso))
            except sqlite3.Error:
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
        dispositivo["id"]: url_for(
            endpoint_do_dispositivo(dispositivo["tipo"]),
            token=dispositivo["token_acesso"],
            _external=True,
        )
        for dispositivo in lista_dispositivos
    }

    return render_template(
        "dispositivos.html",
        lista_dispositivos=lista_dispositivos,
        cartoes=cartoes,
        estacoes=estacoes,
        links_acesso=links_acesso,
        erro=erro,
        dados_form=dados_form,
    )


@app.post("/dispositivos/<int:dispositivo_id>/vincular")
@acesso_requerido("admin")
def vincular_dispositivo(dispositivo_id):
    cartao_id_texto = request.form.get("cartao_id", "").strip()
    estacao_id_texto = request.form.get("estacao_id", "").strip()
    db = get_db()
    dispositivo = db.execute(
        "SELECT id, tipo FROM dispositivos WHERE id = ?", (dispositivo_id,)
    ).fetchone()

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

    return redirect(url_for("dispositivos", token=g.token_acesso))


@app.post("/dispositivos/<int:dispositivo_id>/alternar")
@acesso_requerido("admin")
def alternar_dispositivo(dispositivo_id):
    if dispositivo_id == g.acesso.get("id"):
        flash("O dispositivo administrativo em uso nao pode ser desativado.")
        return redirect(url_for("dispositivos", token=g.token_acesso))

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

    return redirect(url_for("dispositivos", token=g.token_acesso))


@app.get("/health")
def health():
    return {"status": "ok"}


init_db()


if __name__ == "__main__":
    porta = int(os.getenv("PORT", "5000"))
    modo_debug = os.getenv("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=porta, debug=modo_debug)
