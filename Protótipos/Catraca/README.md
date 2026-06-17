# Sistema de Catraca Virtual para Ônibus

Aplicação web em Flask, HTML, CSS e SQLite para simular uma catraca de ônibus com controle de acesso por perfil, token privado de passageiro, estações fictícias e histórico temporário.

## Funcionalidades

- Criar cartão virtual com nome fictício, saldo inicial e status.
- Gerar código público do cartão para uso na catraca.
- Gerar token privado do passageiro para visualizar somente o próprio cartão.
- Bloquear acesso de usuário a cartões de outras pessoas.
- Validar entrada na catraca sem exibir nome completo ou saldo do passageiro.
- Registrar estação de origem e destino quando houver rota planejada.
- Planejar viagem com um ou mais trechos.
- Recarregar o próprio cartão com valores simulados.
- Registrar histórico temporário de recargas.
- Baixar cartão em PDF sem expor token privado.
- Baixar cartão em PDF no formato de cartão, com QR Code do código público.
- Ler QR Code na tela da catraca com `html5-qrcode`, usando câmera ao vivo em HTTPS ou captura de foto em HTTP/IP local.
- Usar link curto privado `/meu/TOKEN` para o passageiro abrir o próprio cartão.
- Cadastrar, ativar e desativar estações fictícias de Londrina e região.
- Configurar valor da passagem, limites de recarga, retenções e opções do PDF.
- Apagar automaticamente histórico expirado.
- Administrar cartões, dispositivos e links autorizados.
- Interface responsiva para uso em celulares.

## Como executar

Crie um ambiente virtual e instale as dependências:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Inicie o servidor:

```bash
python app.py
```

Para desenvolvimento local com recarregamento automático:

```bash
FLASK_DEBUG=1 python app.py
```

## Acessos de demonstração

```text
Admin:
http://localhost:5000/admin?token=admin-demo-2026

Catraca:
http://localhost:5000/catraca?token=catraca-demo-2026
```

O passageiro deve usar o link privado gerado na criação do cartão ou listado em **Admin > Cartões**. O formato é:

```text
http://localhost:5000/usuario/meu-cartao?token=TOKEN_PRIVADO_DO_USUARIO
```

Também existe o link curto:

```text
http://localhost:5000/meu/TOKEN_PRIVADO_DO_USUARIO
```

No GitHub Codespaces, abra a porta `5000` como pública. Em rede local, substitua `localhost` pelo IP mostrado pelo Flask.

## Regras de acesso

- Admin acessa telas administrativas, cartões, estações, configurações, histórico e dispositivos.
- Catraca acessa apenas a tela de validação e usa o código público do cartão.
- Passageiro acessa apenas o próprio cartão, planejamento e própria viagem usando token privado.
- O passageiro não consegue consultar cartão por ID digitado.
- A autorização é validada no back-end.

## Rotas principais

- `/admin` painel administrativo
- `/criar-cartao` criação de cartão, somente admin
- `/admin/cartoes` lista de cartões, status e links privados
- `/admin/estacoes` cadastro e ativação de estações
- `/admin/configuracoes` valor da passagem e retenção do histórico
- `/admin/historico` histórico temporário de passagens
- `/admin/dispositivos` tokens de admin, catraca e acessos legados
- `/usuario/meu-cartao` cartão do passageiro autenticado
- `/meu/<token>` link curto privado para o cartão do passageiro
- `/usuario/recarregar-cartao` recarga simulada do próprio cartão
- `/usuario/recargas` histórico temporário de recargas do passageiro
- `/usuario/cartao/pdf` download do cartão em PDF
- `/usuario/planejar-viagem` planejamento com múltiplos trechos
- `/usuario/minha-viagem` rota planejada atual
- `/catraca` tela restrita da catraca
- `/catraca/validar` validação da entrada
- `/admin/recargas` histórico administrativo de recargas

## Banco de dados

O SQLite é criado e migrado automaticamente no arquivo `database.db`. As tabelas principais são:

- `usuarios`
- `cartoes`
- `passagens`
- `recargas`
- `configuracoes`
- `estacoes`
- `rotas_viagem`
- `trechos_viagem`
- `dispositivos`

## Privacidade

Use apenas dados fictícios na apresentação. O sistema guarda o mínimo necessário para a simulação e remove o histórico depois do período configurado pelo administrador.

O PDF do cartão mostra o nome fictício, código público, status, emissão e, se configurado, saldo. Ele não inclui o token privado do passageiro.

O QR Code do PDF contém apenas `CARD:<codigo_publico>`, usado pela catraca para preencher e validar o cartão sem digitação manual.

Em HTTPS, a catraca usa leitura ao vivo pela câmera com `html5-qrcode`. Em `http://IP_LOCAL`, onde navegadores móveis podem bloquear vídeo ao vivo, use o botão **Usar foto do QR Code** para abrir a câmera do celular, capturar uma foto e ler o QR Code localmente, sem enviar a imagem ao servidor.
