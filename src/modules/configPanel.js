const {
  ActionRowBuilder,
  ButtonBuilder,
  ButtonStyle,
  ModalBuilder,
  TextInputBuilder,
  TextInputStyle,
  SlashCommandBuilder,
  PermissionFlagsBits
} = require('discord.js');
const { getGuildConfig, patchGuildConfig, setGuildConfig } = require('../db/database');
const { baseEmbed } = require('../utils/embeds');

const commandData = [
  new SlashCommandBuilder()
    .setName('painel')
    .setDescription('Abre painel de configuração visual/permissões.')
    .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild),
  new SlashCommandBuilder()
    .setName('config')
    .setDescription('Define configuração por chave')
    .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild)
    .addStringOption((o) => o.setName('secao').setDescription('visual|permissions|channels').setRequired(true))
    .addStringOption((o) => o.setName('chave').setDescription('chave da seção').setRequired(true))
    .addStringOption((o) => o.setName('valor').setDescription('valor').setRequired(true))
];

async function handleCommand(interaction) {
  if (interaction.commandName === 'painel') {
    const cfg = getGuildConfig(interaction.guildId);
    const embed = baseEmbed(cfg, 'Painel de Configuração', 'Edite visual e permissões sem alterar código.');
    const row = new ActionRowBuilder().addComponents(
      new ButtonBuilder().setCustomId('cfg:visual').setLabel('Editar Visual').setStyle(ButtonStyle.Primary),
      new ButtonBuilder().setCustomId('cfg:permissions').setLabel('Editar Permissões').setStyle(ButtonStyle.Secondary)
    );
    await interaction.reply({ embeds: [embed], components: [row], ephemeral: true });
    return true;
  }

  if (interaction.commandName === 'config') {
    const secao = interaction.options.getString('secao');
    const chave = interaction.options.getString('chave');
    const valor = interaction.options.getString('valor');

    if (!['visual', 'permissions', 'channels'].includes(secao)) {
      await interaction.reply({ content: 'Seção inválida.', ephemeral: true });
      return true;
    }

    let normalized = valor;
    if (valor === 'null') normalized = null;
    if (valor === 'true') normalized = true;
    if (valor === 'false') normalized = false;
    if (valor.includes(',')) normalized = valor.split(',').map((x) => x.trim()).filter(Boolean);

    patchGuildConfig(interaction.guildId, secao, chave, normalized);
    await interaction.reply({ content: `Configuração atualizada: ${secao}.${chave} = ${valor}`, ephemeral: true });
    return true;
  }
  return false;
}

async function handleButton(interaction) {
  if (!interaction.customId.startsWith('cfg:')) return false;
  const section = interaction.customId.split(':')[1];

  const modal = new ModalBuilder()
    .setCustomId(`cfgmodal:${section}`)
    .setTitle(`Editar ${section}`);

  const input = new TextInputBuilder()
    .setCustomId('payload')
    .setLabel('JSON da seção (ex: {"title":"Novo"})')
    .setStyle(TextInputStyle.Paragraph)
    .setRequired(true);

  modal.addComponents(new ActionRowBuilder().addComponents(input));
  await interaction.showModal(modal);
  return true;
}

async function handleModal(interaction) {
  if (!interaction.customId.startsWith('cfgmodal:')) return false;
  const section = interaction.customId.split(':')[1];
  const payload = interaction.fields.getTextInputValue('payload');

  try {
    const parsed = JSON.parse(payload);
    const config = getGuildConfig(interaction.guildId);
    config[section] = { ...config[section], ...parsed };
    setGuildConfig(interaction.guildId, config);
    await interaction.reply({ content: `Seção ${section} atualizada.`, ephemeral: true });
  } catch (error) {
    await interaction.reply({ content: `JSON inválido: ${error.message}`, ephemeral: true });
  }

  return true;
}

module.exports = { commandData, handleCommand, handleButton, handleModal };
