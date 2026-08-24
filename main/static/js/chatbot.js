(function () {
  const state = { conversationId: null };

  function getCsrfToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : '';
  }

  function scrollToBottom(container) {
    if (container) container.scrollTop = container.scrollHeight;
  }

  function appendResourceLinks(container, resources, heading) {
    if (!container || !Array.isArray(resources) || !resources.length) return;

    const wrapper = document.createElement('div');
    wrapper.className = 'message-sources';

    const title = document.createElement('span');
    title.className = 'message-sources__title';
    title.textContent = heading;
    wrapper.appendChild(title);

    const list = document.createElement('ul');
    resources.slice(0, 3).forEach((resource) => {
      if (!resource || (!resource.url && !resource.title)) return;

      const item = document.createElement('li');
      const label = resource.title || resource.url;
      if (resource.url) {
        const link = document.createElement('a');
        link.className = 'message-source-link';
        link.href = resource.url;
        link.target = '_blank';
        link.rel = 'noopener noreferrer';
        link.textContent = label;
        item.appendChild(link);
      } else {
        const text = document.createElement('span');
        text.className = 'message-source-link';
        text.textContent = label;
        item.appendChild(text);
      }

      const location = resource.course || resource.category || '';
      const kind = resource.resource_type || '';
      const details = [location, kind].filter(Boolean).join(' | ');
      if (details) {
        const meta = document.createElement('span');
        meta.className = 'message-source-host';
        meta.textContent = details;
        item.appendChild(meta);
      }

      list.appendChild(item);
    });

    if (list.children.length) {
      wrapper.appendChild(list);
      container.appendChild(wrapper);
    }
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
      appendResourceLinks(loadingMsg, data.sources, 'Sources');
      const suggestedResources =
        Array.isArray(data.suggested_resources) && data.suggested_resources.length
          ? data.suggested_resources
          : data.local_resources;
      appendResourceLinks(
        loadingMsg,
        suggestedResources,
        'Suggested from your learning library'
      );
    } catch (err) {
      loadingMsg.classList.remove('is-loading');
      loadingMsg.classList.add('has-error');
      loadingMsg.textContent = err.message;
    } finally {
      scrollToBottom(botMessages);
    }
  };
})();
