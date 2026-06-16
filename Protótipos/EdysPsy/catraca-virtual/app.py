import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "chave_secreta_para_demonstracao"
DATABASE = "database.db"
VALOR_PASSAGEM = 5.00  # Valor sugerido no PRD

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa o banco de dados criando as tabelas necessárias se não existirem."""
    if not os.path.exists(DATABASE):
        conn = get_db_connection()
        # Tabela Cartões
        conn.execute('''
            CREATE TABLE IF NOT EXISTS cartoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_passageiro TEXT NOT NULL,
                saldo REAL NOT NULL,
                status TEXT NOT NULL,
                data_criacao TEXT NOT NULL
            )
        ''')
        # Alterar o valor inicial do AUTOINCREMENT para 1001 conforme o exemplo do PRD
        conn.execute("INSERT INTO sqlite_sequence (name, seq) VALUES ('cartoes', 1000)")
        
        # Tabela Passagens (Histórico)
        conn.execute('''
            CREATE TABLE IF NOT EXISTS passagens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cartao_id INTEGER,
                data_hora TEXT NOT NULL,
                status TEXT NOT NULL,
                motivo TEXT NOT NULL,
                valor_cobrado REAL NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

# Rota: Página Inicial
@app.route('/')
def index():
    return render_template('index.html')

# Rota: Tela de Criação de Cartão
@app.route('/criar-cartao', methods=['GET', 'POST'])
def criar_cartao():
    if request.method == 'POST':
        nome = request.form.get('nome_passageiro')
        saldo_inicial = float(request.form.get('saldo_inicial', 0))
        status = "ativo"
        data_atual = datetime.now().strftime("%Y-%m-%d")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO cartoes (nome_passageiro, saldo, status, data_criacao)
            VALUES (?, ?, ?, ?)
        ''', (nome, saldo_inicial, status, data_atual))
        cartao_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return render_template('resultado.html', acao='criar', cartao={
            'id': cartao_id, 'nome_passageiro': nome, 'saldo': saldo_inicial, 'status': status
        })
        
    return render_template('criar_cartao.html')

# Rota: Tela de Consulta de Cartão
@app.route('/cartao', methods=['GET', 'POST'])
def visualizar_cartao():
    cartao = None
    buscou = False
    if request.method == 'POST':
        cartao_id = request.form.get('cartao_id')
        conn = get_db_connection()
        cartao = conn.execute('SELECT * FROM cartoes WHERE id = ?', (cartao_id,)).fetchone()
        conn.close()
        buscou = True
        
    return render_template('visualizar_cartao.html', cartao=cartao, buscou=buscou)

# Rota: Tela da Catraca Virtual
@app.route('/catraca')
def catraca():
    return render_template('catraca.html')

# Rota: Validação do ID Digitado
@app.route('/validar-catraca', methods=['POST'])
def validar_catraca():
    cartao_id = request.form.get('cartao_id')
    data_hora_atual = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    conn = get_db_connection()
    cartao = conn.execute('SELECT * FROM cartoes WHERE id = ?', (cartao_id,)).fetchone()
    
    status_validacao = "negado"
    motivo = ""
    valor_descontado = 0.0
    
    # 1. Validação de existência
    if not cartao:
        motivo = "Entrada negada. Cartão não encontrado."
    # 2. Validação de status ativo
    elif cartao['status'] != 'ativo':
        motivo = "Entrada negada. Cartão bloqueado."
    # 3. Validação de saldo suficiente
    elif cartao['saldo'] < VALOR_PASSAGEM:
        motivo = "Entrada negada. Saldo insuficiente."
    # 4. Aprovação e Desconto
    else:
        status_validacao = "aprovado"
        motivo = "Entrada aprovada. Boa viagem!"
        valor_descontado = VALOR_PASSAGEM
        novo_saldo = cartao['saldo'] - VALOR_PASSAGEM
        conn.execute('UPDATE cartoes SET saldo = ? WHERE id = ?', (novo_saldo, cartao_id))
    
    # Registrar obrigatoriamente no histórico
    conn.execute('''
        INSERT INTO passagens (cartao_id, data_hora, status, motivo, valor_cobrado)
        VALUES (?, ?, ?, ?, ?)
    ''', (cartao_id if cartao else None, data_hora_atual, status_validacao, motivo, valor_descontado))
    
    conn.commit()
    conn.close()
    
    return render_template('resultado.html', acao='catraca', status=status_validacao, motivo=motivo)

# Rota: Histórico de Passagens
@app.route('/historico')
def historico():
    conn = get_db_connection()
    # Busca unindo as tabelas para exibir também o nome do passageiro (se o cartão existir)
    query = '''
        SELECT p.*, c.nome_passageiro 
        FROM passagens p 
        LEFT JOIN cartoes c ON p.cartao_id = c.id
        ORDER BY p.id DESC
    '''
    passagens = conn.execute(query).fetchall()
    conn.close()
    return render_template('historico.html', passagens=passagens)

if __name__ == '__main__':
    init_db()
    # Rodar em modo debug e acessível externamente na rede local/Codespaces
    app.run(host='0.0.0.0', port=5000, debug=True)
