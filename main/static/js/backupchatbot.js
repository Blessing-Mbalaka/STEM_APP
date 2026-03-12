(function () {
  const state = (window.chatbotState = window.chatbotState || { conversationId: null });
  if (!('pendingSearchQuery' in state)) {
    state.pendingSearchQuery = null;
  }

  function getCsrfToken() {
    if (typeof window.csrftoken === 'string') {
      return window.csrftoken;
    }
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : '';
  }

  function scrollToBottom(container) {
    if (!container) return;
    container.scrollTop = container.scrollHeight;
  }

  function appendSources(container, sources, heading = 'Sources') {
    if (!Array.isArray(sources) || !sources.length) {
      return;
    }
    const wrapper = document.createElement('div');
    wrapper.className = 'message-sources';

    const title = document.createElement('span');
    title.className = 'message-sources__title';
    title.textContent = heading;
    wrapper.appendChild(title);

    const list = document.createElement('ul');
    sources.forEach((source) => {
      const item = document.createElement('li');
      if (source && source.url) {
        const link = document.createElement('a');
        link.className = 'message-source-link';
        link.href = source.url;
        link.target = '_blank';
        link.rel = 'noopener';
        link.textContent = source.title || source.url;
        item.appendChild(link);
        try {
          const parsed = new URL(source.url);
          const host = parsed.hostname.replace(/^www\./, '');
          if (!source.title && host) {
            link.textContent = host;
          }
          if (host) {
            const hostLabel = document.createElement('span');
            hostLabel.className = 'message-source-host';
            hostLabel.textContent = host;
            item.appendChild(hostLabel);
          }
        } catch (e) {
          // ignore invalid URL
        }
      } else if (source && source.title) {
        const titleOnly = document.createElement('span');
        titleOnly.className = 'message-source-link';
        titleOnly.textContent = source.title;
        item.appendChild(titleOnly);
      } else if (typeof source === 'string') {
        const textOnly = document.createElement('span');
        textOnly.className = 'message-source-link';
        textOnly.textContent = source;
        item.appendChild(textOnly);
      }

      if (source && source.excerpt) {
        const excerpt = document.createElement('div');
        excerpt.className = 'message-source-excerpt';
        excerpt.textContent = source.excerpt;
        item.appendChild(excerpt);
      }

      list.appendChild(item);
    });

    wrapper.appendChild(list);
    container.appendChild(wrapper);
  }

  async function requestInternetSearch(query, conversationId) {
    const body = { query };
    if (conversationId) {
      body.conversation_id = conversationId;
    }

    const res = await fetch('/api/chatbot/search/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken(),
      },
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data.error || 'Unable to search the internet right now.');
    }
    return data;
  }

  window.getBotResponse = async function (message, options = {}) {
    const payload = {
      question: message,
      conversation_id: state.conversationId,
    };
    if (options && options.model) {
      payload.model = options.model;
    }
    const res = await fetch('/api/chatbot/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCsrfToken(),
      },
      body: JSON.stringify(payload),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      throw new Error(data.error || data.response || res.statusText || 'Chatbot model not yet running');
    }
    if (data.conversation_id) {
      state.conversationId = data.conversation_id;
    }
    return data;
  };

  window.sendBotMessage = async function () {
    if (typeof botInput === 'undefined' || typeof botMessages === 'undefined') {
      console.warn('Chatbot UI elements are not available on this page.');
      return;
    }

    const message = botInput.value.trim();
    if (!message) return;

    const normalized = message.toLowerCase();
    if (state.pendingSearchQuery && /^(yes|y|sure|ok|please|search)/.test(normalized)) {
      const userMessage = document.createElement('div');
      userMessage.className = 'message user-message';
      userMessage.textContent = message;
      botMessages.appendChild(userMessage);
      botInput.value = '';
      scrollToBottom(botMessages);

      const query = state.pendingSearchQuery;
      state.pendingSearchQuery = null;
      await (async () => {
        const loadingMsg = document.createElement('div');
        loadingMsg.className = 'message bot-message is-loading';
        loadingMsg.textContent = 'Searching...';
        botMessages.appendChild(loadingMsg);
        scrollToBottom(botMessages);
        try {
          const searchData = await requestInternetSearch(query, state.conversationId);
          loadingMsg.classList.remove('is-loading');
          loadingMsg.textContent = searchData.response || 'Here is what I found online.';
          if (Array.isArray(searchData.sources) && searchData.sources.length) {
            appendSources(loadingMsg, searchData.sources);
          }
          if (Array.isArray(searchData.local_resources) && searchData.local_resources.length) {
            appendSources(loadingMsg, searchData.local_resources, 'Campus resources to review');
          }
          if (searchData.conversation_id) {
            state.conversationId = searchData.conversation_id;
          }
        } catch (error) {
          loadingMsg.classList.remove('is-loading');
          loadingMsg.classList.add('has-error');
          loadingMsg.textContent = error.message || 'Internet search failed.';
        } finally {
          scrollToBottom(botMessages);
        }
      })();
    } else {
      // Regular message handling
      const userMessage = document.createElement('div');
      userMessage.className = 'message user-message';
      userMessage.textContent = message;
      botMessages.appendChild(userMessage);
      botInput.value = '';
      scrollToBottom(botMessages);

      const loadingMsg = document.createElement('div');
      loadingMsg.className = 'message bot-message is-loading';
      loadingMsg.textContent = 'Thinking...';
      botMessages.appendChild(loadingMsg);
      scrollToBottom(botMessages);

      try {
        const responseData = await window.getBotResponse(message);
        loadingMsg.classList.remove('is-loading');
        loadingMsg.textContent = responseData.response || 'I\'m here to help!';
        if (Array.isArray(responseData.sources) && responseData.sources.length) {
          appendSources(loadingMsg, responseData.sources);
        }
      } catch (error) {
        loadingMsg.classList.remove('is-loading');
        loadingMsg.classList.add('has-error');
        loadingMsg.textContent = error.message || 'Failed to get response. Please try again.';
      } finally {
        scrollToBottom(botMessages);
      }
    }
  };
})();
