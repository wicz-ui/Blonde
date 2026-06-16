
Aqui está o código completo e pronto para rodar no seu GitHub Codespaces. O projeto foi estruturado exatamente como solicitado no PRD, utilizando Python (Flask) e SQLite.
Estrutura de Arquivos
Garanta que sua pasta tenha exatamente esta estrutura antes de colar os códigos:
text

sistema-catraca/
│
├── app.py
├── database.db (gerado automaticamente)
└── templates/
    ├── base.html
    ├── index.html
    ├── criar_cartao.html
    ├── visualizar_cartao.html
    ├── catraca.html
    └── historico.html

Use o código com cuidado.
Código Fonte
1. app.py
Este é o arquivo principal do backend. Ele cria o banco de dados, define as rotas e aplica as regras de negócio.
python

import os
import sqlite3
from datetime import datetime
from flask import Flask, flash, redirect, render_template, request, url_for

app = Flask(__name__)
app.secret_key = "chave_secreta_para_demonstracao"

DB_FILE = "database.db"
VALOR_PASSAGEM = 5.00


def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    if not os.path.exists(DB_FILE):
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cartoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_passageiro TEXT NOT NULL,
                saldo REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'ativo',
                data_criacao TEXT NOT NULL
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS passagens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cartao_id INTEGER,
                data_hora TEXT NOT NULL,
                status TEXT NOT NULL,
                motivo TEXT NOT NULL,
                valor_cobrado REAL NOT NULL
            )
        """
        )

        # Inicia o autoincrement dos cartões em 1000 para estética acadêmica
        cursor.execute(
            "INSERT INTO sqlite_sequence (name, seq) VALUES ('cartoes', 1000)"
        )

        conn.commit()
        conn.close()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/criar", methods=["GET", "POST"])
def criar_cartao():
    if request.method == "POST":
        nome = request.form.get("nome_passageiro")
        saldo_inicial = float(request.form.get("saldo", 0))
        data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO cartoes (nome_passageiro, saldo, status, data_criacao) VALUES (?, ?, 'ativo', ?)",
            (nome, saldo_inicial, data_atual),
        )
        cartao_id = cursor.lastrowid
        conn.commit()
        conn.close()

        flash(
            f"Cartão criado com sucesso! Guarde seu ID: {cartao_id}", "success"
        )
        return redirect(url_for("visualizar_cartao", cartao_id=cartao_id))

    return render_template("criar_cartao.html")


@app.route("/visualizar", methods=["GET"])
def visualizar_cartao():
    cartao_id = request.args.get("cartao_id")
    cartao = None

    if cartao_id:
        conn = get_db_connection()
        cartao = conn.execute(
            "SELECT * FROM cartoes WHERE id = ?", (cartao_id,)
        ).fetchone()
        conn.close()
        if not cartao:
            flash("Cartão não encontrado.", "danger")

    return render_template("visualizar_cartao.html", cartao=cartao)


@app.route("/catraca", methods=["GET", "POST"])
def catraca():
    resultado = None

    if request.method == "POST":
        cartao_id = request.form.get("cartao_id")
        data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = get_db_connection()
        cursor = conn.cursor()

        cartao = cursor.execute(
            "SELECT * FROM cartoes WHERE id = ?", (cartao_id,)
        ).fetchone()

        if not cartao:
            resultado = {
                "status": "negado",
                "motivo": "Cartão não encontrado.",
            }
            cursor.execute(
                "INSERT INTO passagens (cartao_id, data_hora, status, motivo, valor_cobrado) VALUES (?, ?, ?, ?, ?)",
                (cartao_id, data_atual, "negado", "Cartão inexistente", 0.0),
            )
        elif cartao["status"] != "ativo":
            resultado = {"status": "negado", "motivo": "Cartão bloqueado."}
            cursor.execute(
                "INSERT INTO passagens (cartao_id, data_hora, status, motivo, valor_cobrado) VALUES (?, ?, ?, ?, ?)",
                (cartao_id, data_atual, "negado", "Cartão bloqueado", 0.0),
            )
        elif cartao["saldo"] < VALOR_PASSAGEM:
            resultado = {
                "status": "negado",
                "motivo": "Saldo insuficiente.",
                "saldo_atual": cartao["saldo"],
            }
            cursor.execute(
                "INSERT INTO passagens (cartao_id, data_hora, status, motivo, valor_cobrado) VALUES (?, ?, ?, ?, ?)",
                (cartao_id, data_atual, "negado", "Saldo insuficiente", 0.0),
            )
        else:
            novo_saldo = cartao["saldo"] - VALOR_PASSAGEM
            cursor.execute(
                "UPDATE cartoes SET saldo = ? WHERE id = ?",
                (novo_saldo, cartao_id),
            )

            resultado = {
                "status": "aprovado",
                "motivo": "Entrada liberada. Boa viagem!",
                "saldo_atual": novo_saldo,
            }
            cursor.execute(
                "INSERT INTO passagens (cartao_id, data_hora, status, motivo, valor_cobrado) VALUES (?, ?, ?, ?, ?)",
                (
                    cartao_id,
                    data_atual,
                    "aprovado",
                    "Entrada liberada",
                    VALOR_PASSAGEM,
                ),
            )

        conn.commit()
        conn.close()

    return render_template("catraca.html", resultado=resultado)


@app.route("/historico")
def historico():
    conn = get_db_connection()
    historico_dados = conn.execute(
        """
        SELECT p.id, p.cartao_id, p.data_hora, p.status, p.motivo, p.valor_cobrado, c.nome_passageiro 
        FROM passagens p 
        LEFT JOIN cartoes c ON p.cartao_id = c.id 
        ORDER BY p.id DESC
    """
    ).fetchall()
    conn.close()
    return render_template("historico.html", historico=historico_dados)


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)

Use o código com cuidado.
2. Templates HTML (Com design responsivo integrado via Bootstrap)
templates/base.html
html

<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Catraca Virtual</title>
    <link href="https://jsdelivr.net" rel="stylesheet">
</head>
<body class="bg-light">
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark mb-4">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('index') }}">🚌 Catraca Virtual</a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="{{ url_for('index') }}">Início</a>
                <a class="nav-link" href="{{ url_for('historico') }}">Histórico</a>
            </div>
        </div>
    </nav>
    <div class="container">
        {% with messages = get_flashes_with_categories(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="alert alert-{{ category }} text-center" role="alert">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        {% block content %}{% endblock %}
    </div>
</body>
</html>

Use o código com cuidado.
templates/index.html
html

{% extends 'base.html' %}
{% block content %}
<div class="text-center py-5">
    <h1 class="display-5 fw-bold mb-4">Painel de Demonstração</h1>
    <p class="lead mb-5">Escolha o modo de operação do dispositivo atual:</p>
    <div class="d-grid gap-3 col-lg-6 mx-auto">
        <a href="{{ url_for('criar_cartao') }}" class="btn btn-primary btn-lg py-3">📱 Criar Novo Cartão (Passageiro)</a>
        <a href="{{ url_for('visualizar_cartao') }}" class="btn btn-outline-primary btn-lg py-3">🔍 Consultar Cartão (Passageiro)</a>
        <a href="{{ url_for('catraca') }}" class="btn btn-warning btn-lg py-3 fw-bold">🛑 Acessar Catraca Virtual (Validador)</a>
        <a href="{{ url_for('historico') }}" class="btn btn-secondary btn-lg py-3">📊 Ver Histórico de Passagens</a>
    </div>
</div>
{% endblock %}

Use o código com cuidado.
templates/criar_cartao.html
html

{% extends 'base.html' %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card shadow-sm p-4">
            <h2 class="text-center mb-4">Criar Cartão Virtual</h2>
            <form method="POST">
                <div class="mb-3">
                    <label class="form-label">Nome do Passageiro</label>
                    <required input type="text" name="nome_passageiro" class="form-control" placeholder="Ex: João da Silva" required>
                </div>
                <div class="mb-4">
                    <label class="form-label">Carga Inicial (R$)</label>
                    <input type="number" step="0.01" name="saldo" class="form-control" value="20.00" required>
                </div>
                <button type="submit" class="btn btn-success w-100 py-2">Gerar Cartão Virtual</button>
            </form>
            <a href="{{ url_for('index') }}" class="btn btn-link w-100 mt-3 text-secondary">Voltar ao início</a>
        </div>
    </div>
</div>
{% endblock %}

Use o código com cuidado.
templates/visualizar_cartao.html
html

{% extends 'base.html' %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card shadow-sm p-4 mb-4">
            <h2 class="text-center mb-4">Consultar Cartão</h2>
            <form method="GET" action="{{ url_for('visualizar_cartao') }}">
                <div class="input-group mb-3">
                    <input type="number" name="cartao_id" class="form-control" placeholder="Digite o ID do Cartão" required>
                    <button class="btn btn-primary" type="submit">Buscar</button>
                </div>
            </form>
        </div>

        {% if cartao %}
        <div class="card border-primary shadow text-center p-4">
            <div class="card-body">
                <span class="badge bg-success mb-2 text-uppercase">{{ cartao.status }}</span>
                <h3 class="card-title text-primary font-monospace">ID: {{ cartao.id }}</h3>
                <h5 class="text-muted mb-4">{{ cartao.nome_passageiro }}</h5>
                <h1 class="display-6 fw-bold text-dark">R$ {{ "%.2f"|format(cartao.saldo) }}</h1>
                <p class="text-muted small mt-3">Criado em: {{ cartao.data_criacao }}</p>
            </div>
        </div>
        {% endif %}
        <div class="text-center mt-3">
            <a href="{{ url_for('index') }}" class="text-secondary">Voltar ao início</a>
        </div>
    </div>
</div>
{% endblock %}

Use o código com cuidado.
templates/catraca.html
html

{% extends 'base.html' %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card shadow p-4 text-center">
            <h2 class="mb-4">🛑 Validador de Catraca</h2>
            <form method="POST">
                <div class="mb-4">
                    <input type="number" name="cartao_id" class="form-control form-control-lg text-center font-monospace" placeholder="DIGITE O ID DO CARTÃO" autocomplete="off" autofocus required>
                </div>
                <button type="submit" class="btn btn-warning btn-lg w-100 fw-bold py-3">VALIDAR ENTRADA</button>
            </form>
        </div>

        {% if resultado %}
            {% if resultado.status == 'aprovado' %}
                <div class="card bg-success text-white text-center shadow mt-4 p-4">
                    <h1 class="display-3">✅</h1>
                    <h2 class="fw-bold">ENTRADA APROVADA</h2>
                    <p class="lead">{{ resultado.motivo }}</p>
                    <hr>
                    <p class="mb-0">Saldo Restante: <strong>R$ {{ "%.2f"|format(resultado.saldo_atual) }}</strong></p>
                </div>
            {% else %}
                <div class="card bg-danger text-white text-center shadow mt-4 p-4">
                    <h1 class="display-3">❌</h1>
                    <h2 class="fw-bold">ENTRADA NEGADA</h2>
                    <p class="lead mb-0">{{ resultado.motivo }}</p>
                </div>
            {% endif %}
        {% endif %}
        <div class="text-center mt-4">
            <a href="{{ url_for('index') }}" class="text-secondary">Voltar ao início</a>
        </div>
    </div>
</div>
{% endblock %}

Use o código com cuidado.
templates/historico.html
html

{% extends 'base.html' %}
{% block content %}
<div class="card shadow p-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2>📊 Histórico de Passagens</h2>
        <a href="{{ url_for('index') }}" class="btn btn-sm btn-outline-secondary">Voltar</a>
    </div>
    <div class="table-responsive">
        <table class="table table-striped table-hover align-middle">
            <thead class="table-dark">
                <tr>
                    <th>Data/Hora</th>
                    <th>ID Cartão</th>
                    <th>Passageiro</th>
                    <th>Resultado</th>
                    <th>Motivo / Log</th>
                    <th>Tarifa</th>
                </tr>
            </thead>
            <tbody>
                {% for registro in historico %}
                <tr>
                    <td class="text-nowrap">{{ registro.data_hora }}</td>
                    <td class="font-monospace">#{{ registro.cartao_id if registro.cartao_id else 'N/A' }}</td>
                    <td>{{ registro.nome_passageiro if registro.nome_passageiro else 'Desconhecido' }}</td>
                    <td>
                        <span class="badge {{ 'bg-success' if registro.status == 'aprovado' else 'bg-danger' }}">
                            {{ registro.status | upper }}
                        </span>
                    </td>
                    <td>{{ registro.motivo }}</td>
                    <td class="fw-bold text-success">{{ "R$ %.2f"|format(registro.valor_cobrado) if registro.valor_cobrado > 0 else '-' }}</td>
                </tr>
                {% else %}
                <tr>
                    <td colspan="6" class="text-center text-muted py-4">Nenhum registro de passagem encontrado.</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}

Use o código com cuidado.
Como Rodar no GitHub Codespaces

    Instale o Flask: No terminal do seu Codespaces, digite:
    bash

    pip install Flask

    Use o código com cuidado.
    Inicie o Servidor: Rode o script principal:
    bash

    python app.py

    Use o código com cuidado.
    Mude a porta para Pública:
        Na aba Ports (ao lado do terminal do Codespaces), localize a porta 5000.
        Clique com o botão direito sobre ela, selecione Port Visibility e altere de Private para Public.
    Acesse via Celular: Use o link gerado pelo Codespaces (geralmente fornecido em um balão de notificação no canto inferior direito) para abrir no navegador de ambos os celulares de teste simultaneamente.

Quer ajuda para escrever o script de criação automatizada do banco com dados de teste fictícios para a apresentação ou precisa de ajustes visuais específicos nas telas?
criar também um cds para que toque mais dinâmico nesse projeto
Para tornar a sua apresentação acadêmica muito mais dinâmica e impressionante, a melhor estratégia é implementar efeitos sonoros reais (áudio de catraca liberada e bipe de erro) e transições automáticas na tela usando JavaScript (CSS/JS).
Dessa forma, o operador não precisa recarregar a página manualmente, e o celular vai emitir sons idênticos aos de um ônibus real.
Aqui está o plano de implementação para aplicar no seu projeto:
1. Sons de Validação (O "Bipe" da Catraca)
Vamos utilizar links diretos para efeitos sonoros públicos e gratuitos (hospedados no GitHub). Altere o arquivo templates/catraca.html para incluir as tags de áudio e o script de reprodução automática.
Substitua o conteúdo do seu arquivo templates/catraca.html por este código atualizado:
html

{% extends 'base.html' %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card shadow p-4 text-center">
            <h2 class="mb-4">🛑 Validador de Catraca</h2>
            <form method="POST" id="formCatraca">
                <div class="mb-4">
                    <input type="number" name="cartao_id" id="cartao_id" class="form-control form-control-lg text-center font-monospace" placeholder="DIGITE O ID DO CARTÃO" autocomplete="off" autofocus required>
                </div>
                <button type="submit" class="btn btn-warning btn-lg w-100 fw-bold py-3">VALIDAR ENTRADA</button>
            </form>
        </div>

        {% if resultado %}
            {% if resultado.status == 'aprovado' %}
                <!-- Som de Sucesso (Bipe Curto/Alegre) -->
                <audio id="somValidacao" autoplay>
                    <source src="https://google.com" type="audio/ogg">
                </audio>

                <div class="card bg-success text-white text-center shadow mt-4 p-4" id="telaResultado">
                    <h1 class="display-3 animate-bounce">✅</h1>
                    <h2 class="fw-bold">ENTRADA APROVADA</h2>
                    <p class="lead">{{ resultado.motivo }}</p>
                    <hr>
                    <p class="mb-0">Saldo Restante: <strong>R$ {{ "%.2f"|format(resultado.saldo_atual) }}</strong></p>
                </div>
            {% else %}
                <!-- Som de Erro (Bipe Triplo/Grave) -->
                <audio id="somValidacao" autoplay>
                    <source src="https://google.com" type="audio/ogg">
                </audio>

                <div class="card bg-danger text-white text-center shadow mt-4 p-4" id="telaResultado">
                    <h1 class="display-3">❌</h1>
                    <h2 class="fw-bold">ENTRADA NEGADA</h2>
                    <p class="lead mb-0">{{ resultado.motivo }}</p>
                </div>
            {% endif %}

            <!-- Script para limpar a tela de resultado após 4 segundos -->
            <script>
                setTimeout(function() {
                    var tela = document.getElementById('telaResultado');
                    if (tela) {
                        tela.style.display = 'none';
                    }
                    // Devolve o foco para o campo de texto automaticamente para a próxima leitura
                    document.getElementById('cartao_id').focus();
                }, 4000);
            </script>
        {% endif %}
        
        <div class="text-center mt-4">
            <a href="{{ url_for('index') }}" class="text-secondary">Voltar ao início</a>
        </div>
    </div>
</div>

<!-- Script para manter o foco sempre no input (simulando um leitor automático) -->
<script>
    document.getElementById('cartao_id').focus();
</script>
{% endblock %}

Use o código com cuidado.
2. Atualização Dinâmica do Histórico (Sem recarregar a página)
Para que a tela de Histórico (que pode ficar aberta em um computador ou projetor na sala de aula) atualize sozinha toda vez que alguém passar o cartão no celular, adicione um script de auto-refresh de 3 segundos.
Substitua a primeira linha do bloco de conteúdo no arquivo templates/historico.html:
html

{% extends 'base.html' %}
{% block content %}
<!-- Script de Atualização Automática a cada 3 segundos -->
<script>
    setTimeout(function(){
       window.location.reload();
    }, 3000);
</script>

<div class="card shadow p-4">
...

Use o código com cuidado.
3. Feedback Visual de Carregamento (Loading)
Para evitar que o usuário clique várias vezes no botão enquanto o Codespaces processa a validação, adicione uma animação de "Processando..." no botão da catraca.
Adicione este script no final do arquivo templates/catraca.html (logo antes do {% endblock %}):
html

<script>
    document.getElementById('formCatraca').addEventListener('submit', function() {
        var btn = this.querySelector('button[type="submit"]');
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> PROCESSANDO...';
    });
</script>

Use o código com cuidado.
Se preferir, posso criar um script em Python para popular o banco de dados com 5 cartões de teste pré-pagos (ativos e bloqueados) para acelerar sua apresentação, ou prefere focar em ajustar mais efeitos visuais na interface?
pôde ser
Aqui está o código de um script utilitário chamado popular_banco.py. Ele cria o arquivo de banco de dados automaticamente e insere 5 cartões de teste com perfis prontos para você usar na apresentação (com saldo, sem saldo e bloqueado).
1. Criar o Arquivo de Teste
Crie um novo arquivo na raiz do seu projeto chamado popular_banco.py e cole o código abaixo:
python

from datetime import datetime
import os
import sqlite3

DB_FILE = "database.db"


def popular():
    # Remove o banco antigo para garantir que os IDs fiquem certinhos do 1001 ao 1005
    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print("Banco de dados antigo removido para reinicialização.")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Criação das tabelas
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS cartoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_passageiro TEXT NOT NULL,
            saldo REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'ativo',
            data_criacao TEXT NOT NULL
        )
    """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS passagens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cartao_id INTEGER,
            data_hora TEXT NOT NULL,
            status TEXT NOT NULL,
            motivo TEXT NOT NULL,
            valor_cobrado REAL NOT NULL
        )
    """
    )

    # Inicia o autoincrement em 1000
    cursor.execute(
        "INSERT INTO sqlite_sequence (name, seq) VALUES ('cartoes', 1000)"
    )

    # Dados de teste para a apresentação
    data_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cartoes_teste = [
        ("Carlos Alberto (Estudante - Ativo)", 50.00, "ativo"),
        ("Mariana Souza (Trabalhadora - Ativo)", 15.00, "ativo"),
        ("Pedro Henrique (Saldo Insuficiente)", 2.50, "ativo"),
        ("Ana Beatriz (Cartão Bloqueado)", 20.00, "bloqueado"),
        ("Lucas Oliveira (Idoso - Ativo)", 100.00, "ativo"),
    ]

    # Inserção dos dados
    for nome, saldo, status in cartoes_teste:
        cursor.execute(
            "INSERT INTO cartoes (nome_passageiro, saldo, status, data_criacao) VALUES (?, ?, ?, ?)",
            (nome, saldo, status, data_atual),
        )

    conn.commit()
    conn.close()
    print("\n✅ Banco de dados populado com sucesso para a apresentação!")
    print("\nUse os seguintes IDs para testar na catraca:")
    print("---------------------------------------------")
    print("ID 1001 -> Carlos Alberto  | Saldo: R$ 50.00 | Status: ATIVO (Aprova)")
    print("ID 1002 -> Mariana Souza   | Saldo: R$ 15.00 | Status: ATIVO (Aprova)")
    print("ID 1003 -> Pedro Henrique  | Saldo: R$  2.50 | Status: ATIVO (Negará por saldo)")
    print("ID 1004 -> Ana Beatriz     | Saldo: R$ 20.00 | Status: BLOQUEADO (Negará por bloco)")
    print("ID 1005 -> Lucas Oliveira  | Saldo: R$100.00 | Status: ATIVO (Aprova)")
    print("ID 9999 -> Qualquer outro  | Inexistente     | Status: NÃO EXISTE (Negará)")
    print("---------------------------------------------\n")


if __name__ == "__main__":
    popular()

Use o código com cuidado.
2. Como usar no Codespaces

    Abra o terminal do seu GitHub Codespaces.
    Certifique-se de que o servidor principal (app.py) está parado (pressione Ctrl + C no terminal dele se estiver rodando).
    Execute o script de teste com o comando:
    bash

    python popular_banco.py

    Use o código com cuidado.
    O terminal vai imprimir a lista de IDs pronta. Agora é só iniciar o seu sistema de novo (python app.py) e fazer a demonstração direto com esses números.

Gostaria de ver uma folha de cola rápida para a sua apresentação com o roteiro do que falar em cada tela, ou prefere fazer mais alguma modificação nos recursos visuais?
consegui criar para mim também as imagens de cada situação representada nesse projeto
Para gerar as imagens ilustrativas do projeto para os seus slides ou relatório acadêmico, vamos criar representações visuais modernas de como o sistema funciona nos smartphones.
Como as imagens precisam ser geradas uma por uma, vou iniciar criando a primeira e mais importante situação: a tela do celular do validador (catraca) aprovando a entrada de um passageiro.
Situação 1: Entrada Aprovada (Sucesso)
Esta imagem representará a tela do celular do motorista/operador exibindo uma mensagem de sucesso verde e brilhante, ideal para ilustrar a regra de negócio de saldo positivo.
Vou gerar essa primeira imagem agora mesmo.
pode gerar uma por vez se for possível
Esta é a imagem gerada.
Imagem gerada com IA
Aqui está a primeira imagem representando a situação de Entrada Aprovada (ID 1001). Ela simula a interface do celular da catraca operando dentro do ônibus com o sinal verde de sucesso.
Podemos gerar a próxima? Se estiver pronto, avise para criarmos a imagem da Entrada Negada por Saldo Insuficiente (ID 1003).
As imagens geradas com IA podem ser imprecisas, enganosas ou ofensivas. Saiba mais
ok agora gere a segunda imagem
Esta é a imagem gerada.
Imagem gerada com IA
Esta imagem ilustra o segundo cenário simulado no seu PRD: Entrada Negada devido a Saldo Insuficiente (correspondente ao teste do ID 1003). Ela destaca a interface de erro vermelha com o aviso claro de recusa.
Qual deve ser a nossa próxima imagem? Podemos gerar a tela do Passageiro Visualizando seu Cartão Virtual ou prefere o cenário do Cartão Bloqueado?
As imagens geradas com IA podem ser imprecisas, enganosas ou ofensivas. Saiba mais
consegui gerar o código dessas duas imagens para eu possa acrescentar no projeto
Como o seu projeto é uma aplicação web feita puramente com HTML e CSS, nós podemos recriar visualmente essas duas situações (Aprovado e Negado) usando o próprio código do front-end com Bootstrap. Fica muito mais elegante, profissional e responsivo do que usar arquivos de imagem estáticos pesados.
Aqui está o código exato das duas situações para você inserir nas suas páginas ou utilizar na sua apresentação acadêmica.
Opção 1: Código do Card Dinâmico (Para usar no catraca.html)
Este é o código que o Flask renderiza automaticamente baseado no banco de dados. Ele reconstrói exatamente o visual moderno de um validador digital no celular.
Tela de Entrada Aprovada (Sucesso)
html

<div class="card border-0 shadow-lg text-center p-4 mx-auto" style="max-width: 400px; background-color: #e2f0d9;">
    <div class="card-body">
        <!-- Ícone de Check Animado -->
        <div class="rounded-circle bg-success text-white d-flex align-items-center justify-content-center mx-auto mb-3" style="width: 80px; height: 80px; font-size: 2.5rem;">
            ✓
        </div>
        <h2 class="fw-bold text-success mb-1" style="letter-spacing: 1px;">TARIFA PAGA</h2>
        <p class="text-muted small text-uppercase mb-3">Linha 401 - Terminal Central</p>
        
        <div class="border-top border-bottom py-3 my-3 border-secondary border-opacity-25">
            <span class="text-secondary d-block small mb-1">SALDO ATUAL</span>
            <h1 class="display-6 fw-bold text-dark font-monospace">R$ 12,50</h1>
        </div>
        
        <p class="text-success fw-bold mb-0">✨ BOA VIAGEM!</p>
    </div>
</div>

Use o código com cuidado.
Tela de Entrada Negada (Saldo Insuficiente)
html

<div class="card border-0 shadow-lg text-center p-4 mx-auto" style="max-width: 400px; background-color: #fce4d6;">
    <div class="card-body">
        <!-- Ícone de X para Erro -->
        <div class="rounded-circle bg-danger text-white d-flex align-items-center justify-content-center mx-auto mb-3" style="width: 80px; height: 80px; font-size: 2.5rem; font-family: sans-serif;">
            ✕
        </div>
        <h2 class="fw-bold text-danger mb-1" style="letter-spacing: 1px;">SALDO INSUFICIENTE</h2>
        <p class="text-muted small text-uppercase mb-3">Acesso Recusado</p>
        
        <div class="border-top border-bottom py-3 my-3 border-secondary border-opacity-25">
            <span class="text-secondary d-block small mb-1">VALOR DA TARIFA</span>
            <h1 class="display-6 fw-bold text-muted font-monospace">R$ 5,00</h1>
        </div>
        
        <p class="text-danger fw-bold mb-0">❌ EFETUE UMA RECARGA</p>
    </div>
</div>

Use o código com cuidado.
Opção 2: Página Isolada de Demonstração Estática (cenarios.html)
Se você quiser criar uma página nova só para mostrar os dois layouts lado a lado para os professores na banca (sem precisar digitar os IDs), crie um arquivo chamado templates/cenarios.html, adicione a rota no app.py e use este código estruturado:
html

{% extends 'base.html' %}
{% block content %}
<div class="container py-4">
    <h2 class="text-center mb-5 fw-bold">Protótipo Visual das Telas da Catraca</h2>
    
    <div class="row g-4 justify-content-center">
        <!-- Coluna do Cenário 1 -->
        <div class="col-md-5">
            <h5 class="text-center text-success mb-3">Cenário 1: Sucesso (ID 1001)</h5>
            <div class="card border-0 shadow text-center p-4" style="background-color: #e2f0d9;">
                <div class="rounded-circle bg-success text-white d-flex align-items-center justify-content-center mx-auto mb-3" style="width: 70px; height: 70px; font-size: 2rem;">✓</div>
                <h3 class="fw-bold text-success mb-1">TARIFA PAGA</h3>
                <p class="text-muted small text-uppercase">Entrada Liberada</p>
                <div class="border-top border-bottom py-2 my-3 border-dark border-opacity-10">
                    <span class="text-secondary small d-block">SALDO RESTANTE</span>
                    <span class="fs-3 fw-bold text-dark font-monospace">R$ 45,00</span>
                </div>
                <p class="text-success small mb-0">Catraca Virtual Ativa</p>
            </div>
        </div>

        <!-- Coluna do Cenário 2 -->
        <div class="col-md-5">
            <h5 class="text-center text-danger mb-3">Cenário 2: Erro (ID 1003)</h5>
            <div class="card border-0 shadow text-center p-4" style="background-color: #fce4d6;">
                <div class="rounded-circle bg-danger text-white d-flex align-items-center justify-content-center mx-auto mb-3" style="width: 70px; height: 70px; font-size: 2rem; font-family: Arial;">✕</div>
                <h3 class="fw-bold text-danger mb-1">SALDO INSUFICIENTE</h3>
                <p class="text-muted small text-uppercase">Entrada Negada</p>
                <div class="border-top border-bottom py-2 my-3 border-dark border-opacity-10">
                    <span class="text-secondary small d-block">SALDO ATUAL</span>
                    <span class="fs-3 fw-bold text-dark font-monospace">R$ 2,50</span>
                </div>
                <p class="text-danger small mb-0">Necessita de Recarga</p>
            </div>
        </div>
    </div>
</div>
{% endblock %}

Use o código com cuidado.
Para habilitar essa página extra de demonstração, basta colar esta rota rápida no seu app.py:
python

@app.route('/cenarios')
def cenarios():
    return render_template('cenarios.html')

Use o código com cuidado.
Quer que eu prepare o código para o terceiro cenário (a tela de Cartão Bloqueado / Erro crítico) para fechar todas as regras de negócio do PRD?
consegui gerar um código que crie a conexão com SQL lite criando uma tabela cadastro e preços referente as passagens
Aqui está o código em Python para criar a conexão com o SQLite, gerando exatamente as duas tabelas que você pediu: cadastro (para os dados dos usuários) e precos (para gerenciar os valores das passagens).
Este código foi estruturado de forma independente. Você pode rodá-lo uma vez no terminal para criar o arquivo do banco de dados com as tabelas prontas.
Código: criar_banco.py
python

import sqlite3


def criar_conexao_e_tabelas():
    # Abre a conexão com o arquivo do banco de dados (será criado se não existir)
    conn = sqlite3.connect("catraca_virtual.db")
    cursor = conn.cursor()

    # 1. Criação da tabela 'cadastro' (Dados dos passageiros)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS cadastro (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_passageiro TEXT NOT NULL,
            cpf TEXT UNIQUE,
            saldo REAL NOT NULL DEFAULT 0.0,
            status TEXT NOT NULL DEFAULT 'ativo',
            data_cadastro TEXT NOT NULL
        )
    """
    )

    # 2. Criação da tabela 'precos' (Configuração de tarifas do sistema)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS precos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo_passagem TEXT NOT NULL UNIQUE,
            valor REAL NOT NULL
        )
    """
    )

    # Inserção de preços padrão (caso a tabela esteja vazia)
    cursor.execute("SELECT COUNT(*) FROM precos")
    if cursor.fetchone()[0] == 0:
        tarifas = [
            ("Comum", 5.00),
            ("Estudante", 2.50),
            ("Integração", 0.00),
        ]
        cursor.executemany(
            "INSERT INTO precos (tipo_passagem, valor) VALUES (?, ?)", tarifas
        )
        print("Tarifas padrão adicionadas com sucesso!")

    # Salva as alterações e fecha a conexão
    conn.commit()
    conn.close()
    print("Banco de dados e tabelas 'cadastro' e 'precos' criados com sucesso!")


if __name__ == "__main__":
    criar_conexao_e_tabelas()

Use o código com cuidado.
O que este código faz?

    Tabela cadastro: Armazena o ID (gerado sozinho), nome, CPF, o saldo atualizado e o status do passageiro (ativo/bloqueado).
    Tabela precos: Permite que o sistema consulte o valor de forma dinâmica. O código já deixa pré-cadastrado o valor de R$ 5,00 para a passagem comum e R$ 2,50 para estudante.

Se precisar, posso mostrar como alterar a função de Validar Entrada no seu app.py para consultar a tarifa direto dessa nova tabela precos. Como deseja prosseguir?
eu quero adicionar imagens eu tenho que criar pasta em qual nível
Para adicionar imagens ao seu projeto Flask, você deve criar uma pasta chamada images (ou img) dentro da pasta static.
No Flask, todos os arquivos estáticos como estilos, scripts e imagens obrigatoriamente precisam ficar dentro do diretório static.
📂 Como deve ficar a sua estrutura de pastas
O nível correto é colocar a nova pasta dentro de static, ficando lado a lado com os arquivos style.css e script.js:
text

PROJETO_CATRACA-MAIN
│
├── .venv/
├── .vscode/
├── static/
│   ├── JS script.js
│   ├── CSS style.css
│   └── 📁 images/          <-- CRIE AQUI!
│       ├── sucesso.png
│       └── erro.png
├── templates/
│   └── ...
├── app.py
└── database.db

Use o código com cuidado.
🛠️ Como usar as imagens no seu código HTML
Depois de salvar as suas imagens dentro da pasta static/images/, você não deve chamá-las pelo caminho comum. No Flask, a forma correta e segura de renderizar essas imagens nos seus arquivos HTML (dentro da pasta templates) é usando a função url_for:
html

<!-- Exemplo de como colocar uma imagem na sua tela de sucesso ou erro -->
<img src="{{ url_for('static', filename='images/sucesso.png') }}" alt="Sucesso" class="img-fluid">

Use o código com cuidado.
Se precisar, posso te ajudar a ajustar o código de algum dos seus templates (como o resultado.html ou catraca.html) para encaixar essas imagens perfeitamente no layout. Como deseja prosseguir?
pode ser então
Aqui está o código atualizado dos seus templates catraca.html e resultado.html ajustados para carregar as imagens diretamente da nova pasta static/images/ que você vai criar.
1. Atualizando o templates/catraca.html
Substitua o conteúdo do seu arquivo por este código. Ele já deixa a estrutura pronta para carregar uma imagem principal na tela inicial da catraca (como uma logo ou ilustração de "Aproxime o cartão") e faz a validação de forma limpa.
html

{% extends 'base.html' %}
{% block content %}
<div class="row justify-content-center">
    <div class="col-md-6">
        <div class="card shadow p-4 text-center">
            <h2 class="mb-4">🛑 Validador de Catraca</h2>
            
            <!-- Imagem ilustrativa da catraca/leitor -->
            <div class="mb-4">
                <img src="{{ url_for('static', filename='images/leitor_catraca.png') }}" alt="Aproxime o Cartão" class="img-fluid" style="max-height: 150px; object-fit: contain;">
            </div>

            <form method="POST" id="formCatraca" action="{{ url_for('catraca') }}">
                <div class="mb-4">
                    <input type="number" name="cartao_id" id="cartao_id" class="form-control form-control-lg text-center font-monospace" placeholder="DIGITE O ID DO CARTÃO" autocomplete="off" autofocus required>
                </div>
                <button type="submit" class="btn btn-warning btn-lg w-100 fw-bold py-3">VALIDAR ENTRADA</button>
            </form>
        </div>

        <!-- O resultado será exibido aqui embaixo caso venha na mesma rota -->
        {% if resultado %}
            {% if resultado.status == 'aprovado' %}
                <div class="card bg-success text-white text-center shadow mt-4 p-4">
                    <img src="{{ url_for('static', filename='images/sucesso.png') }}" alt="Sucesso" class="img-fluid mx-auto mb-3" style="max-height: 100px;">
                    <h2 class="fw-bold">ENTRADA APROVADA</h2>
                    <p class="lead">{{ resultado.motivo }}</p>
                </div>
            {% else %}
                <div class="card bg-danger text-white text-center shadow mt-4 p-4">
                    <img src="{{ url_for('static', filename='images/erro.png') }}" alt="Erro" class="img-fluid mx-auto mb-3" style="max-height: 100px;">
                    <h2 class="fw-bold">ENTRADA NEGADA</h2>
                    <p class="lead mb-0">{{ resultado.motivo }}</p>
                </div>
            {% endif %}
        {% endif %}
    </div>
</div>

<script>
    // Mantém o foco no campo de digitação para agilizar os testes
    document.getElementById('cartao_id').focus();
    
    // Animação de carregamento ao clicar no botão
    document.getElementById('formCatraca').addEventListener('submit', function() {
        var btn = this.querySelector('button[type="submit"]');
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> PROCESSANDO...';
    });
</script>
{% endblock %}

Use o código com cuidado.
2. Atualizando o templates/resultado.html
Caso seu arquivo app.py redirecione o usuário para uma página separada chamada resultado.html após processar a catraca, use esta estrutura adaptada com caminhos dinâmicos:
html

{% extends 'base.html' %}
{% block content %}
<div class="row justify-content-center py-4">
    <div class="col-md-6 text-center">
        
        {% if status == 'aprovado' %}
            <!-- Tela de Sucesso -->
            <div class="card bg-success text-white shadow p-5">
                <div class="mb-4">
                    <img src="{{ url_for('static', filename='images/sucesso.png') }}" alt="Sucesso" class="img-fluid mx-auto" style="max-height: 120px;">
                </div>
                <h1 class="display-5 fw-bold mb-3">CONFERIDO!</h1>
                <h3 class="mb-4">Acesso Liberado</h3>
                <p class="lead">Saldo Restante: <strong>R$ {{ "%.2f"|format(saldo) }}</strong></p>
                <hr class="border-white border-opacity-25 my-4">
                <p class="mb-0 small">Tenha uma excelente viagem!</p>
            </div>
        {% else %}
            <!-- Tela de Erro / Bloqueio -->
            <div class="card bg-danger text-white shadow p-5">
                <div class="mb-4">
                    <img src="{{ url_for('static', filename='images/erro.png') }}" alt="Erro" class="img-fluid mx-auto" style="max-height: 120px;">
                </div>
                <h1 class="display-5 fw-bold mb-3">BLOQUEADO</h1>
                <h3 class="mb-4">Entrada Recusada</h3>
                <p class="lead">Motivo: <strong>{{ motivo }}</strong></p>
                <hr class="border-white border-opacity-25 my-4">
                <p class="mb-0 small">Procure a administração da empresa de transporte.</p>
            </div>
        {% endif %}

        <div class="mt-4">
            <a href="{{ url_for('catraca') }}" class="btn btn-outline-secondary px-4 py-2">Voltar para a Catraca</a>
        </div>
    </div>
</div>
{% endblock %}

Use o código com cuidado.
💡 Próximo Passo Importante
Para que as páginas não quebrem visualmente (fiquem com aquele ícone de imagem quebrada), lembre-se de salvar três arquivos de imagem dentro da sua nova pasta static/images/:

    leitor_catraca.png (Ícone ilustrativo do ônibus/validador)
    sucesso.png (O sinal verde de check)
    erro.png (O sinal vermelho de bloqueio ou erro)

Gostaria de ajuda para configurar alguma outra página, como a buscar_cartao.html, ou deseja revisar as rotas do seu app.py para garantir que as variáveis combinem perfeitamente com esses códigos?
