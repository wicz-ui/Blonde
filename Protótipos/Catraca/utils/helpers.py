import secrets
import string
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from zoneinfo import ZoneInfo

FUSO_HORARIO = ZoneInfo("America/Sao_Paulo")


def agora_dt():
    return datetime.now(FUSO_HORARIO)


def formatar_data(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def agora_formatado():
    return formatar_data(agora_dt())


def gerar_token_usuario(db=None):
    from .database import get_db

    alfabeto = string.ascii_uppercase + string.digits
    while True:
        partes = ["".join(secrets.choice(alfabeto) for _ in range(4)) for _ in range(3)]
        token = "-".join(partes)
        banco = db or get_db()
        existe = banco.execute(
            "SELECT 1 FROM usuarios WHERE token_usuario = ?",
            (token,),
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


def extrair_codigo_publico(valor):
    texto = (valor or "").strip()
    if texto.upper().startswith("CARD:"):
        return texto.split(":", 1)[1].strip()
    return texto


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


def valores_recarga_padrao():
    return [Decimal("10.00"), Decimal("20.00"), Decimal("50.00"), Decimal("100.00")]


def endpoint_do_dispositivo(tipo):
    return {
        "admin": "admin_home",
        "catraca": "catraca",
        "usuario": "usuario_meu_cartao",
    }[tipo]


def status_cartao_filter(status):
    return "Ativo" if status == "ativo" else "Bloqueado"
