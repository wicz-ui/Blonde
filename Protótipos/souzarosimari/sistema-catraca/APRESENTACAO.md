# 🎤 Roteiro de Apresentação Acadêmica

Guia rápido para apresentar o projeto à banca sem imprevistos.

## Preparação física da sala

- **Tela 1 (projetor):** aberta em `/historico`. A página atualiza sozinha a
  cada poucos segundos, então qualquer validação aparece automaticamente.
- **Tela 2 (celular do passageiro):** aberta em `/buscar`.
- **Tela 3 (celular do operador):** aberta em `/catraca`.

## Roteiro de fala

### Introdução (1 minuto)

"Nosso projeto simula o ecossistema de bilhetagem eletrônica de uma empresa
de transporte público sem depender de catracas físicas. A arquitetura é
totalmente web, construída com Flask e SQLite, permitindo que qualquer
celular com acesso à internet funcione como cartão virtual ou como
validador."

### Demonstração prática (3 minutos)

1. **Cenário de sucesso:** digite `1001` na catraca. A tela fica verde, o
   braço da catraca "abre" na animação e o histórico no projetor atualiza
   sozinho mostrando a tarifa de R$ 5,00 descontada.
2. **Saldo insuficiente:** digite `1003`. A tela fica vermelha explicando
   que o saldo é menor que a tarifa.
3. **Cartão bloqueado:** digite `1004`. Mesmo com saldo disponível, a
   entrada é negada porque o status do cartão é `bloqueado`.
4. **Cadastro em tempo real:** no celular do passageiro, crie um cartão com
   o nome de um dos professores e use o ID gerado imediatamente na catraca.

### Conclusão (1 minuto)

"Com isso demonstramos persistência de dados relacional, regras de negócio
aplicadas em tempo real, rotas dinâmicas e uma interface responsiva
resolvendo um problema logístico do dia a dia."

## Perguntas frequentes da banca

**"O SQLite é local. Como isso funcionaria com o ônibus em movimento, sem
internet estável?"**

> O SQLite foi escolhido pela leveza, ideal para um protótipo acadêmico. Em
> uma operação real, a arquitetura correta seria híbrida: o validador
> físico teria um banco local para aprovar passagens offline instantaneamente,
> sincronizando os registros com o servidor central quando o ônibus
> encontrasse conexão estável.

**"Qualquer pessoa com a URL pública pode digitar um ID e liberar a
catraca ou ver dados de um passageiro. Como resolveriam isso?"**

> Como é um MVP para fins demonstrativos, focamos nas regras de negócio.
> Em produção, adicionaríamos autenticação para a rota da catraca (login do
> operador) e substituiríamos o ID numérico simples por um token dinâmico,
> no estilo de um QR Code que muda periodicamente, dificultando fraude ou
> clonagem.

**"O que acontece se dois passageiros validarem o cartão ao mesmo tempo?
O SQLite aguenta?"**

> Para poucos dispositivos simultâneos, o SQLite gerencia bem as escritas
> através de locks automáticos. Em uma frota real, com milhares de
> validações simultâneas, migraríamos para um banco mais robusto, como
> PostgreSQL, possivelmente com cache em memória (Redis) para autorizações
> de baixa latência.

## Dica extra

Se um professor apontar uma limitação ou sugerir uma melhoria, não
justifique com falta de tempo. Responda como um time profissional faria:
"Esse ponto está mapeado no nosso backlog de melhorias para uma próxima
versão do sistema."
