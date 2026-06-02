# PRD — Sistema de Catraca Virtual para Ônibus

## 1. Nome do projeto

**Sistema de Catraca Virtual para Ônibus**

---

## 2. Objetivo do projeto

Desenvolver um sistema web que simule o funcionamento de uma catraca de ônibus, permitindo que passageiros criem cartões virtuais e que uma tela de catraca valide a entrada desses passageiros por meio do ID do cartão.

O sistema será usado apenas para demonstração acadêmica, sem catraca física. A catraca será representada por uma tela web acessada por celular.

---

## 3. Descrição geral

O projeto consiste em um sistema principal de uma empresa de ônibus. Esse sistema será desenvolvido com **Python, HTML, CSS e SQLite**.

A aplicação ficará rodando em um computador da escola, preferencialmente usando **GitHub Codespaces**, com uma porta pública aberta para que outros dispositivos possam acessar o sistema pelo navegador.

Durante a demonstração, dois celulares poderão acessar o sistema:

1. **Celular do passageiro**
   Usado para criar ou visualizar um cartão virtual.

2. **Celular da catraca virtual**
   Usado para digitar o ID do cartão e validar a entrada no ônibus.

A validação será feita consultando o banco de dados SQLite. Se o ID do cartão existir e estiver válido, o sistema aprova a entrada. Caso contrário, a entrada será negada.

---

## 4. Problema que o sistema resolve

Em sistemas reais de transporte público, os passageiros utilizam cartões para liberar a entrada no ônibus por meio de catracas. O objetivo deste projeto é simular esse processo de forma simples, demonstrando conceitos de:

* Cadastro de usuários/cartões;
* Banco de dados;
* Validação de informações;
* Registro de histórico;
* Acesso ao sistema por múltiplos dispositivos;
* Comunicação entre telas usando uma aplicação web.

---

## 5. Público-alvo

O sistema será utilizado por três tipos de usuários simulados:

### 5.1 Passageiro

Pessoa que deseja criar ou visualizar seu cartão virtual.

Funções principais:

* Criar um cartão;
* Consultar o ID do cartão;
* Visualizar saldo e status do cartão.

### 5.2 Operador da catraca

Pessoa que utilizará a tela da catraca virtual para validar o ID do cartão.

Funções principais:

* Digitar o ID do cartão;
* Validar entrada;
* Visualizar mensagem de entrada aprovada ou negada.

### 5.3 Empresa de ônibus

Representada pelo sistema principal.

Funções principais:

* Armazenar cartões;
* Validar cartões;
* Registrar passagens;
* Consultar histórico de uso.

---

## 6. Tecnologias utilizadas

### Back-end

* Python
* Flask

### Front-end

* HTML
* CSS

### Banco de dados

* SQLite

### Ambiente de execução

* GitHub Codespaces
* Navegador web
* Celulares conectados ao link público do sistema

---

## 7. Funcionamento esperado

O funcionamento geral será o seguinte:

1. O sistema é iniciado no GitHub Codespaces.
2. A porta do servidor Flask é aberta publicamente.
3. Os celulares acessam o link gerado pelo Codespaces.
4. Um celular acessa a área do passageiro.
5. O passageiro cria ou visualiza seu cartão.
6. O sistema gera um ID para o cartão.
7. O outro celular acessa a tela da catraca virtual.
8. Na catraca, o ID do cartão é digitado.
9. O sistema consulta o banco de dados SQLite.
10. Se o cartão existir e estiver válido, a entrada é aprovada.
11. Se o cartão não existir, estiver bloqueado ou sem saldo, a entrada é negada.
12. O sistema registra a tentativa no histórico.

---

## 8. Escopo do projeto

### 8.1 O que será desenvolvido

O sistema deverá conter:

* Página inicial;
* Página para criação de cartão;
* Página para visualização de cartão;
* Página da catraca virtual;
* Validação do ID do cartão;
* Banco de dados SQLite;
* Registro de histórico de passagens;
* Interface responsiva para funcionar no celular;
* Mensagens de entrada aprovada ou negada.

### 8.2 O que não será desenvolvido

O projeto não terá:

