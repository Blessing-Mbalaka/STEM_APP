window.getBotResponse = async function(message, model) {
    try {
        const res = await fetch('/api/chatbot/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(Object.assign({ prompt: message }, model ? { model } : {}))
        });
        const data = await res.json().catch(() => ({}));
        if (!res.ok) {
            throw new Error(data.error || data.response || res.statusText || 'Chatbot model not yet running');
        }
        return data.response || data.error || "Sorry, I couldn't get an answer.";
    } catch (e) {
        return e.message || "Chatbot model not yet running. Please ask your admin to deploy it.";
    }
};

window.sendBotMessage = async function() {
    const message = botInput.value.trim();
    if (!message) return;

    const userMessage = document.createElement('div');
    userMessage.className = 'message user-message';
    userMessage.textContent = message;
    botMessages.appendChild(userMessage);
    botInput.value = '';
    botMessages.scrollTop = botMessages.scrollHeight;

    // Show loading message
    const loadingMsg = document.createElement('div');
    loadingMsg.className = 'message bot-message';
    loadingMsg.textContent = "Thinking...";
    botMessages.appendChild(loadingMsg);
    botMessages.scrollTop = botMessages.scrollHeight;

    // Get response from backend
    const botResponse = await window.getBotResponse(message);
    loadingMsg.textContent = botResponse;
};