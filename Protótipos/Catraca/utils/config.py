from pathlib import Path
from datetime import timedelta
from decimal import Decimal

from .helpers import parse_int_positivo, parse_valor

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASE = BASE_DIR / "database.db"
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
    ("Computador administrativo", "admin", __import__("os").getenv("ADMIN_TOKEN", "admin-demo-2026")),
    ("Catraca virtual principal", "catraca", __import__("os").getenv("CATRACA_TOKEN", "catraca-demo-2026")),
    ("Celular do passageiro", "usuario", __import__("os").getenv("USUARIO_TOKEN", "usuario-demo-2026")),
)
ESTACOES_PADRAO = (
    ("Terminal Central", "Centro"),
    ("Centro", "Centro"),
    ("Higienopolis", "Centro"),
    ("Ipiranga", "Centro"),
    ("Petropolis", "Centro"),
    ("Quebec", "Centro"),
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


def _get_db():
    from .database import get_db

    return get_db()


def get_config(chave, padrao=None, db=None):
    banco = db or _get_db()
    row = banco.execute(
        "SELECT valor FROM configuracoes WHERE chave = ?",
        (chave,),
    ).fetchone()
    return row["valor"] if row else padrao


def set_config(chave, valor):
    from .database import get_db

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
    from .helpers import agora_dt, formatar_data

    return formatar_data(agora_dt() + timedelta(hours=horas_retencao_historico()))


def recarga_expira_em_formatado():
    from .helpers import agora_dt, formatar_data

    return formatar_data(agora_dt() + timedelta(days=dias_retencao_recargas()))
