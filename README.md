# Discord Management Bot

Bot de Discord profissional, modular e configurável para:

- Registro com aprovação por cargo e logs.
- Registro de farm com criação automática de canal privado.
- Hierarquia configurável com atualização automática.
- Ações com escalação e controle de vagas em tempo real.
- Painel e comando de configuração sem editar código.

## Requisitos

- Node.js 20+
- Token de bot Discord

## Instalação

```bash
npm install
cp .env.example .env
# preencher DISCORD_TOKEN
npm start
```

## Configuração rápida

1. Use `/config` para definir canais e cargos:
   - `channels.registrationReviewChannelId`
   - `channels.logsChannelId`
   - `channels.farmCategoryId`
   - `permissions.registrationReviewerRoleId`
   - `permissions.registrationApprovedRoleId`
   - `permissions.actionManagerRoleId`
   - `permissions.farmAccessRoleIds` (ids separados por vírgula)
2. Use `/setup-registro` e `/setup-farm` para publicar painéis.
3. Use `/hierarquia publicar` para publicar quadro hierárquico.
4. Use `/acao criar` para criar escalas.

## Banco de dados

O bot utiliza SQLite (`data.sqlite`) e cria/mantém as tabelas automaticamente no boot.

## Segurança e permissões

- Todas as aprovações de registro exigem cargo configurado em `permissions.registrationReviewerRoleId`.
- Remoção manual de participantes em ações exige cargo responsável da ação ou `permissions.actionManagerRoleId`.
