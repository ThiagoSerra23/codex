require('dotenv').config();
const { Client, GatewayIntentBits, Partials, Events } = require('discord.js');
const { migrate } = require('./db/database');
const configPanel = require('./modules/configPanel');
const registerModule = require('./modules/register');
const farmModule = require('./modules/farm');
const hierarchyModule = require('./modules/hierarchy');
const actionsModule = require('./modules/actions');

migrate();

const client = new Client({
  intents: [GatewayIntentBits.Guilds, GatewayIntentBits.GuildMembers, GatewayIntentBits.GuildMessages],
  partials: [Partials.Channel]
});

const modules = [configPanel, registerModule, farmModule, hierarchyModule, actionsModule];
const commandData = modules.flatMap((m) => m.commandData || []).map((c) => c.toJSON());

client.once(Events.ClientReady, async (readyClient) => {
  console.log(`✅ Bot online: ${readyClient.user.tag}`);
  await readyClient.application.commands.set(commandData);
  console.log(`✅ ${commandData.length} comandos sincronizados.`);
});

client.on(Events.InteractionCreate, async (interaction) => {
  try {
    if (interaction.isChatInputCommand()) {
      for (const mod of modules) {
        if (mod.handleCommand && await mod.handleCommand(interaction)) return;
      }
    }

    if (interaction.isButton()) {
      for (const mod of modules) {
        if (mod.handleButton && await mod.handleButton(interaction)) return;
      }
    }

    if (interaction.isModalSubmit()) {
      for (const mod of modules) {
        if (mod.handleModal && await mod.handleModal(interaction)) return;
      }
    }
  } catch (error) {
    console.error('Erro de interação:', error);
    if (interaction.deferred || interaction.replied) {
      await interaction.followUp({ content: 'Ocorreu um erro ao processar a ação.', ephemeral: true }).catch(() => null);
    } else {
      await interaction.reply({ content: 'Ocorreu um erro ao processar a ação.', ephemeral: true }).catch(() => null);
    }
  }
});

client.on(Events.GuildMemberUpdate, async (_, newMember) => {
  await hierarchyModule.refreshHierarchy(newMember.guild).catch(() => null);
});

if (!process.env.DISCORD_TOKEN) {
  throw new Error('Defina DISCORD_TOKEN no arquivo .env');
}

client.login(process.env.DISCORD_TOKEN);
