const projectSelect = document.getElementById('projectSelect');
const sessionSelect = document.getElementById('sessionSelect');
const sessionCountEl = document.getElementById('sessionCount');
const logList = document.getElementById('logList');
const emptyHint = document.getElementById('emptyHint');
const explainEmptyHint = document.getElementById('explainEmptyHint');
const explainPane = document.getElementById('explainPane');
const explainMeta = document.getElementById('explainMeta');
const ruleSummary = document.getElementById('ruleSummary');
const modelStatus = document.getElementById('modelStatus');
const modelExplainText = document.getElementById('modelExplainText');
const jsonPreview = document.getElementById('jsonPreview');
const jsonToggleBtn = document.getElementById('jsonToggleBtn');
const explainGotoSettingsHint = document.getElementById('explainGotoSettingsHint');
const explainGotoSettingsBtn = document.getElementById('explainGotoSettingsBtn');
const generateExplainBtn = document.getElementById('generateExplainBtn');
const explainModeSelect = document.getElementById('explainMode');
const refreshBtn = document.getElementById('refreshBtn');
const autoRefreshCheck = document.getElementById('autoRefresh');
const eventTypeFilter = document.getElementById('eventTypeFilter');
const toolFilter = document.getElementById('toolFilter');
const keywordFilter = document.getElementById('keywordFilter');
const healthSummary = document.getElementById('healthSummary');

const questionInput = document.getElementById('questionInput');
const askQuestionBtn = document.getElementById('askQuestionBtn');
const questionStatus = document.getElementById('questionStatus');
const questionAnswer = document.getElementById('questionAnswer');

const settingsModal = document.getElementById('settingsModal');
const settingsBtn = document.getElementById('settingsBtn');
const settingsForm = document.getElementById('settingsForm');
const settingsClose = document.getElementById('settingsClose');
const settingsBackdrop = document.getElementById('settingsBackdrop');
const settingsStatus = document.getElementById('settingsStatus');
const configBaseUrl = document.getElementById('configBaseUrl');
const configApiKey = document.getElementById('configApiKey');
const configModel = document.getElementById('configModel');

let refreshTimer = null;
let refreshInFlight = false;
let eventsRequestSeq = 0;
let loadingExplain = false;
let askingQuestion = false;

let projects = [];
let sessions = [];
let currentEvents = [];
let selectedIndex = -1;
let currentHealth = null;
const explainCache = new Map();

const REFRESH_INTERVAL_MS = 2000;
const MAX_EXPLAIN_CACHE_SIZE = 800;
const EVENT_FETCH_LIMIT = 1200;

function shortTextHash(input) {
  const text = String(input || '');
  const len = Math.min(text.length, 1024);
  let hash = 2166136261;
  for (let i = 0; i < len; i++) {
    hash ^= text.charCodeAt(i);
    hash += (hash << 1) + (hash << 4) + (hash << 7) + (hash << 8) + (hash << 24);
  }
  return (hash >>> 0).toString(16);
}

function formatDateTime(isoUtc) {
  if (!isoUtc) return '-';
  const d = new Date(isoUtc);
  if (Number.isNaN(d.getTime())) return isoUtc;
  return d.toLocaleString('zh-CN', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  });
}

function compactText(value, limit = 120) {
  const s = String(value || '').replace(/\s+/g, ' ').trim();
  return s.length > limit ? s.slice(0, limit) + '…' : s;
}

function getEventKey(event) {
  if (!event) return '';
  if (event.eventId) return String(event.eventId);
  return `${event.timestamp}|${event.eventType}|${event.traceId}|${shortTextHash(JSON.stringify(event.raw || event))}`;
}

function setExplainCache(key, value) {
  explainCache.set(key, value);
  while (explainCache.size > MAX_EXPLAIN_CACHE_SIZE) {
    const first = explainCache.keys().next().value;
    if (!first) break;
    explainCache.delete(first);
  }
}

function currentSelectedEvent() {
  if (selectedIndex < 0 || selectedIndex >= currentEvents.length) return null;
  return currentEvents[selectedIndex];
}

function eventClass(eventType) {
  const t = String(eventType || '').toLowerCase();
  if (t === 'pre_tool') return 'pre';
  if (t === 'tool_failure') return 'failure';
  return 'post';
}

