const {
  ActionRowBuilder,
  ButtonBuilder,
  ButtonStyle,
  ModalBuilder,
  PermissionFlagsBits,
  SlashCommandBuilder,
  TextInputBuilder,
  TextInputStyle
} = require('discord.js');
const { db, now, getGuildConfig, addLog } = require('../db/database');
const { baseEmbed } = require('../utils/embeds');
const { hasRole } = require('../core/permissions');

const commandData = [
  new SlashCommandBuilder()
    .setName('acao')
    .setDescription('Sistema de ações e escalação')
    .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild)
    .addSubcommand((s) => s.setName('criar').setDescription('Cria uma nova ação')
      .addStringOption((o) => o.setName('nome').setDescription('Nome da ação').setRequired(true))
      .addStringOption((o) => o.setName('data').setDescription('Data').setRequired(true))
      .addStringOption((o) => o.setName('horario').setDescription('Horário').setRequired(true))
      .addIntegerOption((o) => o.setName('maximo').setDescription('Máximo de participantes').setRequired(true))
      .addRoleOption((o) => o.setName('responsavel').setDescription('Cargo responsável').setRequired(false)))
];

async function handleCommand(interaction) {
  if (interaction.commandName !== 'acao') return false;
  const sub = interaction.options.getSubcommand();
  if (sub !== 'criar') return false;

  const name = interaction.options.getString('nome', true);
  const date = interaction.options.getString('data', true);
  const time = interaction.options.getString('horario', true);
  const max = interaction.options.getInteger('maximo', true);
  const responsibleRole = interaction.options.getRole('responsavel');

  const insert = db.prepare(`
    INSERT INTO actions (guild_id, channel_id, message_id, name, date, time, max_participants, participants_json, responsible_role_id, created_by, created_at)
    VALUES (?, ?, NULL, ?, ?, ?, ?, '[]', ?, ?, ?)
  `).run(interaction.guildId, interaction.channelId, name, date, time, max, responsibleRole?.id || null, interaction.user.id, now());

  const actionId = Number(insert.lastInsertRowid);
  const cfg = getGuildConfig(interaction.guildId);
  const message = await interaction.channel.send(buildActionMessage(cfg, {
    id: actionId,
    name,
    date,
    time,
    max_participants: max,
    participants_json: '[]'
  }));

  db.prepare('UPDATE actions SET message_id = ? WHERE id = ?').run(message.id, actionId);
  await interaction.reply({ content: `Ação #${actionId} criada com sucesso.`, ephemeral: true });
  return true;
}

function buildActionMessage(cfg, action) {
  const participants = JSON.parse(action.participants_json || '[]');
  const filled = participants.length;
  const remaining = Math.max(action.max_participants - filled, 0);
  const canJoin = remaining > 0;

  const row = new ActionRowBuilder().addComponents(
    new ButtonBuilder().setCustomId(`act:join:${action.id}`).setLabel(cfg.visual.actionJoinButtonLabel).setStyle(ButtonStyle.Success).setDisabled(!canJoin),
    new ButtonBuilder().setCustomId(`act:leave:${action.id}`).setLabel(cfg.visual.actionLeaveButtonLabel).setStyle(ButtonStyle.Secondary),
    new ButtonBuilder().setCustomId(`act:remove:${action.id}`).setLabel(cfg.visual.actionRemoveButtonLabel).setStyle(ButtonStyle.Danger)
  );

  const participantsText = participants.map((id, i) => `${i + 1}. <@${id}>`).join('\n') || '*Nenhum participante*';
  const embed = baseEmbed(
    cfg,
    `Ação: ${action.name}`,
    `**Data:** ${action.date}\n**Horário:** ${action.time}\n**Participantes:** ${filled}/${action.max_participants}\n**Vagas restantes:** ${remaining}\n\n${participantsText}`
  );

  return { embeds: [embed], components: [row] };
}

