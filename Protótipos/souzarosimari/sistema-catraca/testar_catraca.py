"""
testar_catraca.py
==================
Script utilitário que simula, via requisições HTTP, o comportamento dos
celulares do passageiro e do operador, sem precisar digitar nada
manualmente em dois navegadores diferentes.

Pré-requisitos:
    1. O servidor Flask precisa estar rodando (python app.py).
    2. É recomendado rodar antes "python popular_banco.py" para garantir
       os IDs 1001-1005 usados nos testes abaixo.

Uso:
    python testar_catraca.py
"""

import time

import requests

BASE_URL = "http://127.0.0.1:5000"


def executar_testes():
    print("Iniciando testes automatizados da Catraca Virtual...")
    print("-" * 56)

    try:
        requests.get(BASE_URL, timeout=5)
    except requests.exceptions.ConnectionError:
        print("ERRO: o servidor Flask não está rodando.")
        print("Execute 'python app.py' em outro terminal e tente novamente.")
        return

    casos = [
        (1001, "Cartão ativo com saldo (deve aprovar)"),
        (1001, "Mesmo cartão de novo (deve aprovar e descontar outra vez)"),
        (1003, "Cartão ativo sem saldo suficiente (deve negar)"),
        (1004, "Cartão bloqueado (deve negar mesmo com saldo)"),
        (9999, "Cartão inexistente (deve negar)"),
    ]

    print("\nSimulando validações na catraca:")
    print("-" * 56)
    for cartao_id, descricao in casos:
        resposta = requests.post(f"{BASE_URL}/catraca", data={"cartao_id": cartao_id})
        texto = resposta.text

        if "Entrada aprovada" in texto:
            resultado = "APROVADO"
        elif "Entrada negada" in texto:
            resultado = "NEGADO"
        else:
            resultado = "RESPOSTA INESPERADA"

        print(f"ID {cartao_id:>5} | {descricao}")
        print(f"          -> {resultado}")
        time.sleep(0.5)

    print("-" * 56)
    print("Verificando a página de histórico...")
    resposta_historico = requests.get(f"{BASE_URL}/historico")
    if "Histórico de passagens" in resposta_historico.text:
        print("Histórico carregado com sucesso.")
    else:
        print("Não foi possível confirmar o carregamento do histórico.")

    print("\nTestes finalizados. Confira as telas no navegador para o efeito visual.")


if __name__ == "__main__":
    executar_testes()
