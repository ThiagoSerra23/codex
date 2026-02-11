const { SlashCommandBuilder, PermissionFlagsBits } = require('discord.js');
const { db, getGuildConfig, addLog } = require('../db/database');
const { baseEmbed } = require('../utils/embeds');

const commandData = [
  new SlashCommandBuilder()
    .setName('hierarquia')
    .setDescription('Gerencia hierarquia configurável')
    .setDefaultMemberPermissions(PermissionFlagsBits.ManageGuild)
    .addSubcommand((s) => s.setName('adicionar').setDescription('Adiciona cargo')
      .addRoleOption((o) => o.setName('cargo').setDescription('Cargo').setRequired(true)))
    .addSubcommand((s) => s.setName('remover').setDescription('Remove cargo')
      .addRoleOption((o) => o.setName('cargo').setDescription('Cargo').setRequired(true)))
    .addSubcommand((s) => s.setName('publicar').setDescription('Publica/atualiza mensagem da hierarquia')
      .addChannelOption((o) => o.setName('canal').setDescription('Canal alvo').setRequired(true)))
];

async function handleCommand(interaction) {
  if (interaction.commandName !== 'hierarquia') return false;

  const sub = interaction.options.getSubcommand();
  if (sub === 'adicionar') {
    const role = interaction.options.getRole('cargo', true);
    const maxPosition = db.prepare('SELECT MAX(position) as pos FROM hierarchy_roles WHERE guild_id = ?').get(interaction.guildId);
    db.prepare('INSERT INTO hierarchy_roles (guild_id, role_id, position) VALUES (?, ?, ?)').run(interaction.guildId, role.id, (maxPosition?.pos || 0) + 1);
    await interaction.reply({ content: `Cargo ${role} adicionado à hierarquia.`, ephemeral: true });
    await refreshHierarchy(interaction.guild);
    return true;
  }

  if (sub === 'remover') {
    const role = interaction.options.getRole('cargo', true);
    db.prepare('DELETE FROM hierarchy_roles WHERE guild_id = ? AND role_id = ?').run(interaction.guildId, role.id);
    await interaction.reply({ content: `Cargo ${role} removido da hierarquia.`, ephemeral: true });
    await refreshHierarchy(interaction.guild);
    return true;
  }

  if (sub === 'publicar') {
    const channel = interaction.options.getChannel('canal', true);
    const cfg = getGuildConfig(interaction.guildId);
    const message = await channel.send({ embeds: [baseEmbed(cfg, 'Hierarquia', 'Sincronizando...')] });
    db.prepare(`
      INSERT INTO hierarchy_views (guild_id, channel_id, message_id) VALUES (?, ?, ?)
      ON CONFLICT(guild_id) DO UPDATE SET channel_id = excluded.channel_id, message_id = excluded.message_id
    `).run(interaction.guildId, channel.id, message.id);

    await interaction.reply({ content: 'Painel de hierarquia publicado.', ephemeral: true });
    await refreshHierarchy(interaction.guild);
    addLog(interaction.guildId, 'hierarchy_published', { channelId: channel.id, messageId: message.id, userId: interaction.user.id });
    return true;
  }

  return false;
}

async function refreshHierarchy(guild) {
  const view = db.prepare('SELECT * FROM hierarchy_views WHERE guild_id = ?').get(guild.id);
  if (!view) return;

  const roles = db.prepare('SELECT role_id FROM hierarchy_roles WHERE guild_id = ? ORDER BY position ASC').all(guild.id);
  const lines = [];

  for (const roleData of roles) {
    const role = guild.roles.cache.get(roleData.role_id);
    if (!role) continue;
    const members = role.members.map((m) => `<@${m.id}>`).join(', ') || '*Nenhum membro*';
    lines.push(`### ${role.name}\n${members}`);
  }

  const cfg = getGuildConfig(guild.id);
  const channel = await guild.channels.fetch(view.channel_id).catch(() => null);
  if (!channel?.isTextBased()) return;

  const message = await channel.messages.fetch(view.message_id).catch(() => null);
  if (!message) return;

  await message.edit({
    embeds: [baseEmbed(cfg, 'Hierarquia Oficial', lines.join('\n\n') || 'Nenhum cargo configurado.')]
  });
}

module.exports = { commandData, handleCommand, refreshHierarchy };