* Catraca física real;
* Integração com cartão RFID real;
* Pagamento real;
* Integração bancária;
* Aplicativo instalado no celular;
* Login avançado com autenticação real;
* Sistema completo de empresa de transporte.

---

## 9. Funcionalidades principais

### 9.1 Criar cartão

O usuário poderá criar um cartão virtual informando dados básicos.

Campos sugeridos:

* Nome do passageiro;
* CPF ou identificador simples, se necessário;
* Saldo inicial;
* Status do cartão.

Após o cadastro, o sistema deverá gerar um ID para o cartão.

Exemplo:

```text
Nome: João da Silva
ID do cartão: 1001
Saldo: R$ 20,00
Status: Ativo
```

---

### 9.2 Visualizar cartão

O usuário poderá consultar um cartão existente usando o ID.

A tela deverá mostrar:

* ID do cartão;
* Nome do passageiro;
* Saldo;
* Status;
* Data de criação.

---

### 9.3 Tela da catraca virtual

A tela da catraca será usada para simular a entrada no ônibus.

Ela deverá conter:

* Campo para digitar o ID do cartão;
* Botão para validar;
* Área de resultado.

Exemplo:

```text
Digite o ID do cartão:
[__________]

[Validar entrada]
```

---

### 9.4 Validar entrada

Ao digitar o ID do cartão, o sistema deverá verificar:

* Se o cartão existe;
* Se o cartão está ativo;
* Se o cartão possui saldo suficiente.

Se tudo estiver correto, o sistema aprova a entrada.

Mensagem esperada:

```text
Entrada aprovada.
Boa viagem!
```

Se houver algum problema, o sistema nega a entrada.

Mensagens possíveis:

```text
Entrada negada. Cartão não encontrado.
```

```text
Entrada negada. Cartão bloqueado.
```

```text
Entrada negada. Saldo insuficiente.
```

---

### 9.5 Registrar passagem

Toda tentativa de validação deverá ser registrada no banco de dados.

O histórico deverá guardar:

* ID do cartão;
* Data e hora da tentativa;
* Status da tentativa;
* Motivo da aprovação ou negação;
* Valor descontado, se aprovado.

---

### 9.6 Histórico de passagens

O sistema poderá ter uma página para exibir as passagens registradas.

Informações exibidas:

* ID do cartão;
* Nome do passageiro;
* Data e hora;
* Resultado;
* Valor cobrado.

---

## 10. Regras de negócio

### 10.1 Cartão ativo

Um cartão só poderá liberar a entrada se estiver com status **ativo**.

### 10.2 Cartão inexistente

Se o ID digitado não existir no banco de dados, a entrada deverá ser negada.

### 10.3 Saldo insuficiente

Se o cartão existir, mas o saldo for menor que o valor da passagem, a entrada deverá ser negada.

### 10.4 Desconto de saldo

Quando a entrada for aprovada, o sistema deverá descontar o valor da passagem do saldo do cartão.

Exemplo:

```text
Saldo antes: R$ 20,00
Valor da passagem: R$ 5,00
Saldo depois: R$ 15,00
```

### 10.5 Registro obrigatório

Toda tentativa de entrada deve ser registrada, mesmo que seja negada.

---

## 11. Valor da passagem

Para a demonstração, o valor da passagem poderá ser fixo.

Valor sugerido:

```text
R$ 5,00
```

Esse valor poderá ser definido diretamente no código.

---

## 12. Telas do sistema

### 12.1 Página inicial

Objetivo: permitir que o usuário escolha qual área deseja acessar.

Botões sugeridos:

* Criar cartão;
* Visualizar cartão;
* Acessar catraca virtual;
* Ver histórico.

---

### 12.2 Página de criação de cartão

Objetivo: cadastrar um novo cartão virtual.

Campos:

* Nome do passageiro;
* Saldo inicial.

Botão:

* Criar cartão.

Resultado esperado:

* Mostrar o ID gerado;
* Mostrar dados do cartão criado.

---

### 12.3 Página de visualização de cartão

Objetivo: consultar um cartão existente.

Campos:

* ID do cartão.

Botão:

* Buscar cartão.

Resultado esperado:

* Mostrar dados do cartão;
* Informar caso o cartão não exista.