function eventLabel(eventType) {
  const t = String(eventType || '');
  if (t === 'pre_tool') return 'pre_tool';
  if (t === 'post_tool') return 'post_tool';
  if (t === 'tool_failure') return 'tool_failure';
  if (t === 'user_input') return 'user_input';
  if (t === 'assistant_output') return 'assistant_output';
  return t || 'system';
}

function getRuleSummary(event) {
  if (!event) return '';
  const eventType = String(event.eventType || '');
  const toolName = String(event.toolName || '');
  const input = event.toolInput || {};
  const output = event.toolOutput || {};
  const content = String(event.content || '');
  if (eventType === 'user_input') return '用户输入：' + compactText(content || '(空)');
  if (eventType === 'assistant_output') return '助手输出：' + compactText(content || '(空)');
  if (eventType === 'pre_tool') {
    if (toolName.toLowerCase().includes('shell') || toolName.toLowerCase().includes('bash')) {
      return '即将执行命令：' + compactText(input.command || input.commandText || '(无命令)');
    }
    return `即将调用工具 ${toolName || '(未知工具)'}`;
  }
  if (eventType === 'post_tool') {
    if (typeof output === 'string') return '工具返回：' + compactText(output);
    if (output && output.error) return '工具返回错误：' + compactText(output.error);
    return `工具 ${toolName || '(未知工具)'} 执行完成`;
  }
  if (eventType === 'tool_failure') {
    return `工具 ${toolName || '(未知工具)'} 执行失败：${compactText(event.error || output?.error || '未知错误')}`;
  }
  return compactText(content || JSON.stringify(output || input || {}));
}

function buildEventMetaText(event) {
  const arr = [
    formatDateTime(event.timestamp),
    eventLabel(event.eventType),
    event.toolName || '-',
    event.source || '-'
  ];
  if (event.cwd) arr.push(event.cwd);
  return arr.join('  |  ');
}

function updateCounterText() {
  const projectText = projects.length ? `项目 ${projects.length}` : '项目 0';
  const sessionText = sessions.length ? `会话 ${sessions.length}` : '会话 0';
  sessionCountEl.textContent = `${projectText} · ${sessionText}`;
}

function renderHealthSummary() {
  if (!healthSummary) return;
  const h = currentHealth;
  if (!h) {
    healthSummary.textContent = '';
    return;
  }
  healthSummary.textContent = `总事件 ${h.totalEvents || 0} · pre ${h.preToolCount || 0} · post ${h.postToolCount || 0} · 失败 ${h.failureCount || 0} · 去重 ${h.duplicateCollapsed || 0} · 缺失post ${h.missingPostCount || 0}`;
}

function renderLogList() {
  const savedScrollTop = logList.scrollTop;
  logList.innerHTML = '';
  if (!currentEvents.length) {
    emptyHint.classList.remove('hidden');
    return;
  }
  emptyHint.classList.add('hidden');
  const frag = document.createDocumentFragment();
  currentEvents.forEach((event, index) => {
    const item = document.createElement('div');
    item.className = 'log-item' + (index === selectedIndex ? ' active' : '');
    item.dataset.index = String(index);

    const header = document.createElement('div');
    header.className = 'log-item-header';

    const timeEl = document.createElement('span');
    timeEl.className = 'time';
    timeEl.textContent = formatDateTime(event.timestamp);

    const eventEl = document.createElement('span');
    eventEl.className = `event ${eventClass(event.eventType)}`;
    eventEl.textContent = eventLabel(event.eventType);

    const toolEl = document.createElement('span');
    toolEl.className = 'tool';
    toolEl.textContent = event.toolName || '-';

    const cwdEl = document.createElement('span');
    cwdEl.className = 'cwd';
    cwdEl.title = event.cwd || '';
    cwdEl.textContent = event.cwd || '-';

    const summary = document.createElement('div');
    summary.className = 'log-item-summary';
    summary.textContent = getRuleSummary(event);

    header.appendChild(timeEl);
    header.appendChild(eventEl);
    header.appendChild(toolEl);
    header.appendChild(cwdEl);
    item.appendChild(header);
    item.appendChild(summary);
    frag.appendChild(item);
  });
  logList.appendChild(frag);
  logList.scrollTop = savedScrollTop;
}

