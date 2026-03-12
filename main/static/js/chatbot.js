(function () {
  const state = { conversationId: null };

  function getCsrfToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : '';
  }

  function scrollToBottom(container) {
    if (container) container.scrollTop = container.scrollHeight;
  }

  window.getBotResponse = async function (message) {
    const res = await fetch('/api/chatbot/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken(),
      },
      body: JSON.stringify({
        question: message,
        conversation_id: state.conversationId,
      }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || 'Failed to get response');
    if (data.conversation_id) state.conversationId = data.conversation_id;
    return data;
  };

  window.sendBotMessage = async function () {
    const message = botInput.value.trim();
    if (!message) return;

    const userMsg = document.createElement('div');
    userMsg.className = 'message user-message';
    userMsg.textContent = message;
    botMessages.appendChild(userMsg);
    botInput.value = '';
    scrollToBottom(botMessages);

    const loadingMsg = document.createElement('div');
    loadingMsg.className = 'message bot-message is-loading';
    loadingMsg.textContent = 'Thinking...';
    botMessages.appendChild(loadingMsg);

    try {
      const data = await window.getBotResponse(message);
      loadingMsg.classList.remove('is-loading');
      loadingMsg.textContent = data.response || 'I\'m here to help!';
    } catch (err) {
      loadingMsg.classList.remove('is-loading');
      loadingMsg.classList.add('has-error');
      loadingMsg.textContent = err.message;
    } finally {
      scrollToBottom(botMessages);
    }
  };
})();