---

### 12.4 Página da catraca virtual

Objetivo: simular a validação da entrada no ônibus.

Campos:

* ID do cartão.

Botão:

* Validar entrada.

Resultado esperado:

* Entrada aprovada;
* Entrada negada;
* Motivo da negação.

---

### 12.5 Página de histórico

Objetivo: exibir as tentativas de entrada.

Dados exibidos:

* ID do cartão;
* Nome do passageiro;
* Data e hora;
* Resultado;
* Motivo;
* Valor descontado.

---

## 13. Estrutura sugerida do banco de dados

### 13.1 Tabela `cartoes`

Responsável por armazenar os cartões virtuais.

Campos sugeridos:

```text
id
nome_passageiro
saldo
status
data_criacao
```

Exemplo:

```text
id: 1001
nome_passageiro: João da Silva
saldo: 20.00
status: ativo
data_criacao: 2026-06-02
```

---

### 13.2 Tabela `passagens`

Responsável por armazenar o histórico de validações.

Campos sugeridos:

```text
id
cartao_id
data_hora
status
motivo
valor_cobrado
```

Exemplo:

```text
id: 1
cartao_id: 1001
data_hora: 2026-06-02 14:30
status: aprovado
motivo: Entrada liberada
valor_cobrado: 5.00
```

---

## 14. Estrutura sugerida do projeto

```text
sistema-catraca/
│
├── app.py
├── database.db
├── README.md
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── criar_cartao.html
│   ├── visualizar_cartao.html
│   ├── catraca.html
│   ├── resultado.html
│   └── historico.html
│
└── static/
    ├── style.css
    └── script.js
```

---

## 15. Rotas sugeridas

```text
/                     Página inicial
/criar-cartao          Tela de criação de cartão
/cartao                Tela de consulta de cartão
/catraca               Tela da catraca virtual
/validar-catraca       Validação do ID digitado
/historico             Histórico de passagens
```

---

## 16. Requisitos funcionais

### RF01 — Criar cartão

O sistema deve permitir o cadastro de um cartão virtual.

### RF02 — Gerar ID do cartão

O sistema deve gerar um ID único para cada cartão criado.

### RF03 — Consultar cartão

O sistema deve permitir a consulta de um cartão pelo ID.

### RF04 — Validar entrada

O sistema deve permitir que a catraca virtual valide um cartão pelo ID.

### RF05 — Aprovar entrada

O sistema deve aprovar a entrada quando o cartão existir, estiver ativo e tiver saldo suficiente.

### RF06 — Negar entrada

O sistema deve negar a entrada quando o cartão não existir, estiver bloqueado ou não tiver saldo suficiente.

### RF07 — Descontar saldo

O sistema deve descontar o valor da passagem quando a entrada for aprovada.

### RF08 — Registrar histórico

O sistema deve registrar todas as tentativas de entrada.

### RF09 — Exibir histórico

O sistema deve permitir a visualização do histórico de passagens.

### RF10 — Acesso por celulares

O sistema deve poder ser acessado por celulares através do link público gerado pelo Codespaces.

---

## 17. Requisitos não funcionais

### RNF01 — Responsividade

A interface deve funcionar corretamente em telas de celular.

### RNF02 — Simplicidade

O sistema deve ter uma interface simples e fácil de usar.

### RNF03 — Persistência de dados

Os dados dos cartões e passagens devem ser salvos no SQLite.

### RNF04 — Organização do código

O código deve ser organizado em arquivos separados para Python, HTML e CSS.

### RNF05 — Demonstração em rede

O sistema deve permitir acesso por mais de um dispositivo durante a apresentação.

---

## 18. Critérios de aceite

O projeto será considerado funcional se:

* Um cartão puder ser criado com sucesso;
* O sistema gerar um ID para o cartão;
* O cartão puder ser consultado pelo ID;
* A tela da catraca conseguir validar um ID;
* A entrada for aprovada quando o cartão for válido;
* A entrada for negada quando o cartão for inválido;
* O saldo for descontado quando a entrada for aprovada;
* O histórico registrar as tentativas;
* O sistema puder ser acessado por pelo menos dois celulares;
* A interface funcionar de forma adequada no navegador do celular.

