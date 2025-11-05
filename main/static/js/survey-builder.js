// survey-builder.js - Admin survey builder experience.
(() => {
  const state = {
    surveys: [],
    current: null,
    questions: [],
    editingQuestion: null,
  };

  const els = {
    surveyList: document.getElementById('surveyList'),
    surveysEmpty: document.getElementById('surveysEmpty'),
    surveyStats: document.getElementById('surveyStats'),
    builderTitle: document.getElementById('builderTitle'),
    builderIntro: document.getElementById('builderIntro'),
    builderActions: document.getElementById('builderActions'),
    surveyForm: document.getElementById('surveyForm'),
    surveyTitle: document.getElementById('surveyTitle'),
    surveyDescription: document.getElementById('surveyDescription'),
    surveyIntro: document.getElementById('surveyIntro'),
    surveyOutro: document.getElementById('surveyOutro'),
    surveyConsent: document.getElementById('surveyConsent'),
    surveyRequireConsent: document.getElementById('surveyRequireConsent'),
    surveyActive: document.getElementById('surveyActive'),
    surveyRoles: document.getElementById('surveyRoles'),
    surveyRemind: document.getElementById('surveyRemind'),
    surveySlug: document.getElementById('surveySlug'),
    resetSurveyBtn: document.getElementById('resetSurveyBtn'),
    saveSurveyBtn: document.getElementById('saveSurveyBtn'),
    createSurveyBtn: document.getElementById('createSurveyBtn'),
    deleteSurveyBtn: document.getElementById('deleteSurveyBtn'),
    duplicateSurveyBtn: document.getElementById('duplicateSurveyBtn'),
    questionsPanel: document.getElementById('questionsPanel'),
    questionsEmpty: document.getElementById('questionsEmpty'),
    questionsList: document.getElementById('questionsList'),
    addQuestionBtn: document.getElementById('addQuestionBtn'),
    questionEditor: document.getElementById('questionEditor'),
    questionForm: document.getElementById('questionForm'),
    questionPrompt: document.getElementById('questionPrompt'),
    questionHelp: document.getElementById('questionHelp'),
    questionType: document.getElementById('questionType'),
    questionChart: document.getElementById('questionChart'),
    questionRequired: document.getElementById('questionRequired'),
    questionScored: document.getElementById('questionScored'),
    questionMaxScore: document.getElementById('questionMaxScore'),
    questionOrder: document.getElementById('questionOrder'),
    questionOptionsSection: document.getElementById('questionOptionsSection'),
    questionOptions: document.getElementById('questionOptions'),
    addOptionBtn: document.getElementById('addOptionBtn'),
    questionScaleSection: document.getElementById('questionScaleSection'),
    scaleMin: document.getElementById('scaleMin'),
    scaleMax: document.getElementById('scaleMax'),
    scaleStep: document.getElementById('scaleStep'),
    cancelQuestionBtn: document.getElementById('cancelQuestionBtn'),
    saveQuestionBtn: document.getElementById('saveQuestionBtn'),
    questionAlert: document.getElementById('questionAlert'),
    optionTemplate: document.getElementById('optionTemplate'),
  };

  function handleError(err, fallback = 'Something went wrong.') {
    console.error(err);
    const message = (err && err.json && err.json.error) || err?.message || fallback;
    alert(message);
  }

  function parseRoles(value) {
    if (!value) return [];
    return value
      .split(',')
      .map((item) => item.trim().toLowerCase())
      .filter(Boolean);
  }

  function hydrateSurveyForm() {
    const survey = state.current;
    if (!survey) return;
    els.surveyTitle.value = survey.title || '';
    els.surveyDescription.value = survey.description || '';
    els.surveyIntro.value = survey.introText || '';
    els.surveyOutro.value = survey.outroText || '';
    els.surveyConsent.value = survey.consentText || '';
    els.surveyRequireConsent.checked = Boolean(survey.requireConsent);
    els.surveyActive.checked = Boolean(survey.isActive);
    els.surveyRoles.value = (survey.targetRoles || []).join(', ');
    const remind = (survey.displayRules && survey.displayRules.remind_after_hours) || 24;
    els.surveyRemind.value = remind;
    els.surveySlug.value = survey.slug || '';

    if (survey.participantCounts) {
      const { total = 0, completed = 0, pending = 0 } = survey.participantCounts;
      els.surveyStats.innerHTML = `
        <div><strong>Total participants:</strong> ${total}</div>
        <div><strong>Completed:</strong> ${completed}</div>
        <div><strong>Pending:</strong> ${pending}</div>
      `;
    } else {
      els.surveyStats.innerHTML = 'No participation data yet.';
    }
  }

  function gatherSurveyPayload() {
    const displayRules = {};
    const remind = parseInt(els.surveyRemind.value, 10);
    if (!Number.isNaN(remind) && remind > 0) {
      displayRules.remind_after_hours = remind;
    }
    return {
      title: els.surveyTitle.value.trim(),
      description: els.surveyDescription.value.trim(),
      introText: els.surveyIntro.value.trim(),
      outroText: els.surveyOutro.value.trim(),
      consentText: els.surveyConsent.value.trim(),
      requireConsent: els.surveyRequireConsent.checked,
      isActive: els.surveyActive.checked,
      targetRoles: parseRoles(els.surveyRoles.value),
      displayRules,
    };
  }

  function renderSurveyList() {
    const surveys = state.surveys;
    if (!surveys.length) {
      showElement(els.surveysEmpty);
      els.surveyList.innerHTML = '';
      return;
    }
    hideElement(els.surveysEmpty);
    els.surveyList.innerHTML = '';
    const frag = document.createDocumentFragment();
    surveys.forEach((survey) => {
      const pill = document.createElement('div');
      pill.className = 'survey-pill';
      if (state.current && survey.id === state.current.id) {
        pill.classList.add('active');
      }
      const title = document.createElement('h3');
      title.textContent = survey.title || 'Untitled survey';
      const meta = document.createElement('span');
      meta.textContent = survey.isActive ? 'Active' : 'Draft';
      meta.className = 'pill';
      pill.appendChild(title);
      pill.appendChild(meta);
      pill.addEventListener('click', () => selectSurvey(survey.id));
      frag.appendChild(pill);
    });
    els.surveyList.appendChild(frag);
  }

  function clearQuestionEditor() {
    state.editingQuestion = null;
    els.questionForm.dataset.mode = 'create';
    els.questionForm.dataset.questionId = '';
    els.questionPrompt.value = '';
    els.questionHelp.value = '';
    els.questionType.value = 'short-text';
    els.questionChart.value = '';
    els.questionRequired.checked = true;
    els.questionScored.checked = false;
    els.questionMaxScore.value = '0';
    els.questionOrder.value = state.questions.length + 1;
    els.questionOptions.innerHTML = '';
    els.scaleMin.value = '1';
    els.scaleMax.value = '5';
    els.scaleStep.value = '1';
    hideElement(els.questionAlert);
    refreshQuestionEditorVisibility();
  }

  function refreshQuestionEditorVisibility() {
    const type = els.questionType.value;
    if (type === 'single-choice' || type === 'multi-choice') {
      showElement(els.questionOptionsSection);
      if (!els.questionOptions.childElementCount) {
        appendOptionRow();
      }
    } else {
      hideElement(els.questionOptionsSection);
    }

    if (type === 'scale' || type === 'rating') {
      showElement(els.questionScaleSection);
    } else {
      hideElement(els.questionScaleSection);
    }
  }

  function showQuestionEditor(question = null) {
    if (question) {
      state.editingQuestion = question;
      els.questionForm.dataset.mode = 'edit';
      els.questionForm.dataset.questionId = question.id;
      els.questionPrompt.value = question.prompt || '';
      els.questionHelp.value = question.helpText || '';
      els.questionType.value = question.type;
      els.questionChart.value = question.chartType || '';
      els.questionRequired.checked = Boolean(question.isRequired);
      els.questionScored.checked = Boolean(question.isScored);
      els.questionMaxScore.value = question.maxScore ?? 0;
      els.questionOrder.value = question.order || 1;

      const cfg = question.config || {};
      els.questionOptions.innerHTML = '';
      if (Array.isArray(cfg.options)) {
        cfg.options.forEach((opt) => appendOptionRow(opt.label || opt.text || '', opt.value, opt.score));
      }
      if (cfg.min !== undefined) els.scaleMin.value = cfg.min;
      if (cfg.max !== undefined) els.scaleMax.value = cfg.max;
      if (cfg.step !== undefined) els.scaleStep.value = cfg.step;
    } else {
      clearQuestionEditor();
    }
    refreshQuestionEditorVisibility();
    showElement(els.questionEditor);
  }

  function hideQuestionEditor() {
    hideElement(els.questionEditor);
    clearQuestionEditor();
  }

  function appendOptionRow(label = '', value = '', score = '') {
    const tpl = els.optionTemplate.content.cloneNode(true);
    const row = tpl.querySelector('.option-row');
    const labelInput = row.querySelector('.option-label');
    const valueInput = row.querySelector('.option-value');
    const scoreInput = row.querySelector('.option-score');
    labelInput.value = label;
    valueInput.value = value || label.toLowerCase().replace(/\s+/g, '-');
    scoreInput.value = score;
    row.querySelector('.remove-option').addEventListener('click', () => {
      row.remove();
    });
    els.questionOptions.appendChild(row);
  }

  function gatherQuestionPayload() {
    const type = els.questionType.value;
    const config = {};
    if (type === 'single-choice' || type === 'multi-choice') {
      const rows = els.questionOptions.querySelectorAll('.option-row');
      const options = [];
      rows.forEach((row) => {
        const label = row.querySelector('.option-label').value.trim();
        const value = row.querySelector('.option-value').value.trim();
        const scoreRaw = row.querySelector('.option-score').value;
        if (!label) return;
        const option = { label, value: value || label.toLowerCase().replace(/\s+/g, '-') };
        if (scoreRaw !== '') {
          option.score = parseFloat(scoreRaw) || 0;
        }
        options.push(option);
      });
      config.options = options;
    }
    if (type === 'scale' || type === 'rating') {
      config.min = parseFloat(els.scaleMin.value) || 0;
      config.max = parseFloat(els.scaleMax.value) || 5;
      config.step = parseFloat(els.scaleStep.value) || 1;
    }

    return {
      prompt: els.questionPrompt.value.trim(),
      helpText: els.questionHelp.value.trim(),
      type,
      chartType: els.questionChart.value,
      isRequired: els.questionRequired.checked,
      isScored: els.questionScored.checked,
      maxScore: parseFloat(els.questionMaxScore.value) || 0,
      order: parseInt(els.questionOrder.value, 10) || state.questions.length + 1,
      config,
    };
  }

  function renderQuestions() {
    const questions = state.questions || [];
    if (!questions.length) {
      showElement(els.questionsEmpty);
      els.questionsList.innerHTML = '';
      return;
    }
    hideElement(els.questionsEmpty);
    els.questionsList.innerHTML = '';
    const frag = document.createDocumentFragment();
    questions.forEach((question, index) => {
      const card = document.createElement('div');
      card.className = 'question-card';

      const header = document.createElement('header');
      const title = document.createElement('h4');
      title.textContent = `${question.order}. ${question.prompt || 'Untitled question'}`;
      header.appendChild(title);

      const actions = document.createElement('div');
      actions.className = 'question-actions';

      const editBtn = document.createElement('button');
      editBtn.className = 'btn secondary';
      editBtn.type = 'button';
      editBtn.textContent = 'Edit';
      editBtn.addEventListener('click', () => showQuestionEditor(question));

      const deleteBtn = document.createElement('button');
      deleteBtn.className = 'btn danger';
      deleteBtn.type = 'button';
      deleteBtn.textContent = 'Delete';
      deleteBtn.addEventListener('click', () => deleteQuestion(question));

      const moveUpBtn = document.createElement('button');
      moveUpBtn.className = 'btn secondary';
      moveUpBtn.type = 'button';
      moveUpBtn.textContent = 'Move up';
      moveUpBtn.disabled = index === 0;
      moveUpBtn.addEventListener('click', () => moveQuestion(question, -1));

      const moveDownBtn = document.createElement('button');
      moveDownBtn.className = 'btn secondary';
      moveDownBtn.type = 'button';
      moveDownBtn.textContent = 'Move down';
      moveDownBtn.disabled = index === questions.length - 1;
      moveDownBtn.addEventListener('click', () => moveQuestion(question, 1));

      actions.appendChild(moveUpBtn);
      actions.appendChild(moveDownBtn);
      actions.appendChild(editBtn);
      actions.appendChild(deleteBtn);

      header.appendChild(actions);
      card.appendChild(header);

      const meta = document.createElement('div');
      meta.className = 'question-meta';
      meta.innerHTML = `
        <span class="pill">${question.type}</span>
        <span>${question.isRequired ? 'Required' : 'Optional'}</span>
        ${question.isScored ? `<span>Max score: ${question.maxScore}</span>` : ''}
      `;
      card.appendChild(meta);

      if (question.helpText) {
        const help = document.createElement('p');
        help.style.marginTop = '8px';
        help.style.color = '#4b5563';
        help.textContent = question.helpText;
        card.appendChild(help);
      }

      frag.appendChild(card);
    });
    els.questionsList.appendChild(frag);
  }

  async function loadSurveys() {
    try {
      const res = await api('/api/surveys/');
      state.surveys = res.results || [];
      renderSurveyList();
    } catch (err) {
      handleError(err, 'Unable to load surveys.');
    }
  }

  async function selectSurvey(id) {
    try {
      const res = await api(`/api/surveys/${id}/`);
      state.current = res.survey;
      state.questions = (res.survey && res.survey.questions) || [];
      renderSurveyList();
      showElement(els.surveyForm);
      hideElement(els.builderIntro);
      showElement(els.builderActions);
      showElement(els.questionsPanel);
      hydrateSurveyForm();
      renderQuestions();
      hideQuestionEditor();
      els.builderTitle.textContent = `Survey: ${state.current.title || 'Untitled'}`;
    } catch (err) {
      handleError(err, 'Unable to load survey details.');
    }
  }

  async function saveSurvey(event) {
    event.preventDefault();
    if (!state.current) return;
    const payload = gatherSurveyPayload();
    if (!payload.title) {
      alert('Title is required.');
      return;
    }
    try {
      const res = await api(`/api/surveys/${state.current.id}/`, {
        method: 'PATCH',
        data: payload,
      });
      state.current = res.survey;
      state.questions = res.survey.questions || state.questions;
      await loadSurveys();
      hydrateSurveyForm();
      alert('Survey saved.');
    } catch (err) {
      handleError(err, 'Unable to save survey.');
    }
  }

  async function createSurvey() {
    const defaultTitle = prompt('Survey title', 'New custom survey');
    if (defaultTitle === null) return;
    const payload = {
      title: defaultTitle.trim() || 'Untitled survey',
      description: '',
      introText: '',
      outroText: '',
      consentText: '',
      requireConsent: true,
      isActive: false,
      targetRoles: [],
      displayRules: { remind_after_hours: 24 },
    };
    try {
      const res = await api('/api/surveys/', {
        method: 'POST',
        data: payload,
      });
      await loadSurveys();
      selectSurvey(res.survey.id);
    } catch (err) {
      handleError(err, 'Unable to create survey.');
    }
  }

  async function deleteSurvey() {
    if (!state.current) return;
    const confirmed = confirm('Delete this survey? This cannot be undone.');
    if (!confirmed) return;
    try {
      await api(`/api/surveys/${state.current.id}/`, { method: 'DELETE' });
      state.current = null;
      state.questions = [];
      hideQuestionEditor();
      els.surveyForm.reset();
      hideElement(els.surveyForm);
      hideElement(els.builderActions);
      showElement(els.builderIntro);
      hideElement(els.questionsPanel);
      els.surveyStats.innerHTML = 'Select a survey to see metrics.';
      await loadSurveys();
    } catch (err) {
      handleError(err, 'Unable to delete survey.');
    }
  }

  async function duplicateSurvey() {
    if (!state.current) return;
    const base = state.current;
    const payload = {
      title: `${base.title || 'Untitled survey'} (copy)`,
      description: base.description || '',
      introText: base.introText || '',
      outroText: base.outroText || '',
      consentText: base.consentText || '',
      requireConsent: base.requireConsent,
      isActive: false,
      targetRoles: base.targetRoles || [],
      displayRules: base.displayRules || { remind_after_hours: 24 },
    };
    try {
      const res = await api('/api/surveys/', { method: 'POST', data: payload });
      const newSurvey = res.survey;
      for (const question of state.questions) {
        await api(`/api/surveys/${newSurvey.id}/questions/`, {
          method: 'POST',
          data: {
            prompt: question.prompt,
            helpText: question.helpText,
            type: question.type,
            chartType: question.chartType,
            isRequired: question.isRequired,
            isScored: question.isScored,
            maxScore: question.maxScore,
            order: question.order,
            config: question.config || {},
          },
        });
      }
      await loadSurveys();
      selectSurvey(newSurvey.id);
      alert('Survey duplicated.');
    } catch (err) {
      handleError(err, 'Unable to duplicate survey.');
    }
  }

  async function saveQuestion(event) {
    event.preventDefault();
    if (!state.current) return;
    const payload = gatherQuestionPayload();
    if (!payload.prompt) {
      showQuestionAlert('Question prompt is required.');
      return;
    }
    try {
      if (state.editingQuestion) {
        await api(`/api/surveys/${state.current.id}/questions/${state.editingQuestion.id}/`, {
          method: 'PATCH',
          data: payload,
        });
      } else {
        await api(`/api/surveys/${state.current.id}/questions/`, {
          method: 'POST',
          data: payload,
        });
      }
      hideQuestionEditor();
      await refreshSurveyDetail();
    } catch (err) {
      handleError(err, 'Unable to save question.');
    }
  }

  function showQuestionAlert(message) {
    els.questionAlert.textContent = message;
    showElement(els.questionAlert);
  }

  async function deleteQuestion(question) {
    if (!state.current) return;
    const confirmDelete = confirm('Remove this question?');
    if (!confirmDelete) return;
    try {
      await api(`/api/surveys/${state.current.id}/questions/${question.id}/`, {
        method: 'DELETE',
      });
      await refreshSurveyDetail();
    } catch (err) {
      handleError(err, 'Unable to delete question.');
    }
  }

  async function moveQuestion(question, direction) {
    if (!state.current) return;
    const newOrder = question.order + direction;
    if (newOrder < 1) return;
    try {
      await api(`/api/surveys/${state.current.id}/questions/${question.id}/`, {
        method: 'PATCH',
        data: { order: newOrder },
      });
      await refreshSurveyDetail();
    } catch (err) {
      handleError(err, 'Unable to reorder question.');
    }
  }

  async function refreshSurveyDetail() {
    if (!state.current) return;
    try {
      const res = await api(`/api/surveys/${state.current.id}/`);
      state.current = res.survey;
      state.questions = res.survey.questions || [];
      hydrateSurveyForm();
      renderQuestions();
    } catch (err) {
      handleError(err, 'Unable to refresh survey.');
    }
  }

  function hideElement(el) {
    if (!el) return;
    el.style.display = 'none';
  }

  function showElement(el, display = 'block') {
    if (!el) return;
    el.style.display = display;
  }

  function initEvents() {
    if (els.surveyForm) {
      els.surveyForm.addEventListener('submit', saveSurvey);
    }
    if (els.resetSurveyBtn) {
      els.resetSurveyBtn.addEventListener('click', hydrateSurveyForm);
    }
    if (els.createSurveyBtn) {
      els.createSurveyBtn.addEventListener('click', createSurvey);
    }
    if (els.deleteSurveyBtn) {
      els.deleteSurveyBtn.addEventListener('click', deleteSurvey);
    }
    if (els.duplicateSurveyBtn) {
      els.duplicateSurveyBtn.addEventListener('click', duplicateSurvey);
    }
    if (els.addQuestionBtn) {
      els.addQuestionBtn.addEventListener('click', () => showQuestionEditor());
    }
    if (els.questionType) {
      els.questionType.addEventListener('change', refreshQuestionEditorVisibility);
    }
    if (els.addOptionBtn) {
      els.addOptionBtn.addEventListener('click', () => appendOptionRow());
    }
    if (els.cancelQuestionBtn) {
      els.cancelQuestionBtn.addEventListener('click', hideQuestionEditor);
    }
    if (els.questionForm) {
      els.questionForm.addEventListener('submit', saveQuestion);
    }
  }

  function init() {
    initEvents();
    loadSurveys();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init, { once: true });
  } else {
    init();
  }
})();
