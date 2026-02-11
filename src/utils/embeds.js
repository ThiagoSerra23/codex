const { EmbedBuilder } = require('discord.js');

function baseEmbed(config, title, description) {
  const embed = new EmbedBuilder()
    .setColor(config.visual.color)
    .setTitle(title || config.visual.title)
    .setDescription(description || config.visual.description)
    .setFooter({ text: config.visual.footer });

  if (config.visual.banner) embed.setImage(config.visual.banner);
  return embed;
}

module.exports = { baseEmbed };