---

## 19. Fluxo de demonstração

Durante a apresentação, o grupo poderá seguir este roteiro:

1. Abrir o sistema no computador pelo Codespaces.
2. Mostrar a página inicial.
3. Abrir o sistema em um celular para simular o passageiro.
4. Criar um novo cartão.
5. Mostrar o ID gerado.
6. Abrir o sistema em outro celular para simular a catraca.
7. Digitar o ID do cartão.
8. Validar a entrada.
9. Mostrar mensagem de entrada aprovada.
10. Consultar o cartão novamente para mostrar o saldo atualizado.
11. Mostrar o histórico de passagens.
12. Testar um ID inexistente para mostrar entrada negada.

---

## 20. Divisão sugerida de tarefas

### Pessoa 1 — Back-end

Responsável por:

* Criar o arquivo `app.py`;
* Configurar Flask;
* Criar rotas;
* Implementar validação da catraca.

### Pessoa 2 — Banco de dados

Responsável por:

* Criar o banco SQLite;
* Criar tabelas;
* Inserir e consultar dados;
* Registrar histórico.

### Pessoa 3 — Front-end

Responsável por:

* Criar páginas HTML;
* Criar CSS;
* Fazer layout responsivo;
* Melhorar visual das telas.

### Pessoa 4 — Testes e apresentação

Responsável por:

* Testar no computador;
* Testar nos celulares;
* Configurar Codespaces;
* Preparar roteiro de apresentação.

---

## 21. Prioridade das funcionalidades

### Prioridade alta

* Criar cartão;
* Consultar cartão;
* Validar ID na catraca;
* Aprovar ou negar entrada;
* Salvar dados no SQLite.

### Prioridade média

* Histórico de passagens;
* Desconto de saldo;
* Interface responsiva.

### Prioridade baixa

* Melhorias visuais;
* Tela administrativa;
* Filtros no histórico;
* Bloqueio e desbloqueio manual de cartão.

---

## 22. Possíveis melhorias futuras

Caso o grupo tenha tempo, o sistema poderá receber:

* Tela de administração;
* Login para funcionários;
* Edição de saldo;
* Bloqueio de cartões;
* QR Code do cartão;
* Leitura simulada por botão;
* Relatório de passagens;
* Página com estatísticas.

---

## 23. Riscos do projeto

### Risco 1 — Dificuldade para acessar pelo celular

Pode acontecer de a porta do Codespaces não estar pública.

Solução:

* Verificar se a porta está aberta como pública;
* Testar o acesso antes da apresentação.

### Risco 2 — Problemas com banco de dados

Pode acontecer de o SQLite não criar ou salvar corretamente os dados.

Solução:

* Criar uma função para inicializar o banco;
* Testar cadastro e consulta antes da apresentação.

### Risco 3 — Layout ruim no celular

Pode acontecer de as telas ficarem grandes ou desorganizadas no celular.

Solução:

* Criar CSS responsivo;
* Testar em tela pequena desde o início.

### Risco 4 — Grupo desenvolver funcionalidades diferentes

Pode acontecer de cada integrante entender o sistema de uma forma.

Solução:

* Usar este PRD como base;
* Dividir tarefas claramente;
* Definir primeiro o MVP.

---

## 24. MVP do projeto

A primeira versão funcional do sistema precisa ter apenas o essencial:

* Criar cartão;
* Mostrar ID do cartão;
* Digitar ID na tela da catraca;
* Validar cartão;
* Aprovar ou negar entrada;
* Salvar os dados no SQLite.

Depois que o MVP estiver funcionando, o grupo poderá adicionar histórico, saldo, melhorias visuais e outras funcionalidades.

---

## 25. Conclusão

O Sistema de Catraca Virtual para Ônibus será uma aplicação web simples, desenvolvida com Python, Flask, HTML, CSS e SQLite.

Ele servirá para demonstrar o funcionamento básico de um sistema de transporte público, simulando a criação de cartões e a validação de entrada em uma catraca virtual.

Mesmo sem uma catraca física, o projeto conseguirá representar o fluxo principal de um passageiro utilizando um cartão para entrar no ônibus.