function updateExplainButton() {
  const selected = currentSelectedEvent();
  const isAuto = explainModeSelect.value === 'auto';
  generateExplainBtn.textContent = loadingExplain ? '生成中…' : (isAuto ? '重新生成' : '生成解说');
  generateExplainBtn.disabled = loadingExplain || !selected;
}

function renderExplainPane() {
  const event = currentSelectedEvent();
  const hasSelection = !!event;
  explainEmptyHint.classList.toggle('hidden', hasSelection);
  explainPane.classList.toggle('hidden', !hasSelection);
  if (!hasSelection) {
    updateExplainButton();
    return;
  }
  explainMeta.textContent = buildEventMetaText(event);
  ruleSummary.textContent = getRuleSummary(event);
  jsonPreview.textContent = JSON.stringify(event.raw || event, null, 2);
  const cache = explainCache.get(getEventKey(event));
  if (cache?.text) {
    modelStatus.textContent = cache.time ? `已生成（${cache.time}）` : '已生成';
    modelStatus.className = 'model-status success';
    modelExplainText.textContent = cache.text;
    if (explainGotoSettingsHint) explainGotoSettingsHint.classList.add('hidden');
  } else {
    modelStatus.textContent = explainModeSelect.value === 'auto' ? '自动模式：将自动生成解说' : '手动模式：点击按钮生成';
    modelStatus.className = 'model-status';
    modelExplainText.textContent = '';
    if (explainGotoSettingsHint) explainGotoSettingsHint.classList.add('hidden');
  }
  updateExplainButton();
}

async function fetchProjects() {
  const res = await fetch('/api/projects');
  if (!res.ok) throw new Error('获取项目列表失败');
  const data = await res.json();
  return data.projects || [];
}

async function fetchProjectSessions(projectId) {
  if (!projectId) return [];
  const res = await fetch(`/api/projects/${encodeURIComponent(projectId)}/sessions`);
  if (!res.ok) throw new Error('获取项目会话失败');
  const data = await res.json();
  return data.sessions || [];
}

async function fetchSessionEvents(sessionId) {
  const params = new URLSearchParams();
  params.set('limit', String(EVENT_FETCH_LIMIT));
  const et = (eventTypeFilter?.value || '').trim();
  const tool = (toolFilter?.value || '').trim();
  const q = (keywordFilter?.value || '').trim();
  if (et) params.set('eventType', et);
  if (tool) params.set('toolName', tool);
  if (q) params.set('q', q);
  const res = await fetch(`/api/timelines/${encodeURIComponent(sessionId)}/events?${params.toString()}`);
  if (!res.ok) throw new Error('获取会话事件失败');
  return res.json();
}

async function requestModelExplain(event) {
  const fallbackInput = event.toolInput && Object.keys(event.toolInput).length
    ? event.toolInput
    : { content: event.content || '' };
  const fallbackOutput = event.toolOutput && (
    (typeof event.toolOutput === 'string' && event.toolOutput.trim()) ||
    (typeof event.toolOutput === 'object' && Object.keys(event.toolOutput).length)
  ) ? event.toolOutput : { note: event.content || '' };

  const res = await fetch('/api/explain', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      toolName: event.toolName || event.eventType || 'timeline_event',
      toolInput: fallbackInput,
      toolResponse: fallbackOutput,
      event: event.eventType
    })
  });
  const data = await res.json();
  if (!res.ok || data.error) throw new Error(data.error || `HTTP ${res.status}`);
  const text = String(data.explanation || data.text || '').trim();
  if (!text) throw new Error('模型未返回文本');
  return text;
}

async function ensureModelExplain(force = false) {
  const event = currentSelectedEvent();
  if (!event || loadingExplain) return;
  const key = getEventKey(event);
  if (!force && explainCache.get(key)?.text) return;
  loadingExplain = true;
  modelStatus.textContent = '正在调用模型...';
  modelStatus.className = 'model-status';
  modelExplainText.textContent = '';
  updateExplainButton();
  try {
    const text = await requestModelExplain(event);
    const t = new Date().toLocaleTimeString('zh-CN', { hour12: false });
    setExplainCache(key, { text, time: t });
    renderExplainPane();
  } catch (err) {
    const msg = String(err.message || err || '调用失败');
    modelStatus.textContent = msg;
    modelStatus.className = 'model-status error';
    modelExplainText.textContent = '';
    if (explainGotoSettingsHint) {
      explainGotoSettingsHint.classList.toggle('hidden', !msg.includes('未配置解说 API'));
    }
  } finally {
    loadingExplain = false;
    updateExplainButton();
  }
}

