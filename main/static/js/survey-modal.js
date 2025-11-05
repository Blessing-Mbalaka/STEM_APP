// survey-modal.js - Handles custom user survey modal experience.
(() => {
  const overlay = document.getElementById('surveyModal');
  if (!overlay) return;

  const modalTitle = document.getElementById('surveyModalTitle');
  const modalSubtitle = document.getElementById('surveyModalSubtitle');
  const promptBlock = document.getElementById('surveyPrompt');
  const consentBlock = document.getElementById('surveyConsent');
  const form = document.getElementById('surveyForm');
  const successBlock = document.getElementById('surveySuccess');
  const chartsContainer = document.getElementById('surveyCharts');
  const primaryBtn = document.getElementById('surveyPrimaryBtn');
  const laterBtn = document.getElementById('surveyLaterBtn');

  let currentSurvey = null;
  let participant = null;
  let chartInstances = [];
  let loading = false;
  let previewMode = false;

  const noop = () => {};

  function resetChartInstances() {
    if (!chartInstances.length) return;
    chartInstances.forEach((instance) => {
      try {
        instance.destroy();
      } catch (e) {
        console.warn('Unable to destroy chart instance', e);
      }
    });
    chartInstances = [];
  }

  function hideElement(el) {
    if (!el) return;
    el.style.display = 'none';
  }

  function showElement(el, display = 'block') {
    if (!el) return;
    el.style.display = display;
  }

  function setPrimaryAction(label, handler) {
    if (!primaryBtn) return;
    if (label === null) {
      hideElement(primaryBtn);
      primaryBtn.onclick = noop;
      return;
    }
    primaryBtn.textContent = label;
    showElement(primaryBtn, 'inline-flex');
    primaryBtn.onclick = handler;
  }

  function setLaterAction(label, handler) {
    if (!laterBtn) return;
    if (label === null) {
      hideElement(laterBtn);
      laterBtn.onclick = noop;
      return;
    }
    laterBtn.textContent = label;
    showElement(laterBtn, 'inline-flex');
    laterBtn.onclick = handler;
  }

  function closeModal() {
    overlay.classList.remove('active');
    overlay.setAttribute('aria-hidden', 'true');
    currentSurvey = null;
    participant = null;
    previewMode = false;
    form.reset();
    form.innerHTML = '';
    promptBlock.innerHTML = '';
    consentBlock.innerHTML = '';
    successBlock.innerHTML = '';
    chartsContainer.innerHTML = '';
    hideElement(consentBlock);
    hideElement(form);
    hideElement(successBlock);
    resetChartInstances();
  }

  function dismissSurvey() {
    if (!currentSurvey) {
      closeModal();
      return;
    }
    if (previewMode) {
      closeModal();
      return;
    }
    api(`/api/surveys/${currentSurvey.id}/participation/`, {
      method: 'POST',
      data: { action: 'dismiss' },
    }).catch((err) => {
      console.warn('Failed to dismiss survey', err);
    }).finally(() => {
      closeModal();
    });
  }

  async function ensureConsent() {
    if (!currentSurvey) return;
    if (previewMode) {
      participant = participant || { status: 'consented' };
      return;
    }
    if (participant && participant.status === 'consented') return;
    try {
      const res = await api(`/api/surveys/${currentSurvey.id}/participation/`, {
        method: 'POST',
        data: { action: 'consent' },
      });
      participant = res.participant;
    } catch (error) {
      console.warn('Unable to capture consent', error);
      throw error;
    }
  }

  function renderPrompt() {
    if (!currentSurvey) return;
    promptBlock.innerHTML = '';
    const intro = currentSurvey.introText || currentSurvey.description || 'We value your feedback. This short survey helps us tailor the experience.';
    const p = document.createElement('p');
    p.textContent = intro;
    promptBlock.appendChild(p);
    showElement(promptBlock);

    if (currentSurvey.requireConsent && currentSurvey.consentText) {
      consentBlock.textContent = currentSurvey.consentText;
      showElement(consentBlock);
    } else {
      hideElement(consentBlock);
    }

    hideElement(form);
    hideElement(successBlock);
    chartsContainer.innerHTML = '';
    setPrimaryAction('Start survey', startSurveyFlow);
    setLaterAction('Maybe later', dismissSurvey);
  }

  function createInfoBlock(question) {
    const wrapper = document.createElement('div');
    wrapper.className = 'survey-info-block';
    const label = document.createElement('strong');
    label.textContent = question.prompt;
    const body = document.createElement('p');
    body.textContent = question.helpText || '';
    wrapper.appendChild(label);
    if (question.helpText) wrapper.appendChild(body);
    return wrapper;
  }

  function createTextField(question) {
    const input = question.type === 'long-text'
      ? document.createElement('textarea')
      : document.createElement('input');
    if (question.type !== 'long-text') {
      input.type = 'text';
    }
    input.name = `question-${question.id}`;
    input.dataset.questionId = question.id;
    input.dataset.qtype = question.type;
    if (question.isRequired) {
      input.required = true;
    }
    return input;
  }

  function createNumberField(question) {
    const input = document.createElement('input');
    input.type = 'number';
    input.step = '0.1';
    input.name = `question-${question.id}`;
    input.dataset.questionId = question.id;
    input.dataset.qtype = question.type;
    if (question.isRequired) input.required = true;
    const cfg = question.config || {};
    if (cfg.min !== undefined) input.min = cfg.min;
    if (cfg.max !== undefined) input.max = cfg.max;
    return input;
  }

  function createScaleField(question) {
    const container = document.createElement('div');
    container.className = 'survey-scale-field';
    const input = document.createElement('input');
    input.type = 'range';
    input.name = `question-${question.id}`;
    input.dataset.questionId = question.id;
    input.dataset.qtype = question.type;

    const cfg = question.config || {};
    const min = Number(cfg.min ?? 1);
    const max = Number(cfg.max ?? 5);
    const step = Number(cfg.step ?? 1);

    input.min = min;
    input.max = max;
    input.step = step;
    input.value = cfg.default ?? Math.round((min + max) / 2);

    const output = document.createElement('div');
    output.style.marginTop = '4px';
    output.style.fontSize = '0.85rem';
    output.style.color = '#1f2937';
    output.textContent = `Selected: ${input.value}`;

    input.addEventListener('input', () => {
      output.textContent = `Selected: ${input.value}`;
    });

    if (question.isRequired) input.required = true;

    container.appendChild(input);
    container.appendChild(output);
    return container;
  }

  function createChoiceField(question) {
    const wrapper = document.createElement('div');
    wrapper.className = 'survey-choice-list';
    const options = (question.config && Array.isArray(question.config.options))
      ? question.config.options
      : [];

    const type = question.type === 'single-choice' ? 'radio' : 'checkbox';

    options.forEach((option, index) => {
      const row = document.createElement('div');
      row.className = 'survey-choice-item';
      const input = document.createElement('input');
      input.type = type;
      const value = option.value != null ? option.value : option.label || `option-${index}`;
      input.value = String(value);
      input.name = `question-${question.id}` + (type === 'checkbox' ? '[]' : '');
      input.dataset.questionId = question.id;
      input.dataset.qtype = question.type;
      if (question.isRequired && type === 'radio') {
        input.required = true;
      }
      const label = document.createElement('label');
      label.textContent = option.label || option.text || `Option ${index + 1}`;
      row.appendChild(input);
      row.appendChild(label);
      wrapper.appendChild(row);
    });
    return wrapper;
  }

  function buildQuestionBlock(question) {
    const block = document.createElement('div');
    block.className = 'question-block';
    block.dataset.questionId = question.id;
    block.dataset.qtype = question.type;
    block.dataset.required = String(question.isRequired);

    const label = document.createElement('label');
    label.htmlFor = `question-${question.id}`;
    label.textContent = question.prompt;
    if (question.isRequired) {
      label.innerHTML += ' <span style="color:#ef4444">*</span>';
    }

    block.appendChild(label);

    if (question.type === 'info') {
      block.appendChild(createInfoBlock(question));
      return block;
    }

    if (question.type === 'short-text' || question.type === 'long-text') {
      const field = createTextField(question);
      field.id = `question-${question.id}`;
      block.appendChild(field);
    } else if (question.type === 'single-choice' || question.type === 'multi-choice') {
      block.appendChild(createChoiceField(question));
    } else if (question.type === 'number' || question.type === 'rating') {
      const field = createNumberField(question);
      field.id = `question-${question.id}`;
      block.appendChild(field);
    } else if (question.type === 'scale') {
      const container = createScaleField(question);
      container.querySelector('input').id = `question-${question.id}`;
      block.appendChild(container);
    } else {
      const fallback = document.createElement('input');
      fallback.type = 'text';
      fallback.id = `question-${question.id}`;
      fallback.name = `question-${question.id}`;
      block.appendChild(fallback);
    }

    if (question.helpText) {
      const help = document.createElement('p');
      help.style.fontSize = '0.8rem';
      help.style.color = '#6b7280';
      help.style.marginTop = '4px';
      help.textContent = question.helpText;
      block.appendChild(help);
    }

    return block;
  }

  function renderForm() {
    if (!currentSurvey) return;
    form.innerHTML = '';
    const fragment = document.createDocumentFragment();
    currentSurvey.questions.forEach((question) => {
      fragment.appendChild(buildQuestionBlock(question));
    });

    const actions = document.createElement('div');
    actions.style.display = 'flex';
    actions.style.justifyContent = 'flex-end';
    actions.style.gap = '12px';
    actions.style.marginTop = '16px';

    const submitBtn = document.createElement('button');
    submitBtn.type = 'submit';
    submitBtn.className = 'btn btn-primary';
    submitBtn.textContent = 'Submit responses';

    actions.appendChild(submitBtn);
    fragment.appendChild(actions);

    form.appendChild(fragment);

    hideElement(promptBlock);
    hideElement(consentBlock);
    hideElement(successBlock);
    showElement(form);
    chartsContainer.innerHTML = '';
    setPrimaryAction(null, noop);
    setLaterAction('Cancel', dismissSurvey);
  }

  function extractAnswers() {
    const answers = {};
    const blocks = form.querySelectorAll('.question-block');
    blocks.forEach((block) => {
      const questionId = block.dataset.questionId;
      const qType = block.dataset.qtype;
      if (!questionId || qType === 'info') {
        return;
      }
      let value = null;
      if (qType === 'single-choice') {
        const checked = block.querySelector('input[type="radio"]:checked');
        value = checked ? checked.value : null;
      } else if (qType === 'multi-choice') {
        value = Array.from(block.querySelectorAll('input[type="checkbox"]:checked')).map((input) => input.value);
      } else if (qType === 'scale') {
        const input = block.querySelector('input[type="range"]');
        value = input ? input.value : null;
      } else if (qType === 'rating' || qType === 'number') {
        const input = block.querySelector('input[type="number"]');
        value = input ? input.value : null;
      } else {
        const input = block.querySelector('textarea, input');
        value = input ? input.value : null;
      }
      answers[questionId] = value;
    });
    return answers;
  }

  function renderError(details) {
    const error = document.createElement('div');
    error.style.background = 'rgba(239, 68, 68, 0.12)';
    error.style.color = '#b91c1c';
    error.style.border = '1px solid rgba(239, 68, 68, 0.3)';
    error.style.borderRadius = '12px';
    error.style.padding = '12px 14px';
    error.style.marginBottom = '16px';
    if (typeof details === 'string') {
      error.textContent = details;
    } else {
      error.innerHTML = '<strong>We need a bit more information:</strong>';
      const list = document.createElement('ul');
      list.style.margin = '8px 0 0';
      list.style.paddingLeft = '18px';
      Object.entries(details || {}).forEach(([key, message]) => {
        const item = document.createElement('li');
        item.textContent = message;
        list.appendChild(item);
      });
      error.appendChild(list);
    }
    const existing = form.querySelector('.survey-error');
    if (existing) existing.remove();
    error.className = 'survey-error';
    form.insertBefore(error, form.firstChild);
  }

  function clearError() {
    const existing = form.querySelector('.survey-error');
    if (existing) existing.remove();
  }

  function buildChart(chartConfig) {
    if (!chartConfig || !chartConfig.data) return null;
    const canvas = document.createElement('canvas');
    chartsContainer.appendChild(canvas);
    return loadChartLibrary().then(() => {
      const ctx = canvas.getContext('2d');
      const chart = new Chart(ctx, {
        type: chartConfig.type || 'bar',
        data: chartConfig.data,
        options: chartConfig.options || {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: 'bottom',
            },
          },
        },
      });
      chartInstances.push(chart);
    });
  }

  function renderSuccess(summary) {
    successBlock.innerHTML = '';
    chartsContainer.innerHTML = '';
    hideElement(form);
    showElement(successBlock);

    const title = document.createElement('h3');
    const outro = currentSurvey && currentSurvey.outroText
      ? currentSurvey.outroText
      : 'Thanks! Your input will help us improve the platform.';
    title.textContent = 'Thank you!';

    const message = document.createElement('p');
    message.textContent = outro;

    successBlock.appendChild(title);
    successBlock.appendChild(message);

    if (summary && Array.isArray(summary.questions) && summary.questions.length) {
      const chartsTitle = document.createElement('p');
      chartsTitle.style.fontWeight = '600';
      chartsTitle.style.marginBottom = '12px';
      chartsTitle.textContent = 'Your scored feedback';
      chartsContainer.appendChild(chartsTitle);

      const chartPromises = summary.questions
        .filter((entry) => entry.chart)
        .map((entry) => buildChart(entry.chart));

      if (chartPromises.length) {
        Promise.all(chartPromises).catch((err) => console.warn('Chart render error', err));
      }
    }

    setPrimaryAction('Close', closeModal);
    setLaterAction(null, noop);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (!currentSurvey || loading) return;
    clearError();
    loading = true;
    const answers = extractAnswers();
    try {
      const res = await api(`/api/surveys/${currentSurvey.id}/responses/`, {
        method: 'POST',
        data: { answers },
      });
      participant = res.participant;
      renderSuccess(res.scoreSummary || {});
    } catch (error) {
      if (error && error.json && error.json.details) {
        renderError(error.json.details);
      } else {
        renderError(error?.message || 'Unexpected error. Please try again.');
      }
    } finally {
      loading = false;
    }
  }

  async function startSurveyFlow() {
    if (loading) return;
    loading = true;
    try {
      await ensureConsent();
      renderForm();
    } catch (error) {
      renderError(error?.message || 'Unable to start the survey right now.');
    } finally {
      loading = false;
    }
  }

  function showModal(data) {
    currentSurvey = data.survey;
    participant = data.participant || null;
    modalTitle.textContent = currentSurvey.title || 'Help us improve';
    modalSubtitle.textContent = currentSurvey.description || 'Your insights keep the platform sharp.';
    renderPrompt();
    overlay.classList.add('active');
    overlay.setAttribute('aria-hidden', 'false');
  }

  async function fetchNextSurvey() {
    try {
      const data = await api('/api/surveys/next/');
      if (!data || !data.survey) return;
      showModal(data);
    } catch (error) {
      if (error && (error.status === 401 || error.status === 403)) {
        return;
      }
      console.warn('Survey fetch failed', error);
    }
  }

  function loadScript(src) {
    return new Promise((resolve, reject) => {
      const existing = document.querySelector(`script[src="${src}"]`);
      if (existing) {
        existing.addEventListener('load', () => resolve());
        existing.addEventListener('error', reject);
        if (existing.dataset.loaded === 'true') {
          resolve();
        }
        return;
      }
      const script = document.createElement('script');
      script.src = src;
      script.async = true;
      script.onload = () => {
        script.dataset.loaded = 'true';
        resolve();
      };
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }

  function loadChartLibrary() {
    if (window.Chart) {
      return Promise.resolve();
    }
    return loadScript('https://cdn.jsdelivr.net/npm/chart.js');
  }

  function onKeyDown(event) {
    if (event.key === 'Escape' && overlay.classList.contains('active')) {
      dismissSurvey();
    }
  }

  function init() {
    if (!overlay) return;
    form.addEventListener('submit', handleSubmit);
    laterBtn.onclick = dismissSurvey;
    primaryBtn.onclick = startSurveyFlow;
    document.addEventListener('keydown', onKeyDown);
    fetchNextSurvey();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();
