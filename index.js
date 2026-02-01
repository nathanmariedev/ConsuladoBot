require('dotenv').config();
const { Client, GatewayIntentBits } = require('discord.js');
const {checkNewSlots} = require("./ConsuladoAPI");
const {sendMessage} = require("./SendMessage");

const vert = "\x1b[32m"
const orange = "\x1b[33m"
const reset = "\x1b[0m"

const channelId = process.env.CHANNEL_ID;

const client = new Client({
    intents: [
        GatewayIntentBits.Guilds,
        GatewayIntentBits.GuildMessages,
        GatewayIntentBits.MessageContent
    ]
});

client.on('messageCreate', (message) => {
    if (message.author.bot) return;

    if (message.content === '!ping') {
        message.reply('🏓 Pong !');
    }
});

console.log("Token is : ", process.env.TOKEN)

client.login(process.env.TOKEN);


const callEveryMinute = process.env.CALL_EVERY_MINUTES

async function startLoop() {

    if (client.isReady()) {

        await checkNewSlots(client);
    }

    setTimeout(startLoop, callEveryMinute * 60 * 1000);
}

client.once('ready', () => {
    console.log(vert + `Connecté en tant que ${client.user.tag} ! 🚀` + reset);
    sendMessage(client, channelId, "🤖 Bot Démarré", "Le bot de surveillance des créneaux est maintenant en ligne !");
    startLoop();
});
