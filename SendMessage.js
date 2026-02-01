const { EmbedBuilder } = require('discord.js');

async function sendMessage(client, targetId, title, description, color = 0x0099FF) {
    try {
        let target;

        try {
            target = await client.users.fetch(targetId);
        } catch (e) {
            target = await client.channels.fetch(targetId);
        }

        if (!target) {
            console.error(`❌ Impossible de trouver la cible : ${targetId}`);
            return;
        }

        const embed = new EmbedBuilder()
            .setTitle(title)
            .setDescription(description)
            .setColor(color)
            .setTimestamp();

        await target.send({ embeds: [embed] });
    } catch (error) {
        console.error("Erreur dans sendMessage:", error);
    }
}

module.exports = { sendMessage };