function updateToolFilter(tools, keepCurrent = true) {
  if (!toolFilter) return;
  const old = keepCurrent ? toolFilter.value : '';
  toolFilter.innerHTML = '<option value="">全部工具</option>';
  (tools || []).forEach((name) => {
    const opt = document.createElement('option');
    opt.value = name;
    opt.textContent = name;
    toolFilter.appendChild(opt);
  });
  if (old && (tools || []).includes(old)) toolFilter.value = old;
}

function selectEvent(index) {
  if (index < 0 || index >= currentEvents.length) return;
  selectedIndex = index;
  renderLogList();
  renderExplainPane();
  if (explainModeSelect.value === 'auto') ensureModelExplain(false);
}

function fillProjectOptions(list, keepCurrent = true) {
  const old = keepCurrent ? projectSelect.value : '';
  projectSelect.innerHTML = '<option value="">-- 选择项目 --</option>';
  list.forEach((p) => {
    const opt = document.createElement('option');
    opt.value = p.id;
    opt.textContent = `${p.name} · ${p.sessionCount || 0}会话`;
    opt.title = p.id;
    projectSelect.appendChild(opt);
  });
  if (old && list.some((x) => x.id === old)) {
    projectSelect.value = old;
  } else if (list.length) {
    projectSelect.value = list[0].id;
  }
}

function fillSessionOptions(list, keepCurrent = true) {
  const old = keepCurrent ? sessionSelect.value : '';
  sessionSelect.innerHTML = '<option value="">-- 选择会话 --</option>';
  list.forEach((s) => {
    const opt = document.createElement('option');
    opt.value = s.id;
    const label = `${(s.id || '').slice(0, 12)}… · ${s.eventCount || 0} 条 · ${formatDateTime(s.mtime)}`;
    opt.textContent = label;
    opt.title = s.id;
    sessionSelect.appendChild(opt);
  });
  if (old && list.some((x) => x.id === old)) {
    sessionSelect.value = old;
  } else if (list.length) {
    sessionSelect.value = list[0].id;
  }
}

function setProjectsLoading(loading) {
  if (projectSelect) projectSelect.disabled = loading;
  if (sessionSelect) sessionSelect.disabled = loading;
  if (sessionCountEl) sessionCountEl.textContent = loading ? '加载中…' : '';
}

function setEventsLoading(loading) {
  if (loading) {
    if (emptyHint) {
      emptyHint.textContent = '加载中…';
      emptyHint.classList.remove('hidden');
    }
    if (sessionSelect) sessionSelect.disabled = true;
  } else {
    if (sessionSelect) sessionSelect.disabled = false;
  }
}

async function loadProjectsAndSessions(keepSelection = true) {
  setProjectsLoading(true);
  try {
    projects = await fetchProjects();
    fillProjectOptions(projects, keepSelection);
    const pid = projectSelect.value;
    sessions = await fetchProjectSessions(pid);
    fillSessionOptions(sessions, keepSelection);
    updateCounterText();
  } finally {
    setProjectsLoading(false);
    updateCounterText();
    if (projects.length === 0 && emptyHint) {
      emptyHint.textContent = '未找到项目。请确认数据目录（默认 ~/.claude/projects）存在且包含 .jsonl 文件。';
      emptyHint.classList.remove('hidden');
    }
  }
}