async function handleButton(interaction) {
  if (!interaction.customId.startsWith('act:')) return false;
  const [, action, id] = interaction.customId.split(':');
  const actionData = db.prepare('SELECT * FROM actions WHERE id = ?').get(Number(id));
  if (!actionData) {
    await interaction.reply({ content: 'Ação não encontrada.', ephemeral: true });
    return true;
  }

  const cfg = getGuildConfig(interaction.guildId);
  const participants = JSON.parse(actionData.participants_json || '[]');

  if (action === 'join') {
    if (participants.includes(interaction.user.id)) {
      await interaction.reply({ content: 'Você já está na lista.', ephemeral: true });
      return true;
    }

    if (participants.length >= actionData.max_participants) {
      await interaction.reply({ content: 'Não há mais vagas disponíveis.', ephemeral: true });
      return true;
    }

    participants.push(interaction.user.id);
    db.prepare('UPDATE actions SET participants_json = ? WHERE id = ?').run(JSON.stringify(participants), actionData.id);
    await updateActionMessage(interaction, actionData.id);
    await interaction.reply({ content: 'Você entrou na escalação.', ephemeral: true });
    return true;
  }

  if (action === 'leave') {
    const filtered = participants.filter((userId) => userId !== interaction.user.id);
    db.prepare('UPDATE actions SET participants_json = ? WHERE id = ?').run(JSON.stringify(filtered), actionData.id);
    await updateActionMessage(interaction, actionData.id);
    await interaction.reply({ content: 'Você saiu da escalação.', ephemeral: true });
    return true;
  }

  if (action === 'remove') {
    const allowed = hasRole(interaction.member, actionData.responsible_role_id) || hasRole(interaction.member, cfg.permissions.actionManagerRoleId);
    if (!allowed) {
      await interaction.reply({ content: 'Somente responsáveis podem remover membros.', ephemeral: true });
      return true;
    }

    const modal = new ModalBuilder().setCustomId(`act:remove-modal:${actionData.id}`).setTitle('Remover da ação');
    modal.addComponents(
      new ActionRowBuilder().addComponents(
        new TextInputBuilder().setCustomId('target').setLabel('ID do Discord').setStyle(TextInputStyle.Short).setRequired(true)
      )
    );

    await interaction.showModal(modal);
    return true;
  }

  return false;
}

async function handleModal(interaction) {
  if (!interaction.customId.startsWith('act:remove-modal:')) return false;
  const actionId = Number(interaction.customId.split(':')[2]);
  const target = interaction.fields.getTextInputValue('target').trim();
  const actionData = db.prepare('SELECT * FROM actions WHERE id = ?').get(actionId);

  if (!actionData) {
    await interaction.reply({ content: 'Ação não encontrada.', ephemeral: true });
    return true;
  }

  const participants = JSON.parse(actionData.participants_json || '[]');
  const filtered = participants.filter((id) => id !== target);
  db.prepare('UPDATE actions SET participants_json = ? WHERE id = ?').run(JSON.stringify(filtered), actionId);

  addLog(interaction.guildId, 'action_participant_removed', { actionId, targetUserId: target, by: interaction.user.id });
  await updateActionMessage(interaction, actionId);
  await interaction.reply({ content: `Membro ${target} removido da escalação.`, ephemeral: true });
  return true;
}

async function updateActionMessage(interaction, actionId) {
  const action = db.prepare('SELECT * FROM actions WHERE id = ?').get(actionId);
  const cfg = getGuildConfig(interaction.guildId);

  const channel = await interaction.guild.channels.fetch(action.channel_id).catch(() => null);
  if (!channel?.isTextBased()) return;
  const message = await channel.messages.fetch(action.message_id).catch(() => null);
  if (!message) return;

  await message.edit(buildActionMessage(cfg, action));
}

module.exports = { commandData, handleCommand, handleButton, handleModal, updateActionMessage };
