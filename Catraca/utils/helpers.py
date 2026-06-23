import secrets
import string
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from zoneinfo import ZoneInfo

FUSO_HORARIO = ZoneInfo("America/Sao_Paulo")
DDD_PADRAO = "43"
CODIGO_PAIS_BRASIL = "55"


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
    texto = str(valor or "").strip().removeprefix("R$").strip()
    texto = texto.replace(" ", "")
    if not texto:
        return None

    if re.fullmatch(r"\d+(?:[,.]\d{1,2})?", texto):
        numero_normalizado = texto.replace(",", ".")
    elif re.fullmatch(r"\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?", texto):
        numero_normalizado = texto.replace(".", "").replace(",", ".")
    else:
        return None

    try:
        numero = Decimal(numero_normalizado).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
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
    numero = parse_valor(valor) if isinstance(valor, str) else None
    if numero is None:
        try:
            numero = Decimal(str(valor or 0)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        except (InvalidOperation, ValueError):
            numero = Decimal("0.00")
    return f"R$ {numero:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def formatar_valor_para_input(valor):
    numero = parse_valor(valor) if isinstance(valor, str) else None
    if numero is None:
        try:
            numero = Decimal(str(valor or 0)).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
        except (InvalidOperation, ValueError):
            numero = Decimal("0.00")
    return f"{numero:.2f}".replace(".", ",")


def normalizar_nome_passageiro(valor):
    return " ".join((valor or "").strip().split()).upper()


def somente_digitos(valor):
    return "".join(caractere for caractere in str(valor or "") if caractere.isdigit())


def normalizar_cpf(valor):
    cpf = somente_digitos(valor)
    return cpf if len(cpf) == 11 else None


def formatar_cpf(valor):
    cpf = somente_digitos(valor)
    if len(cpf) != 11:
        return cpf
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"


def normalizar_celular(valor):
    numero = somente_digitos(valor)
    if numero.startswith(CODIGO_PAIS_BRASIL):
        numero = numero[len(CODIGO_PAIS_BRASIL) :]
    if numero.startswith(DDD_PADRAO):
        numero = numero[len(DDD_PADRAO) :]

    if len(numero) != 9:
        return None
    return f"{CODIGO_PAIS_BRASIL}{DDD_PADRAO}{numero}"


def formatar_celular(valor):
    numero = somente_digitos(valor)
    if numero.startswith(CODIGO_PAIS_BRASIL):
        numero = numero[len(CODIGO_PAIS_BRASIL) :]
    if numero.startswith(DDD_PADRAO):
        numero = numero[len(DDD_PADRAO) :]
    if len(numero) != 9:
        return somente_digitos(valor)
    return f"+{CODIGO_PAIS_BRASIL} ({DDD_PADRAO}) {numero[:5]}-{numero[5:]}"


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
