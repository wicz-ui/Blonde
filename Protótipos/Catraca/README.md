# Catraca Virtual 🚌

Um sistema completo de catraca virtual para controle de acesso em transporte público. Permite gerenciamento de cartões, recargas de saldo, validação de entradas em estações e planejamento de rotas de viagem.

## 📋 Índice

- [Descrição](#descrição)
- [Funcionalidades](#funcionalidades)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Como Usar](#como-usar)
- [Arquitetura](#arquitetura)
- [Estrutura de Pastas](#estrutura-de-pastas)
- [Banco de Dados](#banco-de-dados)
- [Rotas e Endpoints](#rotas-e-endpoints)
- [Configurações](#configurações)
- [Sistema de Autenticação](#sistema-de-autenticação)
- [Exemplos de Uso](#exemplos-de-uso)

## 📝 Descrição

A **Catraca Virtual** é uma aplicação web desenvolvida em Flask que simula um sistema completo de catraca para transporte público. O sistema gerencia:

- **Cartões de Passageiros**: Criação, bloqueio/ativação e visualização
- **Saldo de Crédito**: Recargas e deduções de valores
- **Validação de Entradas**: Verificação de saldo antes de liberar a passagem
- **Histórico de Transações**: Registro de todas as entradas/saídas
- **Planejamento de Rotas**: Passageiros podem planejar suas viagens
- **Estações**: Gerenciamento de estações e regiões
- **Dispositivos**: Criação de links de acesso para diferentes tipos de dispositivos

## ✨ Funcionalidades

### Para Passageiros 👤
- Visualizar cartão e saldo disponível
- Fazer recargas de crédito
- Ver histórico de recargas
- Planejar rotas de viagem
- Acompanhar viagem planejada
- Baixar cartão em PDF
- Acessar via link privado (token do passageiro)

### Para Catraca 🚪
- Validar entrada de passageiros
- Verificar saldo e status do cartão
- Registrar histórico de passagens
- Validar rotas planejadas
- Suportar escanear código QR ou digitar token

### Para Administrador 👨‍💼
- Criar cartões para passageiros
- Gerenciar estações e regiões
- Configurar parâmetros do sistema
- Gerenciar dispositivos de acesso
- Visualizar histórico completo
- Visualizar histórico de recargas
- Alterar status de cartões
- Definir valores de passagem e recargas

## 📦 Requisitos

- Python 3.10+
- Flask 3.0+
- ReportLab 4.0+ (para geração de PDF)
- SQLite3 (incluído no Python)

## 🚀 Instalação

### 1. Clonar o Repositório
```bash
git clone <url-do-repositorio>
cd Catraca
```

### 2. Criar Ambiente Virtual
```bash
python -m venv venv
```

### 3. Ativar Ambiente Virtual

**Linux/Mac:**
```bash
source venv/bin/activate
```

**Windows:**
```bash
venv\Scripts\activate
```

### 4. Instalar Dependências
```bash
pip install -r requirements.txt
```

## 💻 Como Usar

### Iniciar a Aplicação
```bash
python app.py
```

A aplicação estará disponível em `http://localhost:5000`

### Variáveis de Ambiente (Opcionais)

Você pode configurar variáveis de ambiente para personalizar a aplicação:

```bash
export SECRET_KEY="sua-chave-secreta"
export ADMIN_TOKEN="seu-token-admin"
export CATRACA_TOKEN="seu-token-catraca"
export USUARIO_TOKEN="seu-token-usuario"
export PORT="5000"
export FLASK_DEBUG="0"
```

**Padrões se não configurado:**
- `ADMIN_TOKEN`: "admin-demo-2026"
- `CATRACA_TOKEN`: "catraca-demo-2026"
- `USUARIO_TOKEN`: "usuario-demo-2026"
- `SECRET_KEY`: "catraca-demo-secret"
- `PORT`: 5000

### Primeiro Acesso

1. Acesse `http://localhost:5000/login`
2. Use um dos dispositivos pré-configurados:
   - **Admin**: usuário `admin` | senha `admin-demo-2026`
   - **Catraca**: usuário `catraca` | senha `catraca-demo-2026`

## 🏗️ Arquitetura

### Camadas da Aplicação

```
┌─────────────────────────────────────┐
│     Frontend (Templates HTML)       │
│   - Formulários e Interfaces        │
│   - JavaScript para Interatividade  │
└────────────────┬────────────────────┘
                 │
┌─────────────────▼────────────────────┐
│      Flask Application (app.py)      │
│   - Rotas e Endpoints               │
│   - Lógica de Negócio               │
│   - Autenticação                    │
└────────────────┬────────────────────┘
                 │
┌─────────────────▼────────────────────┐
│     SQLite Database (database.db)    │
│   - Tabelas de Dados                │
│   - Transações                      │
└─────────────────────────────────────┘
```

### Fluxo de Autenticação

```
┌─────────────┐
│   Login     │
└──────┬──────┘
       │
       ▼
┌──────────────────────────────────┐
│ Validar Credenciais              │
│ (usuário + senha = token_acesso) │
└──────────────┬───────────────────┘
               │
       ┌───────┴───────┐
       │               │
       ▼               ▼
┌────────────┐  ┌─────────────┐
│ Dispositivo│  │   Usuário   │
│   Token    │  │   Token     │
└────────────┘  └─────────────┘
```

### Fluxo de Validação de Entrada

```
┌──────────────────────────────┐
│  Passageiro Passa Cartão     │
│  (Código Público ou Token)   │
└──────────────┬───────────────┘
               │
               ▼
┌──────────────────────────────┐
│ Buscar Cartão no BD          │
└──────────┬───────────────────┘
           │
    ┌──────┴──────┐
    │             │
    ▼ Não Existe  ▼ Existe
 ┌────────┐  ┌──────────────────────┐
 │ Negado │  │ Verificar Status     │
 └────────┘  │ (Bloqueado/Ativo)    │
             └──────────┬───────────┘
                        │
                    ┌───┴───┐
                    │       │
             Bloqueado    Ativo
                    │       │
                 ┌──┴──┐    │
                 │     │    ▼
              ┌─────────────────────┐
              │ Verificar Saldo     │
              │ (≥ Valor Passagem)  │
              └──────────┬──────────┘
                         │
                    ┌────┴─────┐
                    │          │
            Insuficiente    Suficiente
                    │          │
                  ┌─┴─┐        ▼
                  │   │ ┌──────────────────────┐
               ┌──┴──┐│ │ Validar Rota (se    │
               │Negado││ │ planejada)          │
               └──────┘│ └──────────┬──────────┘
                       │           │
                       │      ┌────┴────┐
                       │      │         │
                       │  Fora de   Compatível
                       │  Rota      com Rota
                       │      │         │
                       │   ┌──┴──┐      ▼
                       │   │     │ ┌──────────────────┐
                       │  ┌┴─────┐│ Debitar Saldo    │
                       │  │Negado││ e Registrar      │
                       │  └──────┘│ ┌────────────────┐
                       │          │ │ Aprovado       │
                       │          │ └────────────────┘
                       │          └────────┬─────────┘
                       │                   │
                       └───────────┬───────┘
                                   ▼
                          ┌──────────────────┐
                          │ Registrar Entrada│
                          │ no Histórico     │
                          └──────────────────┘
```

## 📁 Estrutura de Pastas

```
Catraca/
├── README.md                          # Documentação do projeto
├── requirements.txt                   # Dependências Python
├── app.py                             # Aplicação Flask principal
├── database.db                        # Banco de dados SQLite (gerado na primeira execução)
│
├── static/                            # Arquivos estáticos
│   ├── html5-qrcode.min.js           # Biblioteca para ler código QR
│   ├── script.js                     # JavaScript do frontend
│   └── style.css                     # Estilos CSS
│
└── templates/                         # Templates HTML
    ├── base.html                     # Template base (herança)
    ├── login.html                    # Página de login
    ├── acesso_negado.html            # Página de acesso negado
    ├── index.html                    # Página inicial (admin)
    │
    ├── catraca.html                  # Interface da catraca
    ├── meu_cartao.html               # Cartão do passageiro
    ├── visualizar_cartao.html        # Visualização de cartão
    ├── criar_cartao.html             # Formulário criar cartão
    ├── recarregar_cartao.html        # Recarga de saldo
    ├── usuario_recargas.html         # Histórico de recargas
    ├── minha_viagem.html             # Viagem planejada
    ├── planejar_viagem.html          # Planejamento de viagem
    ├── resultado.html                # Página de resultado
    │
    ├── admin_cartoes.html            # Gerenciamento de cartões (admin)
    ├── admin_estacoes.html           # Gerenciamento de estações (admin)
    ├── admin_recargas.html           # Histórico de recargas (admin)
    ├── admin_configuracoes.html      # Configurações do sistema (admin)
    ├── dispositivos.html             # Gerenciamento de dispositivos (admin)
    └── historico.html                # Histórico de transações (admin)
```

## 🗄️ Banco de Dados

### Esquema das Tabelas

#### `usuarios`
Registro de passageiros do sistema.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | INTEGER PRIMARY KEY | ID único do usuário |
| nome | TEXT NOT NULL | Nome do passageiro |
| token_usuario | TEXT NOT NULL UNIQUE | Token de acesso privado |
| criado_em | TEXT NOT NULL | Data/hora de criação |
| ativo | INTEGER (0/1) | Status do usuário |

#### `cartoes`
Cartões dos passageiros com saldo.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | INTEGER PRIMARY KEY | ID do cartão (código principal) |
| usuario_id | INTEGER FK | Usuário proprietário |
| codigo_publico | TEXT | Código público (QR code) |
| nome_passageiro | TEXT NOT NULL | Nome do passageiro |
| saldo | REAL NOT NULL | Saldo em crédito |
| status | TEXT | 'ativo' ou 'bloqueado' |
| data_criacao | TEXT NOT NULL | Data de criação |
| criado_em | TEXT | Timestamp de criação |
| atualizado_em | TEXT | Timestamp da última atualização |

#### `estacoes`
Estações/paradas do transporte público.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | INTEGER PRIMARY KEY | ID da estação |
| nome | TEXT NOT NULL UNIQUE | Nome da estação |
| regiao | TEXT | Região da estação |
| ativa | INTEGER (0/1) | Status da estação |

#### `passagens`
Histórico de entradas validadas.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | INTEGER PRIMARY KEY | ID da passagem |
| cartao_id | INTEGER FK | Cartão utilizado |
| cartao_digitado | TEXT | Código digitado/escaneado |
| origem_id | INTEGER FK | ID da estação de origem |
| destino_id | INTEGER FK | ID da estação de destino |
| data_hora | TEXT NOT NULL | Data/hora da validação |
| status | TEXT | 'aprovado' ou 'negado' |
| motivo | TEXT NOT NULL | Motivo do resultado |
| valor_cobrado | REAL | Valor debitado |
| expira_em | TEXT | Data de expiração do registro |

#### `recargas`
Histórico de recargas de saldo.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | INTEGER PRIMARY KEY | ID da recarga |
| usuario_id | INTEGER FK | Usuário que fez recarga |
| cartao_id | INTEGER FK | Cartão recarregado |
| valor | REAL NOT NULL | Valor da recarga |
| saldo_anterior | REAL NOT NULL | Saldo antes da recarga |
| saldo_novo | REAL NOT NULL | Saldo após recarga |
| data_hora | TEXT NOT NULL | Data/hora da recarga |
| status | TEXT | 'confirmada' (padrão) |
| expira_em | TEXT | Data de expiração do registro |

#### `configuracoes`
Parâmetros de configuração do sistema.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | INTEGER PRIMARY KEY | ID |
| chave | TEXT NOT NULL UNIQUE | Chave da configuração |
| valor | TEXT NOT NULL | Valor da configuração |

#### `dispositivos`
Dispositivos (catraca, admin, usuário) com tokens de acesso.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | INTEGER PRIMARY KEY | ID do dispositivo |
| nome_dispositivo | TEXT | Nome do dispositivo |
| tipo | TEXT | 'admin', 'catraca' ou 'usuario' |
| token_acesso | TEXT UNIQUE | Token para acesso |
| ativo | INTEGER (0/1) | Status do dispositivo |
| cartao_id | INTEGER FK | Cartão vinculado (tipo usuario) |
| usuario_id | INTEGER FK | Usuário vinculado |
| estacao_id | INTEGER FK | Estação vinculada (tipo catraca) |

#### `rotas_viagem`
Rotas planejadas pelos passageiros.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | INTEGER PRIMARY KEY | ID da rota |
| usuario_id | INTEGER FK | Passageiro |
| cartao_id | INTEGER FK | Cartão da viagem |
| criado_em | TEXT NOT NULL | Data/hora de criação |
| status | TEXT | 'planejada', 'cancelada', 'concluida' |

#### `trechos_viagem`
Trechos/etapas de uma rota de viagem.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| id | INTEGER PRIMARY KEY | ID do trecho |
| rota_id | INTEGER FK | Rota associada |
| origem_id | INTEGER FK | Estação de origem |
| destino_id | INTEGER FK | Estação de destino |
| ordem | INTEGER | Ordem do trecho na rota |
| valor | REAL | Valor da passagem |

## 🔗 Rotas e Endpoints

### Autenticação
| Método | Rota | Descrição |
|--------|------|-----------|
| GET/POST | `/login` | Página de login |
| POST | `/login` | Processar login |

### Passageiro (Requer tipo `usuario`)
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/usuario/meu-cartao` | Ver cartão e saldo |
| GET | `/usuario/cartao/pdf` | Baixar cartão em PDF |
| GET/POST | `/usuario/recarregar-cartao` | Recarregar saldo |
| POST | `/usuario/recarregar-cartao/confirmar` | Confirmar recarga |
| GET | `/usuario/recargas` | Histórico de recargas |
| GET/POST | `/usuario/planejar-viagem` | Planejar rota de viagem |
| GET | `/usuario/minha-viagem` | Ver viagem planejada |
| POST | `/usuario/minha-viagem/cancelar` | Cancelar viagem |

### Catraca (Requer tipo `catraca`)
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/catraca` | Interface da catraca |
| POST | `/validar-catraca` | Validar entrada (POST) |
| POST | `/catraca/validar` | Validar entrada (POST) |

### Administrador (Requer tipo `admin`)
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/admin` | Dashboard administrativo |
| GET/POST | `/criar-cartao` | Criar novo cartão |
| GET/POST | `/admin/estacoes` | Gerenciar estações |
| POST | `/admin/estacoes/<id>/alternar` | Ativar/desativar estação |
| GET/POST | `/admin/configuracoes` | Configurações do sistema |
| GET | `/admin/historico` | Histórico de transações |
| GET | `/admin/recargas` | Histórico de recargas |
| GET | `/admin/cartoes` | Gerenciar cartões |
| POST | `/admin/cartoes/<id>/status` | Alterar status do cartão |
| GET/POST | `/admin/dispositivos` | Gerenciar dispositivos |
| POST | `/dispositivos/<id>/vincular` | Vincular dispositivo a cartão/estação |
| POST | `/dispositivos/<id>/alternar` | Ativar/desativar dispositivo |

### Utilitários
| Método | Rota | Descrição |
|--------|------|-----------|
| GET | `/` | Página inicial (redirect para login) |
| GET | `/meu/<token_usuario>` | Acesso rápido do passageiro |
| GET | `/health` | Health check |

## ⚙️ Configurações

As configurações do sistema podem ser alteradas pelo administrador em `/admin/configuracoes`. As chaves de configuração são:

| Chave | Padrão | Descrição |
|-------|--------|-----------|
| `historico_retencao_horas` | 24 | Horas para manter histórico de passagens |
| `historico_recargas_retencao_dias` | 30 | Dias para manter histórico de recargas |
| `valor_passagem_padrao` | 5.00 | Valor padrão da passagem |
| `valor_minimo_recarga` | 5.00 | Valor mínimo para recarga |
| `valor_maximo_recarga` | 200.00 | Valor máximo para recarga |
| `permitir_download_pdf` | true | Permitir download do cartão em PDF |
| `exibir_saldo_no_pdf` | true | Exibir saldo no cartão PDF |

## 🔐 Sistema de Autenticação

### Tipos de Tokens

#### 1. Token de Dispositivo (`token_acesso`)
- Usado para acessar recursos do dispositivo
- Gerado aleatoriamente ao criar um dispositivo
- Padrão: 24 caracteres (URL-safe)
- Exemplos de dispositivos:
  - **Admin**: Computador administrativo
  - **Catraca**: Catraca virtual em uma estação
  - **Usuário**: Celular do passageiro

#### 2. Token de Usuário (`token_usuario`)
- Usado para identificar um passageiro
- Gerado ao criar um cartão
- Padrão: 11 caracteres (XXXXX-XXXXX-XXXXX)
- Permite acesso ao painel do passageiro

### Fluxo de Autenticação

1. **Login com Credenciais** (na primeira vez)
   ```
   Usuário: admin | Senha: admin-demo-2026
   ```
   
2. **Obter Token de Acesso**
   ```
   token_acesso = "abcd1234efgh5678ijkl"
   ```

3. **Usar Token em Requisições**
   ```
   http://localhost:5000/admin?token=abcd1234efgh5678ijkl
   ```

4. **Token é Validado** em cada requisição protegida
   ```python
   acesso = buscar_acesso(token)
   if acesso is None:
       return "Acesso não autorizado"
   ```

### Protegendo Rotas

Rotas protegidas usam o decorador `@acesso_requerido`:

```python
@app.get("/usuario/meu-cartao")
@acesso_requerido("usuario")  # Apenas tipo "usuario"
def usuario_meu_cartao():
    # Código da rota
    pass

@app.get("/admin/historico")
@acesso_requerido("admin")    # Apenas tipo "admin"
def historico():
    # Código da rota
    pass
```

## 📊 Exemplos de Uso

### 1. Criar um Cartão (Admin)

1. Acesse `http://localhost:5000/admin?token=<admin-token>`
2. Vá para "Criar Cartão"
3. Preencha os dados:
   - Nome do Passageiro: "João Silva"
   - Saldo Inicial: "50,00"
   - Status: Ativo
4. Clique em "Criar Cartão"
5. Um token privado será gerado para o passageiro

### 2. Passageiro Acessa Seu Cartão

1. Clique no link privado fornecido
2. Veja o cartão com código público
3. Baixe o PDF se configurado
4. Visualize saldo e histórico

### 3. Passageiro Faz Recarga

1. No painel do passageiro, vá para "Recarregar Cartão"
2. Escolha um valor predefinido ou digite um valor personalizado:
   - R$ 10.00, R$ 20.00, R$ 50.00, R$ 100.00 (padrão)
   - Ou outro valor entre o mínimo e máximo configurado
3. Confirme a recarga
4. Saldo é atualizado imediatamente

### 4. Passageiro Planeja uma Viagem

1. No painel do passageiro, vá para "Planejar Viagem"
2. Selecione origem e destino
3. Clique em "Adicionar Trecho"
4. Repita para adicionar múltiplos trechos
5. Use os botões para reorganizar (Subir/Descer/Remover)
6. Clique em "Confirmar Viagem"
7. A rota é salva como "planejada"

### 5. Validar Entrada na Catraca

**Opção A: Escanear Código QR**
1. Acesse catraca: `http://localhost:5000/catraca?token=<catraca-token>`
2. Clique em "Escanear QR"
3. Aponte câmera para o código QR do cartão
4. Sistema valida automaticamente

**Opção B: Digitar Código Público**
1. Digite o código público do cartão
2. Clique em "Validar"
3. Sistema verifica saldo e status
4. Resultado: Aprovado ou Negado

### 6. Administrador Gerencia Estações

1. Acesse admin: `http://localhost:5000/admin?token=<admin-token>`
2. Vá para "Estações"
3. Pode:
   - Adicionar nova estação
   - Ativar/desativar estações existentes
   - Definir região de cada estação

### 7. Administrador Gerencia Dispositivos

1. Acesse admin e vá para "Dispositivos"
2. Crie novo dispositivo:
   - Nome: "Catraca Terminal Central"
   - Tipo: Catraca
   - Estação: Terminal Central
3. Dispositivo recebe um token de acesso automático
4. Admin pode compartilhar link com instalação física
5. Link ativa o dispositivo com esse token

## 🛠️ Troubleshooting

### Problema: "Acesso não autorizado"
**Causa:** Token inválido ou ausente
**Solução:** Verifique se o token está correto na URL

### Problema: "Saldo insuficiente"
**Causa:** Cartão não tem crédito suficiente
**Solução:** Passageiro deve fazer recarga em "Recarregar Cartão"

### Problema: "Estação fora da rota planejada"
**Causa:** Catraca em estação diferente da origem do trecho
**Solução:** Passageiro deve estar na estação correta ou planejar rota diferente

### Problema: Dados aparecem vazios
**Causa:** Histórico pode ter expirado (limpeza automática)
**Solução:** Aguarde recarga manual ou limite em configurações

## 📅 Limpeza de Dados

O sistema remove automaticamente registros expirados:

- **Histórico de Passagens**: Removido após 24 horas (configurável)
- **Histórico de Recargas**: Removido após 30 dias (configurável)
- **Limpeza automática** ocorre quando:
  - Admin acessa dashboard
  - Usuário consulta histórico
  - Sistema processa recargas

## 🔄 Fluxo de Dados

### Criação de Cartão
```
Admin cria cartão
    ↓
Novo usuário criado com token_usuario
    ↓
Novo cartão criado com código_publico
    ↓
Novo dispositivo criado tipo "usuario"
    ↓
Passageiro recebe link privado
```

### Validação de Entrada
```
Cartão passado na catraca
    ↓
Código extraído (QR ou digit)
    ↓
Cartão validado no BD
    ↓
Status, saldo e rota verificados
    ↓
Saldo debitado (se aprovado)
    ↓
Transação registrada no histórico
```

## 📝 Notas Técnicas

- **Fuso horário:** America/Sao_Paulo (UTC-3)
- **Banco de dados:** SQLite com journal mode WAL
- **Transações:** ACID com BEGIN IMMEDIATE e COMMIT/ROLLBACK
- **Decimais:** Arredondamento ROUND_HALF_UP para valores monetários
- **Session Key:** Pode ser alterada via variável de ambiente SECRET_KEY
- **Tipagem:** Tipo "admin", "catraca", "usuario"
- **Status:** Cartão "ativo" ou "bloqueado"

## 📞 Suporte

Para reportar bugs ou sugerir melhorias, contate o administrador do projeto.

## 📄 Licença

Este projeto é fornecido como é, para uso educacional e demonstrativo.

---

**Versão:** 1.0  
**Data:** Junho 2026  
**Última atualização:** 2026-06-18
