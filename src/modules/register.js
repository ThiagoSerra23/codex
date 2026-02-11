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
const { db, now, getGuildConfig, addLog } = require('../db/database');
const { baseEmbed } = require('../utils/embeds');
const { hasRole } = require('../core/permissions');

const commandData = [
  new SlashCommandBuilder()
    .setName('setup-registro')
    .setDescription('Publica painel de registro.')
    .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild)
];

async function handleCommand(interaction) {
  if (interaction.commandName !== 'setup-registro') return false;
  const cfg = getGuildConfig(interaction.guildId);
  const row = new ActionRowBuilder().addComponents(
    new ButtonBuilder().setCustomId('register:start').setLabel(cfg.visual.registerButtonLabel).setStyle(ButtonStyle.Success)
  );
  await interaction.reply({ embeds: [baseEmbed(cfg, 'Registro', 'Clique no botão para preencher seu formulário.')], components: [row] });
  return true;
}

async function handleButton(interaction) {
  if (interaction.customId === 'register:start') {
    const modal = new ModalBuilder().setCustomId('register:modal').setTitle('Formulário de Registro');
    modal.addComponents(
      new ActionRowBuilder().addComponents(new TextInputBuilder().setCustomId('nome').setLabel('Nome').setStyle(TextInputStyle.Short).setRequired(true)),
      new ActionRowBuilder().addComponents(new TextInputBuilder().setCustomId('idade').setLabel('Idade').setStyle(TextInputStyle.Short).setRequired(true)),
      new ActionRowBuilder().addComponents(new TextInputBuilder().setCustomId('experiencia').setLabel('Experiência').setStyle(TextInputStyle.Paragraph).setRequired(true))
    );
    await interaction.showModal(modal);
    return true;
  }

  if (interaction.customId.startsWith('register:approve:') || interaction.customId.startsWith('register:reject:')) {
    const [, action, id] = interaction.customId.split(':');
    const cfg = getGuildConfig(interaction.guildId);

    if (!hasRole(interaction.member, cfg.permissions.registrationReviewerRoleId)) {
      await interaction.reply({ content: 'Você não possui permissão para revisar registros.', ephemeral: true });
      return true;
    }

    const registration = db.prepare('SELECT * FROM registrations WHERE id = ?').get(Number(id));
    if (!registration || registration.status !== 'pending') {
      await interaction.reply({ content: 'Registro não encontrado ou já processado.', ephemeral: true });
      return true;
    }

    const status = action === 'approve' ? 'approved' : 'rejected';
    db.prepare('UPDATE registrations SET status = ?, reviewer_id = ?, updated_at = ? WHERE id = ?')
      .run(status, interaction.user.id, now(), Number(id));

    const user = await interaction.client.users.fetch(registration.user_id);
    await user.send(`Seu registro foi **${status === 'approved' ? 'aprovado' : 'recusado'}** em ${interaction.guild.name}.`)
      .catch(() => null);

    if (status === 'approved' && cfg.permissions.registrationApprovedRoleId) {
      const member = await interaction.guild.members.fetch(registration.user_id).catch(() => null);
      if (member) await member.roles.add(cfg.permissions.registrationApprovedRoleId).catch(() => null);
    }

    addLog(interaction.guildId, 'registration_reviewed', {
      registrationId: Number(id),
      status,
      reviewerId: interaction.user.id,
      targetUserId: registration.user_id
    });

    await sendLog(interaction.guild, cfg, `Registro #${id} ${status === 'approved' ? 'aprovado' : 'recusado'} por <@${interaction.user.id}>.`);
    await interaction.update({ components: [] });
    return true;
  }

  return false;
}

async function handleModal(interaction) {
  if (interaction.customId !== 'register:modal') return false;
  const cfg = getGuildConfig(interaction.guildId);

  const form = {
    nome: interaction.fields.getTextInputValue('nome'),
    idade: interaction.fields.getTextInputValue('idade'),
    experiencia: interaction.fields.getTextInputValue('experiencia')
  };

  const info = db.prepare(`
    INSERT INTO registrations (guild_id, user_id, status, form_json, created_at, updated_at)
    VALUES (?, ?, 'pending', ?, ?, ?)
  `).run(interaction.guildId, interaction.user.id, JSON.stringify(form), now(), now());

  const reviewChannelId = cfg.channels.registrationReviewChannelId;
  const channel = reviewChannelId ? await interaction.guild.channels.fetch(reviewChannelId).catch(() => null) : null;

  if (channel && channel.isTextBased()) {
    const row = new ActionRowBuilder().addComponents(
      new ButtonBuilder().setCustomId(`register:approve:${info.lastInsertRowid}`).setLabel('Aprovar').setStyle(ButtonStyle.Success),
      new ButtonBuilder().setCustomId(`register:reject:${info.lastInsertRowid}`).setLabel('Recusar').setStyle(ButtonStyle.Danger)
    );

    await channel.send({
      embeds: [baseEmbed(cfg, `Novo Registro #${info.lastInsertRowid}`, `**Usuário:** <@${interaction.user.id}>\n**Nome:** ${form.nome}\n**Idade:** ${form.idade}\n**Experiência:** ${form.experiencia}`)],
      components: [row]
    });
  }

  await interaction.reply({ content: 'Registro enviado para análise.', ephemeral: true });
  return true;
}

async function sendLog(guild, config, message) {
  const channelId = config.channels.logsChannelId;
  if (!channelId) return;
  const channel = await guild.channels.fetch(channelId).catch(() => null);
  if (channel?.isTextBased()) await channel.send({ embeds: [baseEmbed(config, 'Log', message)] });
}

module.exports = { commandData, handleCommand, handleButton, handleModal };
