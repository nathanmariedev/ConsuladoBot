const { EmbedBuilder } = require('discord.js');

async function sendMessage(client, channelId, title, description, color = 0x0099FF) {
    try {
        const channel = await client.channels.fetch(channelId);

        const embed = new EmbedBuilder()
            .setTitle(title)
            .setDescription(description)
            .setColor(color)
            .setTimestamp();

        await channel.send({ embeds: [embed] });
    } catch (error) {
        console.error("Erreur dans sendMessage:", error);
    }
}

module.exports = { sendMessage };