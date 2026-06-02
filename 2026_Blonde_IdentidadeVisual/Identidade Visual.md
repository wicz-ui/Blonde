# Guia de Estrutura de Projeto: Identidade Visual

Este documento detalha a organização técnica dos diretórios para projetos de branding. A estrutura foi desenhada para garantir a rastreabilidade desde a estratégia inicial até os arquivos de produção final.

## 🌳 Árvore de Diretórios
```text
.
├── 01_Pesquisa_Estrategia       # Fundamentação e referências
├── 02_Processo_Criativo         # Rascunhos e arquivos editáveis
├── 03_Apresentacao              # Defesa de conceito e mockups
├── 04_Entregaveis_Finais        # Arquivos finais prontos para uso
├── 05_Aplicacoes_Brand_Assets   # Implementação em diversos suportes
└── 06_Manual_da_Marca           # Regras de uso e diretrizes

🛠️ Especificações das Pastas
01. Pesquisa e Estratégia

Fase de imersão e definição do "norte" visual.

    Analise_Concorrentes: Documentação sobre o posicionamento visual de marcas do mesmo setor.

    Moodboard: Painel semântico com referências de cor, tipografia e estilo visual aprovado.

02. Processo Criativo

Espaço de trabalho interno. Não deve ser compartilhado com o cliente final.

    Rascunhos: Digitalizações de desenhos manuais ou rascunhos rápidos.

    Arquivos_Trabalho: Arquivos fonte em formato aberto (ex: .ai, .psd, .fig) em suas diversas versões de evolução.

03. Apresentação

Contém o arquivo final de defesa do projeto (geralmente em PDF) utilizado para a reunião de aprovação. Inclui a história da marca e os protótipos de aplicação.
04. Entregáveis Finais

A "Fonte da Verdade". Arquivos fechados e organizados por tipo de uso:

    01_Logotipo_Principal:

        Vetor: Arquivos escaláveis para impressão e alta resolução (AI, PDF, EPS).

        Digital: Arquivos em pixels para uso web e redes sociais (PNG transparente, JPG).

    02_Variacoes_Marca: Versões específicas para diferentes fundos:

        Preto_Branco: Versão em preto puro (K100).

        Negativa: Versão totalmente branca para fundos escuros.

    03_Tipografia: Arquivos de fontes (OTF/TTF) ou guias de licenciamento.

    04_Elementos_Graficos: Grafismos auxiliares, patterns (padronagens) e ícones de apoio.

05. Aplicações / Brand Assets

Materiais derivados da marca prontos para produção:

    Digital: Assets para redes sociais, assinaturas de e-mail e templates de apresentação.

    Papelaria: Arquivos de produção gráfica (cartão de visita, papel timbrado, envelopes) com marcas de corte e sangria.

06. Manual da Marca

Diretrizes técnicas de reprodução. Contém especificações de cores (CMYK, RGB, HEX, Pantone), margens de proteção e exemplos de usos proibidos.
📋 Convenções Técnicas

    Padrão de Nome de Arquivos: [CLIENTE]_[TIPO]_[VERSAO]_[DATA].[EXT]

        Exemplo: Acme_LogoPrincipal_Negativo_V02_2024.eps

    Formatos de Saída:

        Vetor: Sempre manter compatibilidade com versões anteriores (PDF/X-1a ou EPS).

        Digital: Otimizar PNGs para transparência e JPGs para compressão web.

    Escalabilidade: Todo arquivo na pasta 04_Entregaveis_Finais/Vetor deve estar com fontes convertidas em curvas.

Documento gerado para padronização de entregas de Identidade Visual.
