# 🚌 Sistema de Catraca Virtual para Ônibus

Simulador web de uma catraca de transporte público. Permite emitir cartões
virtuais, consultar saldo e status, validar a entrada por ID e auditar tudo
em um histórico em tempo real — sem nenhuma catraca física. Projeto
acadêmico construído com Python (Flask) e SQLite.

## Tecnologias

- **Back-end:** Python 3 + Flask
- **Banco de dados:** SQLite3
- **Front-end:** HTML5 + CSS3 + JavaScript (sem frameworks externos)
- **Ambiente recomendado:** GitHub Codespaces (ou qualquer máquina com Python 3.10+)

## Estrutura do projeto

```
sistema-catraca/
│
├── app.py                 # Aplicação Flask: rotas e regras de negócio
├── popular_banco.py       # Recria o banco com 5 cartões de teste
├── testar_catraca.py      # Testes automatizados via requisições HTTP
├── requirements.txt       # Dependências Python
├── database.db            # Gerado automaticamente na primeira execução
│
├── static/
│   ├── css/style.css      # Identidade visual do projeto
│   └── js/script.js       # Sons da catraca, contagem regressiva, foco automático
│
└── templates/
    ├── base.html           # Estrutura comum (cabeçalho, rodapé, flash messages)
    ├── index.html          # Painel inicial com os 4 acessos do sistema
    ├── criar_cartao.html   # Emissão de cartão virtual
    ├── buscar_cartao.html  # Consulta de saldo/status por ID
    ├── catraca.html        # Validador de entrada (kiosk)
    ├── resultado.html      # Tela de aprovação/negação com animação da catraca
    └── historico.html      # Tabela de tentativas, com auto-atualização
```

## Como executar

### 1. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 2. (Opcional) Popular o banco com dados de teste

```bash
python popular_banco.py
```

Isso recria o banco do zero com os cartões abaixo, prontos para a demonstração:

| ID   | Passageiro      | Saldo     | Status    | Resultado esperado          |
|------|------------------|-----------|-----------|------------------------------|
| 1001 | Carlos Alberto   | R$ 50,00  | ativo     | Aprovado                     |
| 1002 | Mariana Souza    | R$ 15,00  | ativo     | Aprovado                     |
| 1003 | Pedro Henrique   | R$ 2,50   | ativo     | Negado — saldo insuficiente  |
| 1004 | Ana Beatriz      | R$ 20,00  | bloqueado | Negado — cartão bloqueado    |
| 1005 | Lucas Oliveira   | R$ 100,00 | ativo     | Aprovado                     |
| 9999 | —                | —         | —         | Negado — cartão inexistente  |

Se você pular esta etapa, o sistema cria o banco vazio normalmente e você
pode cadastrar cartões pela própria interface em **Criar cartão**.

### 3. Rodar o servidor

```bash
python app.py
```

O servidor sobe em `http://0.0.0.0:5000`.

### 4. Acessar pelo celular (GitHub Codespaces)

1. Na aba **Ports** do Codespaces, localize a porta **5000**.
2. Clique com o botão direito → **Port Visibility** → **Public**.
3. Abra o link gerado pelo Codespaces no navegador de cada celular.
4. Um celular acessa **Criar cartão** / **Consultar cartão** (papel do passageiro).
5. O outro celular acessa **Catraca virtual** (papel do operador).

### 5. (Opcional) Rodar os testes automatizados

Com o servidor já rodando, em outro terminal:

```bash
python testar_catraca.py
```

## Regras de negócio implementadas

1. **Tarifa fixa:** R$ 5,00 por passagem, definida em `app.py` (`VALOR_TARIFARIO`).
2. **Cartão inexistente:** ID que não está no banco → entrada negada e registrada.
3. **Cartão bloqueado:** status diferente de `ativo` → entrada negada, mesmo com saldo.
4. **Saldo insuficiente:** saldo menor que a tarifa → entrada negada.
5. **Débito automático:** entrada aprovada desconta a tarifa do saldo do cartão.
6. **Registro obrigatório:** toda tentativa (aprovada ou negada) é salva na tabela `passagens`.

## Banco de dados

**Tabela `cartoes`**

| Campo            | Tipo    | Descrição                          |
|------------------|---------|--------------------------------------|
| id               | INTEGER | Identificador do cartão (PK)        |
| nome_passageiro  | TEXT    | Nome do passageiro                  |
| saldo            | REAL    | Saldo disponível                    |
| status           | TEXT    | `ativo` ou `bloqueado`              |
| data_criacao     | TEXT    | Data/hora de emissão do cartão      |

**Tabela `passagens`**

| Campo          | Tipo    | Descrição                                |
|----------------|---------|--------------------------------------------|
| id             | INTEGER | Identificador do registro (PK)             |
| cartao_id      | INTEGER | ID do cartão utilizado na tentativa        |
| data_hora      | TEXT    | Data/hora da tentativa                     |
| status         | TEXT    | `aprovado` ou `negado`                     |
| motivo         | TEXT    | Motivo da aprovação/negação                |
| valor_cobrado  | REAL    | Valor descontado (0 se a entrada foi negada)|

## Fora do escopo (por ser um protótipo acadêmico)

- Catraca física ou leitor RFID real.
- Pagamento real / integração bancária.
- Autenticação avançada (login de operador, tokens dinâmicos).
- Múltiplas frotas, linhas ou tarifas simultâneas.

Essas limitações são intencionais e fazem parte da discussão sobre evolução
do projeto — veja `APRESENTACAO.md` para um roteiro de como justificá-las
durante a apresentação.
