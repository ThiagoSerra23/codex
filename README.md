# Manager Bot

Um bot de Discord completo para gerenciamento de registros, farms, hierarquia e ações.

## Instalação

1.  **Pré-requisitos**: Python 3.8+ instalado.
2.  **Clone o repositório** ou baixe os arquivos.
3.  **Instale as dependências**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configuração**:
    *   Edite o arquivo `config.json` e insira o token do seu bot.
    *   Opcional: configure o prefixo (padrão `!`).

## Execução

Execute o bot com o comando:
```bash
python main.py
```

## Funcionalidades e Configuração

### 🎮 Comando Principal: `!painel`

Este é o **único comando** que você precisa usar. Ele abre um painel com todos os controles do bot:

#### Botões Disponíveis:

1. **⚔️ Criar Ação**
   - Abre um formulário para criar invasões/ações
   - Preencha: Nome, Data, Horário, Vagas
   - A ação aparece com botões de Entrar/Sair

2. **👑 Gerenciar Hierarquia**
   - Adicionar cargo: Digite "add", ID do cargo, posição
   - Remover cargo: Digite "remove", ID do cargo

3. **⚙️ Configurações**
   - **Configurar Registro**: Selecione visualmente os cargos e canal de logs
   - **Configurar Farm**: Selecione a categoria onde os canais serão criados

4. **🚜 Painel de Farm (Público)**
   - Envia o botão de farm no canal atual
   - Membros clicam para criar ticket de farm

5. **📝 Painel de Registro (Público)**
   - Envia o botão de registro no canal atual
   - Membros clicam para se registrar

### 📝 Comandos Legados (Opcionais)

- `!hierarquia setup`: Cria mensagem de hierarquia auto-atualizável
- `!hierarquia add @Cargo 1`: Adiciona cargo manualmente
- `!hierarquia remove @Cargo`: Remove cargo manualmente

## Permissões
O bot precisa das seguintes permissões no Discord:
*   `Manage Channels` (Gerenciar Canais) - para criar canais de farm.
*   `Manage Roles` (Gerenciar Cargos) - para dar cargo de registrado.
*   `Manage Messages` (Gerenciar Mensagens) - para editar e enviar mensagens.
*   `View Channels` & `Send Messages` - básico.

## Banco de Dados
O bot utiliza SQLite (`database.db`). O arquivo é criado automaticamente na primeira execução.

## Solução de Problemas
*   **Erro "Command not found"**: Certifique-se de que o bot carregou as extensões. Verifique o console para mensagens "Loaded extension".
*   **Erro de Token**: Verifique se o `config.json` está com o token correto.
*   **Erro de Permissão**: Verifique se o bot tem permissão de administrador ou as permissões listadas acima.
