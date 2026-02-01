const { sendMessage } = require('./SendMessage');

async function callApi() {
    let url = process.env.BOOKING_URL
    let parameters = {
        group_id : 124718,
        "appointments[0][intervention_id]" : 2422111,
        time_format : "datetime",
        apikey : process.env.API_KEY
    }
    const queryString = new URLSearchParams(parameters).toString();
    url += "?" + queryString;

    try {
        let response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        let data = await response.json();
        return data;
    } catch (error) {
        console.error("Erreur dans callApi:", error);
        return null;
    }
}

function formatSlots(apiData) {
    const slots = apiData.availabletimeslots;
    const days = {};

    // 1. On groupe par date (YYYY-MM-DD)
    slots.forEach(s => {
        const datePart = s.start.split(' ')[0]; // Récupère "2026-02-10"
        const timePart = s.start.split(' ')[1].substring(0, 5); // Récupère "09:15"

        if (!days[datePart]) days[datePart] = [];
        days[datePart].push(timePart);
    });

    // 2. On prépare le texte pour l'Embed
    let description = "";
    for (const [date, times] of Object.entries(days)) {
        description += `**📅 ${date}**\n\`${times.join('` `')}\`\n\n`;
    }

    return description || "Aucun créneau disponible.";
}

function formatNewSlots(newSlots) {
    return newSlots.map(s => {
        // Transforme "2026-02-10 09:15:00" en un format plus lisible
        return `✅ **${s.start.split(' ')[0]}** à **${s.start.split(' ')[1].substring(0, 5)}**`;
    }).join('\n');
}

let knownSlots = new Set(); // On stocke les IDs des créneaux ici

async function checkNewSlots(client) {
    try {
        const data = await callApi();
        if (!data || !data.availabletimeslots) return;

        const currentSlots = data.availabletimeslots;

        // On cherche les nouveaux créneaux (ceux qui ne sont pas dans knownSlots)
        const newSlots = currentSlots.filter(s => !knownSlots.has(s.slot));

        if (newSlots.length > 0) {
            console.log(`${newSlots.length} nouveau(x) créneau(x) trouvé(s) !`);

            // On prépare le message uniquement avec les NOUVEAUX
            const messageContent = formatNewSlots(newSlots);

            sendMessage(
                client,
                process.env.CHANNEL_ID,
                '🚨 NOUVEAU CRÉNEAU DISPONIBLE !',
                messageContent,
                0xffa500 // Orange pour l'alerte
            );

            // On ajoute les nouveaux créneaux à la liste des connus
            newSlots.forEach(s => knownSlots.add(s.slot));
        }

        // OPTIONNEL : On nettoie knownSlots pour ne pas garder les vieux créneaux disparus
        const currentIds = new Set(currentSlots.map(s => s.slot));
        knownSlots = currentIds;

    } catch (error) {
        console.error("Erreur lors de la vérification :", error);
    }
}

module.exports = { callApi, formatSlots, checkNewSlots, formatNewSlots };