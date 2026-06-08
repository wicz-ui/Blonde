PRD - Sistema de Catraca Virtual para Ônibus.pdfVocê disse: fazer o DERO Diagrama de Entidade-Relacionamento (DER) para o Sistema de Catraca Virtual para Ônibus é composto por duas entidades principais: cartoes e passagens (p. 9). Elas se conectam em um relacionamento de 1 para muitos (1:N), onde um cartão pode registrar várias passagens (pp. 6, 9).Abaixo está a representação conceitual, os atributos detalhados e o script SQL para criação do banco de dados SQLite conforme o seu PRD (pp. 2, 9).1. Representação Textual do DERCARTOES (id, nome_passageiro, saldo, status, data_criacao) (p. 9)PASSAGENS (id, cartao_id, data_hora, status, motivo, valor_cobrado) (p. 9)Relacionamento:Um CARTÃO pode ter nenhuma ou muitas (0:N) PASSAGENS registradas (pp. 6, 9).Uma PASSAGEM pertence obrigatoriamente a um e apenas um (1:1) CARTÃO (p. 9).text+-----------------+                  +-----------------+

|     CARTOES     |                  |    PASSAGENS    |
+-----------------+                  +-----------------+

| PK | id         |1                N| PK | id         |
|    | nome_pass..|------------------| FK | cartao_id  |
|    | saldo      |                  |    | data_hora  |
|    | status     |                  |    | status     |
|    | data_cri.. |                  |    | motivo     |
+-----------------+                  |    | valor_cob..|
                                     +-----------------+
Use o código com cuidado.2. Dicionário de Dados (Atributos)Tabela: cartoes (p. 9)Armazena as informações das carteiras virtuais geradas pelos passageiros (pp. 2, 9).CampoTipoRestriçõesDescriçãoidINTEGERPK, AUTOINCREMENTIdentificador único do cartão (ex: 1001) (pp. 4, 9).nome_passageiroTEXTNOT NULLNome completo informado pelo usuário (pp. 4, 9).saldoREALNOT NULL, DEFAULT 0.0Saldo em dinheiro disponível para viagens (pp. 4, 9).statusTEXTNOT NULL, DEFAULT 'ativo'Estado do cartão ('ativo', 'bloqueado') (pp. 4-5, 9).data_criacaoTEXTNOT NULLData em que o cartão foi criado (YYYY-MM-DD) (pp. 4, 9).Tabela: passagens (p. 9)Registra o histórico de todas as tentativas de validação feitas na catraca (pp. 6, 9).CampoTipoRestriçõesDescriçãoidINTEGERPK, AUTOINCREMENTIdentificador único do registro de validação (pp. 9-10).cartao_idINTEGERFK (cartoes.id), NOT NULLID do cartão que tentou passar na catraca (p. 9).data_horaTEXTNOT NULLData e hora exata do evento (YYYY-MM-DD HH:MM:SS) (pp. 6, 9).statusTEXTNOT NULLResultado da validação ('aprovado' ou 'negado') (pp. 6, 9).motivoTEXTNOT NULLJustificativa do status (ex: 'Saldo insuficiente', 'Entrada liberada') (pp. 5-6, 9).valor_cobradoREALNOT NULL, DEFAULT 0.0Valor descontado caso a entrada tenha sido aprovada (R$ 5,00) (pp. 6-7, 9).3. Código SQL de Criação (SQLite)Você pode utilizar este código diretamente na função de inicialização do seu banco de dados no arquivo app.py (pp. 10, 14):sql-- Criação da tabela de cartões
CREATE TABLE IF NOT EXISTS cartoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_passageiro TEXT NOT NULL,
    saldo REAL NOT NULL DEFAULT 0.0,
    status TEXT NOT NULL DEFAULT 'ativo',
    data_criacao TEXT NOT NULL
);

-- Criação da tabela de histórico de passagens
CREATE TABLE IF NOT EXISTS passagens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cartao_id INTEGER NOT NULL,
    data_hora TEXT NOT NULL,
    status TEXT NOT NULL,
    motivo TEXT NOT NULL,
    valor_cobrado REAL NOT NULL DEFAULT 0.0,
    FOREIGN KEY (cartao_id) REFERENCES cartoes (id) ON DELETE CASCADE
);
Use o código com cuidado.
