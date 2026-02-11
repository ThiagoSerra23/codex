const {
  ActionRowBuilder,
  ButtonBuilder,
  ButtonStyle,
  ChannelType,
  ModalBuilder,
  PermissionFlagsBits,
  SlashCommandBuilder,
  TextInputBuilder,
  TextInputStyle
} = require('discord.js');
const { db, now, getGuildConfig, addLog } = require('../db/database');
const { baseEmbed } = require('../utils/embeds');

const commandData = [
  new SlashCommandBuilder()
    .setName('setup-farm')
    .setDescription('Publica botão para registrar farm')
    .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild)
];

async function handleCommand(interaction) {
  if (interaction.commandName !== 'setup-farm') return false;
  const cfg = getGuildConfig(interaction.guildId);
  const row = new ActionRowBuilder().addComponents(
    new ButtonBuilder().setCustomId('farm:start').setLabel(cfg.visual.farmButtonLabel).setStyle(ButtonStyle.Primary)
  );

  await interaction.reply({ embeds: [baseEmbed(cfg, 'Registro de Farm', 'Clique para abrir seu registro de farm.')], components: [row] });
  return true;
}

async function handleButton(interaction) {
  if (interaction.customId !== 'farm:start') return false;
  const cfg = getGuildConfig(interaction.guildId);

  const permissionOverwrites = [
    { id: interaction.guild.roles.everyone.id, deny: [PermissionFlagsBits.ViewChannel] },
    { id: interaction.user.id, allow: [PermissionFlagsBits.ViewChannel, PermissionFlagsBits.SendMessages] }
  ];

  (cfg.permissions.farmAccessRoleIds || []).forEach((roleId) => {
    permissionOverwrites.push({ id: roleId, allow: [PermissionFlagsBits.ViewChannel, PermissionFlagsBits.SendMessages] });
  });

  const channel = await interaction.guild.channels.create({
    name: `farm-${interaction.user.username}`.slice(0, 90),
    type: ChannelType.GuildText,
    parent: cfg.channels.farmCategoryId || null,
    permissionOverwrites
  });

  const modal = new ModalBuilder().setCustomId(`farm:modal:${channel.id}`).setTitle('Registrar Farm');
  modal.addComponents(
    new ActionRowBuilder().addComponents(new TextInputBuilder().setCustomId('farm').setLabel('Quantidade de farm entregue').setStyle(TextInputStyle.Short).setRequired(true)),
    new ActionRowBuilder().addComponents(new TextInputBuilder().setCustomId('powder').setLabel('Quantidade de pólvora').setStyle(TextInputStyle.Short).setRequired(true)),
    new ActionRowBuilder().addComponents(new TextInputBuilder().setCustomId('capsule').setLabel('Quantidade de cápsula').setStyle(TextInputStyle.Short).setRequired(true))
  );

  await interaction.showModal(modal);
  return true;
}

async function handleModal(interaction) {
  if (!interaction.customId.startsWith('farm:modal:')) return false;
  const channelId = interaction.customId.split(':')[2];
  const cfg = getGuildConfig(interaction.guildId);

  const farmQtd = Number(interaction.fields.getTextInputValue('farm'));
  const powderQtd = Number(interaction.fields.getTextInputValue('powder'));
  const capsuleQtd = Number(interaction.fields.getTextInputValue('capsule'));

  db.prepare(`
    INSERT INTO farm_entries (guild_id, user_id, channel_id, farm_qtd, powder_qtd, capsule_qtd, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `).run(interaction.guildId, interaction.user.id, channelId, farmQtd, powderQtd, capsuleQtd, now());

  const channel = await interaction.guild.channels.fetch(channelId).catch(() => null);
  if (channel?.isTextBased()) {
    await channel.send({
      embeds: [baseEmbed(cfg, 'Registro de Farm Confirmado', `**Autor:** <@${interaction.user.id}>\n**Farm entregue:** ${farmQtd}\n**Pólvora:** ${powderQtd}\n**Cápsula:** ${capsuleQtd}`)]
    });
  }

  addLog(interaction.guildId, 'farm_registered', { userId: interaction.user.id, channelId, farmQtd, powderQtd, capsuleQtd });
  await interaction.reply({ content: `Registro enviado em <#${channelId}>.`, ephemeral: true });
  return true;
}

module.exports = { commandData, handleCommand, handleButton, handleModal };
