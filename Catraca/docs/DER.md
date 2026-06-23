# DER — Catraca Virtual

Este documento apresenta o Diagrama Entidade-Relacionamento (DER) do banco SQLite utilizado pelo sistema. O diagrama pode ser renderizado diretamente no GitHub.

## Diagrama entidade-relacionamento

```mermaid
erDiagram
    USUARIOS ||--o{ CARTOES : possui
    USUARIOS ||--o{ RECARGAS : realiza
    USUARIOS ||--o{ ROTAS_VIAGEM : planeja
    USUARIOS o|--o{ DISPOSITIVOS : vincula

    CARTOES ||--o{ PASSAGENS : registra
    CARTOES ||--o{ RECARGAS : recebe
    CARTOES ||--o{ ROTAS_VIAGEM : utiliza
    CARTOES o|--o{ DISPOSITIVOS : vincula

    ROTAS_VIAGEM ||--|{ TRECHOS_VIAGEM : contem
    ESTACOES ||--o{ TRECHOS_VIAGEM : origem
    ESTACOES ||--o{ TRECHOS_VIAGEM : destino
    ESTACOES o|--o{ PASSAGENS : origem
    ESTACOES o|--o{ PASSAGENS : destino
    ESTACOES o|--o{ DISPOSITIVOS : localiza

    USUARIOS {
        INTEGER id PK
        TEXT nome
        TEXT token_usuario UK
        TEXT criado_em
        INTEGER ativo
    }

    CARTOES {
        INTEGER id PK
        INTEGER usuario_id FK
        TEXT codigo_publico UK
        TEXT nome_passageiro
        TEXT cpf
        TEXT numero_celular
        REAL saldo
        TEXT status
        TEXT data_criacao
        TEXT criado_em
        TEXT atualizado_em
    }

    ESTACOES {
        INTEGER id PK
        TEXT nome UK
        TEXT regiao
        INTEGER ativa
    }

    PASSAGENS {
        INTEGER id PK
        INTEGER cartao_id FK
        TEXT cartao_digitado
        INTEGER origem_id FK
        INTEGER destino_id FK
        TEXT data_hora
        TEXT status
        TEXT motivo
        REAL valor_cobrado
        TEXT expira_em
    }

    RECARGAS {
        INTEGER id PK
        INTEGER usuario_id FK
        INTEGER cartao_id FK
        REAL valor
        REAL saldo_anterior
        REAL saldo_novo
        TEXT data_hora
        TEXT status
        TEXT expira_em
    }

    ROTAS_VIAGEM {
        INTEGER id PK
        INTEGER usuario_id FK
        INTEGER cartao_id FK
        TEXT criado_em
        TEXT status
    }

    TRECHOS_VIAGEM {
        INTEGER id PK
        INTEGER rota_id FK
        INTEGER origem_id FK
        INTEGER destino_id FK
        INTEGER ordem
        REAL valor
    }

    DISPOSITIVOS {
        INTEGER id PK
        TEXT nome_dispositivo
        TEXT tipo
        TEXT token_acesso UK
        INTEGER ativo
        INTEGER cartao_id FK
        INTEGER usuario_id FK
        INTEGER estacao_id FK
    }

    CONFIGURACOES {
        INTEGER id PK
        TEXT chave UK
        TEXT valor
    }
```

## Entidades

| Entidade | Finalidade | Chave principal |
|---|---|---|
| `usuarios` | Passageiros com token privado de acesso | `id` |
| `cartoes` | Cartões públicos, saldo e status | `id` |
| `estacoes` | Pontos de embarque, terminais e regiões | `id` |
| `passagens` | Tentativas de entrada aprovadas ou negadas | `id` |
| `recargas` | Créditos adicionados ao cartão | `id` |
| `rotas_viagem` | Roteiros planejados por passageiro | `id` |
| `trechos_viagem` | Etapas que formam uma rota planejada | `id` |
| `dispositivos` | Acessos de administrador, catraca ou passageiro | `id` |
| `configuracoes` | Parâmetros dinâmicos de regra de negócio | `id` |

## Relações e cardinalidades

| Origem | Relação | Destino | Cardinalidade |
|---|---|---|---|
| Usuário | possui | Cartão | 1 : N |
| Usuário | realiza | Recarga | 1 : N |
| Usuário | planeja | Rota de viagem | 1 : N |
| Cartão | registra | Passagem | 1 : N |
| Cartão | recebe | Recarga | 1 : N |
| Cartão | utiliza | Rota de viagem | 1 : N |
| Rota de viagem | contém | Trecho de viagem | 1 : N |
| Estação | participa como origem/destino | Passagem e trecho | 1 : N |
| Dispositivo | pode estar vinculado a | Usuário, cartão e/ou estação | 0 : 1 em cada vínculo |

`configuracoes` é uma entidade independente: cada linha armazena uma chave única e seu valor atual.

## Regras de integridade relevantes

- `usuarios.token_usuario`, `cartoes.codigo_publico`, `estacoes.nome`, `dispositivos.token_acesso` e `configuracoes.chave` são únicos.
- `cartoes.status` aceita `ativo` ou `bloqueado`.
- `passagens.status` aceita `aprovado` ou `negado`.
- `rotas_viagem.status` aceita `planejada`, `cancelada` ou `concluida`.
- `dispositivos.tipo` aceita `admin`, `catraca` ou `usuario`.
- O saldo do cartão não pode ser negativo.
- Passagens e recargas possuem `expira_em`, utilizado pela limpeza automática de histórico.

## Exclusão de cartão

A exclusão administrativa é transacional. Ao excluir um cartão, o sistema remove seus trechos, rotas, passagens, recargas e dispositivos vinculados. Se o usuário não possuir outro cartão, seu acesso e os dispositivos associados a ele também são removidos.

## Índices utilizados

| Índice | Objetivo |
|---|---|
| `idx_cartoes_codigo_publico` | Busca rápida do cartão por QR Code/código público |
| `idx_passagens_expira_em` | Limpeza do histórico de passagens |
| `idx_recargas_expira_em` | Limpeza do histórico de recargas |