async function loadCurrentSessionEvents() {
  const requestSeq = ++eventsRequestSeq;
  const sid = sessionSelect.value;
  if (!sid) {
    currentEvents = [];
    selectedIndex = -1;
    currentHealth = null;
    renderHealthSummary();
    renderLogList();
    renderExplainPane();
    return;
  }
  setEventsLoading(true);
  try {
    const prevKey = getEventKey(currentSelectedEvent());
    const data = await fetchSessionEvents(sid);
    if (requestSeq !== eventsRequestSeq) return;
    currentEvents = (data.events || []).map((e) => ({ ...e, key: getEventKey(e) }));
    currentHealth = data.health || null;
    renderHealthSummary();
    updateToolFilter(data.tools || []);
    if (!currentEvents.length) {
      selectedIndex = -1;
      emptyHint.textContent = '当前筛选条件下没有事件。';
      emptyHint.classList.remove('hidden');
    } else {
      const found = prevKey ? currentEvents.findIndex((e) => e.key === prevKey) : -1;
      selectedIndex = found >= 0 ? found : 0;
      emptyHint.classList.add('hidden');
    }
    renderLogList();
    renderExplainPane();
    if (selectedIndex >= 0 && explainModeSelect.value === 'auto') ensureModelExplain(false);
  } catch (err) {
    if (requestSeq !== eventsRequestSeq) return;
    currentEvents = [];
    selectedIndex = -1;
    currentHealth = null;
    renderHealthSummary();
    emptyHint.textContent = '加载失败: ' + (err.message || err) + '。请确认服务已启动且地址正确（默认 http://127.0.0.1:3847）。';
    emptyHint.classList.remove('hidden');
    renderLogList();
    renderExplainPane();
  } finally {
    setEventsLoading(false);
  }
}

function startAutoRefresh() {
  if (refreshTimer) clearInterval(refreshTimer);
  if (!autoRefreshCheck.checked) return;
  refreshTimer = setInterval(async () => {
    if (refreshInFlight) return;
    refreshInFlight = true;
    try {
      await loadProjectsAndSessions(true);
      await loadCurrentSessionEvents();
    } finally {
      refreshInFlight = false;
    }
  }, REFRESH_INTERVAL_MS);
}

function stopAutoRefresh() {
  if (refreshTimer) {
    clearInterval(refreshTimer);
    refreshTimer = null;
  }
}

async function askQuestion() {
  const q = (questionInput?.value || '').trim();
  const event = currentSelectedEvent();
  if (!q || askingQuestion) return;
  if (!event) {
    questionStatus.textContent = '请先选择一条事件';
    questionStatus.className = 'model-status error';
    return;
  }
  askingQuestion = true;
  questionStatus.textContent = '正在思考...';
  questionStatus.className = 'model-status';
  questionAnswer.textContent = '';
  askQuestionBtn.disabled = true;
  try {
    const res = await fetch('/api/question', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question: q,
        logJson: JSON.stringify(event.raw || event, null, 2)
      })
    });
    let data;
    try {
      data = await res.json();
    } catch (_) {
      if (res.status === 404) {
        questionStatus.textContent = '当前服务未支持提问接口。请重启 log-viewer 服务（重新运行 node server.js 或 python server.py）后重试。';
      } else {
        questionStatus.textContent = '请求失败：服务器返回异常，请确认服务已重启到最新版本。';
      }
      questionStatus.className = 'model-status error';
      return;
    }
    if (data.error) {
      questionStatus.textContent = data.error;
      questionStatus.className = 'model-status error';
    } else {
      questionStatus.textContent = '回答已生成';
      questionStatus.className = 'model-status success';
      questionAnswer.textContent = data.answer || '';
    }
  } catch (err) {
    questionStatus.textContent = '请求失败: ' + (err.message || err) + '。若此前未重启过服务，请重启 node server.js 或 python server.py 后重试。';
    questionStatus.className = 'model-status error';
  } finally {
    askingQuestion = false;
    askQuestionBtn.disabled = false;
  }
}

function openSettings() {
  settingsModal.setAttribute('aria-hidden', 'false');
  loadExplainConfig();
}

function closeSettings() {
  settingsModal.setAttribute('aria-hidden', 'true');
  settingsStatus.textContent = '';
  settingsStatus.className = 'settings-status';
}

async function loadExplainConfig() {
  try {
    const res = await fetch('/api/explain-config');
    const c = await res.json();
    configBaseUrl.value = (c.apiUrl || '').replace(/\/chat\/completions\/?$/, '').trim();
    configApiKey.value = c.apiKey || '';
    configModel.value = c.model || 'qwen-turbo';
  } catch (_) {
    configBaseUrl.value = 'https://dashscope.aliyuncs.com/compatible-mode/v1';
    configApiKey.value = '';
    configModel.value = 'qwen-turbo';
  }
}

async function saveExplainConfig(e) {
  e.preventDefault();
  const apiUrl = (configBaseUrl.value || '').trim();
  const apiKey = (configApiKey.value || '').trim();
  const model = (configModel.value || '').trim() || 'qwen-turbo';
  settingsStatus.textContent = '保存中…';
  settingsStatus.className = 'settings-status';
  try {
    const res = await fetch('/api/explain-config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ apiUrl, apiKey, model })
    });
    const data = await res.json();
    if (!res.ok || data.error) {
      settingsStatus.textContent = data.error || '保存失败';
      settingsStatus.className = 'settings-status error';
      return;
    }
    settingsStatus.textContent = '已保存到本地 explain-config.json';
    settingsStatus.className = 'settings-status success';
  } catch (err) {
    settingsStatus.textContent = '请求失败: ' + (err.message || err);
    settingsStatus.className = 'settings-status error';
  }
}

projectSelect.addEventListener('change', async () => {
  sessions = await fetchProjectSessions(projectSelect.value);
  fillSessionOptions(sessions, false);
  updateCounterText();
  await loadCurrentSessionEvents();
});

sessionSelect.addEventListener('change', async () => {
  await loadCurrentSessionEvents();
});

if (eventTypeFilter) {
  eventTypeFilter.addEventListener('change', async () => {
    await loadCurrentSessionEvents();
  });
}
if (toolFilter) {
  toolFilter.addEventListener('change', async () => {
    await loadCurrentSessionEvents();
  });
}

let keywordDebounceTimer = null;
if (keywordFilter) {
  keywordFilter.addEventListener('input', () => {
    if (keywordDebounceTimer) clearTimeout(keywordDebounceTimer);
    keywordDebounceTimer = setTimeout(() => loadCurrentSessionEvents(), 300);
  });
}

logList.addEventListener('click', (e) => {
  const item = e.target.closest('.log-item');
  if (!item || !logList.contains(item)) return;
  const index = Number(item.dataset.index);
  if (Number.isInteger(index)) selectEvent(index);
});

document.addEventListener('keydown', (e) => {
  const target = e.target;
  const isEditable = target && (
    target.tagName === 'INPUT' ||
    target.tagName === 'TEXTAREA' ||
    target.isContentEditable
  );
  if (isEditable) return;
  if (currentEvents.length === 0) return;
  if (e.key === 'ArrowDown') {
    e.preventDefault();
    const next = Math.min(selectedIndex + 1, currentEvents.length - 1);
    if (next !== selectedIndex) selectEvent(next);
    const activeItem = logList.querySelector('.log-item.active');
    if (activeItem) activeItem.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  } else if (e.key === 'ArrowUp') {
    e.preventDefault();
    const prev = Math.max(selectedIndex - 1, 0);
    if (prev !== selectedIndex) selectEvent(prev);
    const activeItem = logList.querySelector('.log-item.active');
    if (activeItem) activeItem.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }
});

refreshBtn.addEventListener('click', async () => {
  await loadProjectsAndSessions(true);
  await loadCurrentSessionEvents();
});

autoRefreshCheck.addEventListener('change', () => {
  if (autoRefreshCheck.checked) startAutoRefresh();
  else stopAutoRefresh();
});

explainModeSelect.addEventListener('change', () => {
  renderExplainPane();
  if (explainModeSelect.value === 'auto') ensureModelExplain(false);
});

generateExplainBtn.addEventListener('click', () => ensureModelExplain(true));

if (askQuestionBtn) askQuestionBtn.addEventListener('click', askQuestion);
if (questionInput) {
  questionInput.addEventListener('keydown', (e) => {
    if (e.isComposing) return;
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      askQuestion();
    }
  });
}

if (settingsBtn) settingsBtn.addEventListener('click', openSettings);
if (explainGotoSettingsBtn) explainGotoSettingsBtn.addEventListener('click', openSettings);
if (settingsClose) settingsClose.addEventListener('click', closeSettings);
if (settingsBackdrop) settingsBackdrop.addEventListener('click', closeSettings);
if (settingsForm) settingsForm.addEventListener('submit', saveExplainConfig);

if (jsonToggleBtn && jsonPreview) {
  jsonToggleBtn.addEventListener('click', () => {
    jsonPreview.classList.toggle('collapsed');
    jsonToggleBtn.textContent = jsonPreview.classList.contains('collapsed') ? '展开' : '收起';
  });
}

(async function init() {
  await loadProjectsAndSessions(false);
  await loadCurrentSessionEvents();
  startAutoRefresh();
})();
