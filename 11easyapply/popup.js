// popup.js - 简历填充助手逻辑控制 v1.1
// 新增：投递记录追踪 + Excel 导出 + Edge 兼容

// ───────── 种子数据 ─────────
const SEED_DATA = {
  fullName: '梁致铭', idType: '身份证', idCard: '130206200107172318',
  gender: '男', birthday: '2001-07-17', phone: '15232735822',
  email: '3053706724@qq.com', political: '中共党员', nation: '汉族',
  weight: '77', height: '179', hometown: '河北省/衡水市',
  birthplace: '河北省/唐山市', source: '招商银行官网', expectCity: '西安市',
  marriage: '未婚', currentAddress: '新加坡650224', hasWorked: '否',
  expectedSalary: '', intro: '勇敢 认真 勤奋 创新 坚持',
  edu: [
    { 'field-school': '南洋理工大学', 'field-degree': '硕士研究生', 'field-major': '人工智能', 'field-department': 'CCDS', 'field-endDate': '2025-08-01～2026-07-01', 'field-rank': '前20%', 'field-fulltime': '是' },
    { 'field-school': '西安交通大学', 'field-degree': '本科', 'field-major': '计算机科学与技术', 'field-department': '电信学部', 'field-endDate': '2019-09-01～2023-07-01', 'field-rank': '中等', 'field-fulltime': '是', 'field-thesis': '图神经网络噪声标签学习' },
    { 'field-school': '衡水第一中学', 'field-degree': '高中', 'field-major': '', 'field-department': '', 'field-endDate': '2016-09-01～2019-06-30', 'field-rank': '', 'field-fulltime': '' }
  ],
  intern: [], work: [], project: [],
  lang: [{ 'field-type': 'IELTS', 'field-level': '6.5' }],
  cert: [],
  family: [
    { 'field-relation': '紧急联络人', 'field-familyName': '梁永江', 'field-job': '中国中车 - 工人', 'field-familyPhone': '15133922728', 'field-inGroup': '否' },
    { 'field-relation': '父亲', 'field-familyName': '梁永江', 'field-job': '中国中车 - 工人', 'field-familyPhone': '15133922728', 'field-inGroup': '否' },
    { 'field-relation': '母亲', 'field-familyName': '王超', 'field-job': '中国中车 - 工人', 'field-familyPhone': '13933352488', 'field-inGroup': '否' }
  ]
};

// ───────── 字段配置 ─────────
const STATIC_FIELDS = [
  'fullName','idType','idCard','gender','birthday','phone','email',
  'political','nation','weight','height','hometown','birthplace',
  'source','expectCity','marriage','currentAddress','hasWorked',
  'expectedSalary','intro'
];

const LIST_FIELDS = {
  edu:    { containerId:'eduContainer',    templateId:'eduTemplate',    fields:['field-school','field-degree','field-major','field-department','field-endDate','field-rank','field-fulltime','field-thesis'] },
  intern: { containerId:'internContainer', templateId:'internTemplate', fields:['field-company','field-position','field-time','field-contact','field-contactPhone','field-desc'] },
  work:   { containerId:'workContainer',   templateId:'workTemplate',   fields:['field-company','field-position','field-time','field-contact','field-contactPhone','field-desc'] },
  project:{ containerId:'projectContainer',templateId:'projectTemplate',fields:['field-certName','field-role','field-time','field-desc'] },
  lang:   { containerId:'langContainer',   templateId:'langTemplate',   fields:['field-type','field-level'] },
  cert:   { containerId:'certContainer',   templateId:'certTemplate',   fields:['field-certName','field-org','field-time'] },
  family: { containerId:'familyContainer', templateId:'familyTemplate', fields:['field-relation','field-familyName','field-job','field-familyPhone','field-inGroup'] }
};

// ─────────────────────────────────────────
//  INIT
// ─────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadProfiles();
  loadCurrentProfile();
  setupEventListeners();
  // 延迟一帧再读投递记录，避免弹窗刚打开时拿到旧缓存
  setTimeout(() => renderRecordsTab(), 0);
  // 监听 storage 变化：别处（或本页刚写入）更新了投递记录时，列表和数量同步刷新
  chrome.storage.onChanged.addListener((changes, areaName) => {
    if (areaName === 'local' && changes.applicationRecords) {
      renderRecordsTab();
    }
  });
});

// ─────────────────────────────────────────
//  EVENT LISTENERS
// ─────────────────────────────────────────
function setupEventListeners() {
  document.getElementById('saveBtn').addEventListener('click', () => saveCurrentProfile(false));
  document.getElementById('fillBtn').addEventListener('click', fillCurrentPage);
  document.getElementById('profileSelector').addEventListener('change', loadCurrentProfile);
  document.getElementById('addProfileBtn').addEventListener('click', createNewProfile);
  document.getElementById('clearFormBtn').addEventListener('click', clearForm);
  document.getElementById('exportExcelBtn').addEventListener('click', exportToExcel);
  document.getElementById('modalSaveBtn').addEventListener('click', saveModalRecord);
  document.getElementById('modalCancelBtn').addEventListener('click', () => hideModal());
  document.getElementById('manualRecordBtn').addEventListener('click', manualRecord);
  // 本地备份下载
  const downloadBackupBtn = document.getElementById('downloadBackupBtn');
  if (downloadBackupBtn) downloadBackupBtn.addEventListener('click', downloadCurrentRecords);

  // Tab switching
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.tab;
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById('tab-' + target).classList.add('active');
      if (target === 'records') renderRecordsTab();
    });
  });

  // Auto-save on form change
  const autoSave = debounce(() => saveCurrentProfile(true), 1000);
  document.querySelector('.form-scroll').addEventListener('input', autoSave);
  document.querySelector('.form-scroll').addEventListener('change', autoSave);

  // Add list item buttons
  document.querySelectorAll('.add-more-btn').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const type = e.target.getAttribute('data-type');
      addListItem(type);
      autoSave();
    });
  });
}

function debounce(fn, delay) {
  let timer = null;
  return function() {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, arguments), delay);
  };
}

// ─────────────────────────────────────────
//  PROFILE MANAGEMENT
// ─────────────────────────────────────────
function loadProfiles() {
  chrome.storage.local.get(['profiles','activeProfileId'], (result) => {
    let profiles = result.profiles;
    const hasValidDefault = profiles && profiles['default'] && profiles['default'].data && profiles['default'].data.fullName;
    if (!hasValidDefault) {
      profiles = { 'default': { name: '梁致铭 - 核心简历 (已同步)', data: SEED_DATA } };
      chrome.storage.local.set({ profiles, activeProfileId: 'default' }, () => {
        renderProfileSelector(profiles, 'default');
      });
    } else {
      const activeId = result.activeProfileId || Object.keys(profiles)[0];
      renderProfileSelector(profiles, activeId);
    }
  });
}

function renderProfileSelector(profiles, activeId) {
  const selector = document.getElementById('profileSelector');
  if (!selector) return;
  selector.innerHTML = '';
  Object.keys(profiles).forEach(id => {
    const option = document.createElement('option');
    option.value = id;
    option.textContent = profiles[id].name;
    option.selected = id === activeId;
    selector.appendChild(option);
  });
  loadCurrentProfile();
}

function loadCurrentProfile() {
  const selector = document.getElementById('profileSelector');
  if (!selector) return;
  const profileId = selector.value;
  chrome.storage.local.get(['profiles'], (result) => {
    const profiles = result.profiles || {};
    const targetId = profiles[profileId] ? profileId : Object.keys(profiles)[0];
    const profile = profiles[targetId] || { data: {} };
    if (targetId !== profileId) selector.value = targetId;
    chrome.storage.local.set({ activeProfileId: targetId });
    renderFormData(profile.data || {});
  });
}

function renderFormData(data) {
  STATIC_FIELDS.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = data[id] || '';
  });
  Object.keys(LIST_FIELDS).forEach(type => {
    const config = LIST_FIELDS[type];
    const container = document.getElementById(config.containerId);
    if (container) {
      container.innerHTML = '';
      (data[type] || []).forEach(itemData => addListItem(type, itemData));
    }
  });
}

function saveCurrentProfile(silent = false) {
  const selector = document.getElementById('profileSelector');
  if (!selector) return;
  const profileId = selector.value;
  const data = {};
  STATIC_FIELDS.forEach(id => {
    const el = document.getElementById(id);
    if (el) data[id] = el.value;
  });
  Object.keys(LIST_FIELDS).forEach(type => {
    const config = LIST_FIELDS[type];
    const container = document.getElementById(config.containerId);
    data[type] = [];
    if (container) {
      Array.from(container.children).forEach(item => {
        const itemData = {};
        config.fields.forEach(fieldClass => {
          const input = item.querySelector('.' + fieldClass);
          if (input) itemData[fieldClass] = input.value;
        });
        data[type].push(itemData);
      });
    }
  });
  chrome.storage.local.get(['profiles'], (result) => {
    const profiles = result.profiles || { 'default': { name: '默认简历', data: {} } };
    if (!profiles[profileId]) profiles[profileId] = { name: '未命名简历', data: {} };
    profiles[profileId].data = data;
    chrome.storage.local.set({ profiles }, () => {
      if (!silent) showStatus('保存成功！');
    });
  });
}

function createNewProfile() {
  const nameInput = document.getElementById('newProfileName');
  const name = nameInput.value.trim();
  if (!name) return showStatus('请输入简历名称');
  const newId = 'profile_' + Date.now();
  chrome.storage.local.get(['profiles'], (result) => {
    const profiles = result.profiles || { 'default': { name: '默认简历', data: {} } };
    profiles[newId] = { name, data: {} };
    chrome.storage.local.set({ profiles, activeProfileId: newId }, () => {
      nameInput.value = '';
      loadProfiles();
      showStatus('新简历已创建');
    });
  });
}

function clearForm() {
  if (!confirm('确定要清空表单吗？')) return;
  STATIC_FIELDS.forEach(id => { const el = document.getElementById(id); if (el) el.value = ''; });
  Object.values(LIST_FIELDS).forEach(config => {
    const c = document.getElementById(config.containerId);
    if (c) c.innerHTML = '';
  });
  showStatus('表单已清空');
}

// ─────────────────────────────────────────
//  LIST ITEM UI
// ─────────────────────────────────────────
function addListItem(type, data = {}) {
  const config = LIST_FIELDS[type];
  const container = document.getElementById(config.containerId);
  const template = document.getElementById(config.templateId);
  const clone = template.content.cloneNode(true);

  const nextIndex = container.children.length + 1;
  const indexSpan = clone.querySelector('.item-index');
  if (indexSpan) {
    const title = { edu:'教育', intern:'实习', work:'工作', project:'项目', lang:'语言', cert:'荣誉', family:'成员' }[type] || type;
    indexSpan.textContent = `${title} #${nextIndex}`;
  }
  config.fields.forEach(fieldClass => {
    const input = clone.querySelector('.' + fieldClass);
    if (input) input.value = data[fieldClass] || '';
  });
  clone.querySelector('.remove-btn').addEventListener('click', (e) => {
    e.target.closest('.list-item').remove();
    updateIndices(container);
    saveCurrentProfile(true);
  });
  container.appendChild(clone);
}

function updateIndices(container) {
  Array.from(container.children).forEach((item, index) => {
    const indexSpan = item.querySelector('.item-index');
    if (indexSpan) {
      const prefix = indexSpan.textContent.split('#')[0];
      indexSpan.textContent = `${prefix}#${index + 1}`;
    }
  });
}

// ─────────────────────────────────────────
//  FILL CURRENT PAGE
// ─────────────────────────────────────────
async function fillCurrentPage() {
  const profileId = document.getElementById('profileSelector').value;
  const fillStatus = document.getElementById('fillStatus');

  chrome.storage.local.get(['profiles'], async (result) => {
    const profiles = result.profiles || {};
    const data = profiles[profileId]?.data || {};

    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab) return showStatus('无法获取当前标签页');

    fillStatus.classList.add('show');
    chrome.tabs.sendMessage(tab.id, { action: 'FILL_FORM', data }, (response) => {
      fillStatus.classList.remove('show');
      if (chrome.runtime.lastError) return showStatus('请刷新页面后重试');
      if (response && response.success) {
        const count = response.count || 0;
        showStatus(`填充完成！共填充 ${count} 个字段`);
        // 只要填充了至少 1 个字段，就弹出保存确认
        if (count >= 1) {
          const prefill = extractPageInfo(tab.title || '', tab.url || '');
          showModal(prefill);
        }
      } else {
        // 即使没有填充成功，也提供手动保存的机会
        showStatus('填充完成（未匹配到字段）');
      }
    });
  });
}

/**
 * Extract company & position name from page title / URL.
 * Heuristic: many job pages have "岗位名 - 公司名 - 招聘" in title.
 */
function extractPageInfo(title, url) {
  let company = '', position = '';
  // Clean common suffixes
  const cleanTitle = title.replace(/[-_|｜–]?\s*(招聘|职位详情|应聘|Apply|Job|Career).*$/i, '').trim();
  const parts = cleanTitle.split(/[-–—|｜]/);
  if (parts.length >= 2) {
    position = parts[0].trim();
    company = parts[1].trim();
  } else {
    company = cleanTitle;
  }
  // Try to extract domain as fallback company name
  if (!company) {
    try {
      const host = new URL(url).hostname.replace('www.', '').split('.')[0];
      company = host;
    } catch(e) {}
  }
  return { company, position };
}

// ─────────────────────────────────────────
//  APPLICATION RECORD MODAL
// ─────────────────────────────────────────
function showModal(prefill = {}) {
  document.getElementById('modal-company').value = prefill.company || '';
  document.getElementById('modal-position').value = prefill.position || '';
  document.getElementById('modal-interview').value = '';
  document.getElementById('modal-note').value = '';
  document.getElementById('appModal').classList.add('show');
}

// 手动记录投递（不依赖填充）
async function manualRecord() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const prefill = extractPageInfo(tab?.title || '', tab?.url || '');
  showModal(prefill);
}

function hideModal() {
  document.getElementById('appModal').classList.remove('show');
}

function saveModalRecord() {
  const company   = document.getElementById('modal-company').value.trim();
  const position  = document.getElementById('modal-position').value.trim();
  const interview = document.getElementById('modal-interview').value.trim();
  const note      = document.getElementById('modal-note').value.trim();

  if (!company) {
    document.getElementById('modal-company').focus();
    return;
  }

  const record = {
    id: Date.now(),
    company,
    position,
    applyTime: new Date().toLocaleString('zh-CN', { hour12: false }),
    interviewTime: interview,
    note,
    url: ''  // filled below
  };

  // Get current tab URL
  chrome.tabs.query({ active: true, currentWindow: true }, ([tab]) => {
    if (tab) record.url = tab.url || '';
    saveRecord(record);
  });
}

function saveRecord(record) {
  chrome.storage.local.get(['applicationRecords'], (result) => {
    const records = result.applicationRecords || [];
    records.unshift(record); // newest first
    chrome.storage.local.set({ applicationRecords: records }, () => {
      hideModal();
      showStatus('✅ 投递记录已保存，正在备份到本地…');
      renderRecordsTab(records);
      autoSaveToLocal(records);
    });
  });
}

// ─────────────────────────────────────────
//  本地文件自动备份与下载
// ─────────────────────────────────────────

/**
 * 手动下载当前投递记录为 JSON 备份文件（与自动备份同格式，可再用于「从备份导入」）
 */
function downloadCurrentRecords() {
  chrome.storage.local.get(['applicationRecords'], (result) => {
    const records = result.applicationRecords || [];
    const json = JSON.stringify({ version: 1, exportedAt: new Date().toISOString(), records }, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const fileName = `投递记录_备份_${new Date().toLocaleDateString('zh-CN').replace(/\//g, '-')}.json`;
    chrome.downloads.download({
      url,
      filename: fileName,
      saveAs: true
    }, (downloadId) => {
      setTimeout(() => URL.revokeObjectURL(url), 10000);
      if (chrome.runtime.lastError) {
        showStatus('下载失败：' + chrome.runtime.lastError.message);
      } else {
        showStatus(`✅ 已下载当前 ${records.length} 条记录`);
      }
    });
  });
}

/**
 * 每次保存记录后，自动把全量记录下载到本地固定文件
 * （下载目录/投递记录_自动备份.json，已存在则覆盖）
 */
function autoSaveToLocal(records) {
  const json = JSON.stringify({ version: 1, exportedAt: new Date().toISOString(), records }, null, 2);
  const blob = new Blob([json], { type: 'application/json' });
  const url  = URL.createObjectURL(blob);
  chrome.downloads.download({
    url,
    filename: '投递记录_自动备份.json',
    conflictAction: 'overwrite',
    saveAs: false
  }, (downloadId) => {
    setTimeout(() => URL.revokeObjectURL(url), 10000);
    if (chrome.runtime.lastError) {
      console.warn('autoSave failed:', chrome.runtime.lastError.message);
    } else {
      console.log('✅ 本地备份已更新，downloadId:', downloadId);
    }
  });
}

// ─────────────────────────────────────────
//  RECORDS TAB RENDER
// ─────────────────────────────────────────
/**
 * 刷新投递记录列表。可传入 records 则直接用该数组渲染（避免 set 后立刻 get 拿不到新值导致界面不更新）。
 * @param {Array|undefined} recordsFromCaller - 可选，刚写入的完整记录数组；不传则从 storage 读取
 */
function renderRecordsTab(recordsFromCaller) {
  function doRender(records) {
    records = records || [];
    const countEl = document.getElementById('recordsCount');
    const listEl  = document.getElementById('recordsList');
    if (!countEl || !listEl) return;

    countEl.textContent = `${records.length} 条`;

    if (records.length === 0) {
      listEl.innerHTML = `
        <div class="empty-records">
          <div class="icon">📭</div>
          <p>暂无投递记录<br>填充简历后可保存记录</p>
        </div>`;
      return;
    }

    const STATUS_OPTS = [
      { val:'pending',   label:'待跟进', color:'#f59e0b', bg:'#fffbeb' },
      { val:'interview', label:'面试中', color:'#2563eb', bg:'#eff6ff' },
      { val:'rejected',  label:'已拒绝', color:'#ef4444', bg:'#fef2f2' },
      { val:'offer',     label:'已Offer',  color:'#10b981', bg:'#f0fdf4' },
    ];

    listEl.innerHTML = '';
    records.forEach((rec) => {
      const status = STATUS_OPTS.find(s => s.val === rec.status) || STATUS_OPTS[0];
      const card = document.createElement('div');
      card.className = 'record-card';
      card.dataset.id = rec.id;
      card.innerHTML = `
        <div class="record-card-header">
          <span class="record-company">${escHtml(rec.company)}</span>
          <span class="record-position">${escHtml(rec.position || '未填写岗位')}</span>
        </div>
        <div class="record-meta">
          <span>📅 投递：${escHtml(rec.applyTime)}</span>
          ${rec.url ? `<span title="${escHtml(rec.url)}">🔗 <a href="${escHtml(rec.url)}" target="_blank" style="color:#2563eb;text-decoration:none;">查看页面</a></span>` : ''}
        </div>
        <!-- 状态标签 + 内联编辑区 -->
        <div style="display:flex;align-items:center;justify-content:space-between;margin-top:6px;flex-wrap:wrap;gap:4px;">
          <span class="rec-status-badge" data-status="${rec.status||'pending'}"
            style="font-size:11px;font-weight:600;padding:2px 8px;border-radius:12px;
                   cursor:pointer;background:${status.bg};color:${status.color};">
            ${status.label}
          </span>
          <span class="record-del" style="font-size:11px;color:#ef4444;cursor:pointer;padding:2px 6px;border-radius:4px;">🗑 删除</span>
        </div>
        <!-- 面试时间内联编辑 -->
        <div style="margin-top:6px;">
          <span style="font-size:11px;color:#94a3b8;">🗓 面试时间：</span>
          <span class="rec-inline-edit" data-field="interviewTime"
            style="font-size:12px;color:${rec.interviewTime?'#059669':'#cbd5e1'};
                   border-bottom:1px dashed #cbd5e1;cursor:pointer;min-width:60px;display:inline-block;">
            ${escHtml(rec.interviewTime) || '点击填写…'}
          </span>
        </div>
        <!-- 备注内联编辑 -->
        <div style="margin-top:3px;">
          <span style="font-size:11px;color:#94a3b8;">📝 备注：</span>
          <span class="rec-inline-edit" data-field="note"
            style="font-size:12px;color:${rec.note?'#1e293b':'#cbd5e1'};
                   border-bottom:1px dashed #cbd5e1;cursor:pointer;min-width:60px;display:inline-block;">
            ${escHtml(rec.note) || '点击填写…'}
          </span>
        </div>
      `;

      // 删除按钮
      card.querySelector('.record-del').addEventListener('click', () => {
        if (confirm(`确认删除「${rec.company}」的投递记录？`)) deleteRecord(rec.id);
      });

      // 状态切换
      card.querySelector('.rec-status-badge').addEventListener('click', (e) => {
        const cur = e.target.dataset.status;
        const idx = STATUS_OPTS.findIndex(s => s.val === cur);
        const next = STATUS_OPTS[(idx + 1) % STATUS_OPTS.length];
        updateRecordField(rec.id, 'status', next.val);
      });

      // 内联编辑（面试时间 / 备注）
      card.querySelectorAll('.rec-inline-edit').forEach(span => {
        span.addEventListener('click', () => startInlineEdit(span, rec));
      });

      listEl.appendChild(card);
    });
  }

  if (recordsFromCaller !== undefined && Array.isArray(recordsFromCaller)) {
    doRender(recordsFromCaller);
    return;
  }
  chrome.storage.local.get(['applicationRecords'], (result) => {
    doRender(result.applicationRecords || []);
  });
}

function deleteRecord(recordId) {
  chrome.storage.local.get(['applicationRecords'], (result) => {
    const records = (result.applicationRecords || []).filter(r => r.id !== recordId);
    chrome.storage.local.set({ applicationRecords: records }, () => {
      renderRecordsTab(records);
      autoSaveToLocal(records);
    });
  });
}

/** 按 id 更新单个字段，保存后刷新卡片 */
function updateRecordField(recordId, field, value) {
  chrome.storage.local.get(['applicationRecords'], (result) => {
    const records = result.applicationRecords || [];
    const rec = records.find(r => r.id === recordId);
    if (!rec) return;
    rec[field] = value;
    chrome.storage.local.set({ applicationRecords: records }, () => {
      renderRecordsTab(records);
      autoSaveToLocal(records);
    });
  });
}

/**
 * 内联编辑：把 span 替换为 input，失焦或回车时保存
 */
function startInlineEdit(span, rec) {
  const field = span.dataset.field;
  const oldVal = rec[field] || '';
  const input = document.createElement('input');
  input.type = 'text';
  input.value = oldVal;
  input.style.cssText = `
    font-size:12px;border:1px solid #2563eb;border-radius:4px;
    padding:2px 6px;outline:none;width:180px;max-width:100%;
  `;
  span.replaceWith(input);
  input.focus();
  input.select();

  const commit = () => {
    const newVal = input.value.trim();
    if (newVal !== oldVal) {
      updateRecordField(rec.id, field, newVal);
    } else {
      // 未改变则简单刷新
      renderRecordsTab();
    }
  };
  input.addEventListener('blur', commit);
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') { e.preventDefault(); input.blur(); }
    if (e.key === 'Escape') { input.value = oldVal; input.blur(); }
  });
}

function escHtml(str) {
  return String(str || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ─────────────────────────────────────────
//  EXCEL EXPORT (SheetJS - dual sheet)
// ─────────────────────────────────────────
function exportToExcel() {
  chrome.storage.local.get(['applicationRecords'], (result) => {
    const records = result.applicationRecords || [];
    if (records.length === 0) return showStatus('暂无投递记录可导出');

    // ── Sheet1：阅读用汇总（无 id，干净美观）──
    const s1Header = ['序号','公司名称','应聘岗位','投递时间','可能面试时间','备注','来源网址'];
    const s1Data = [s1Header, ...records.map((r, i) => [
      i + 1,
      r.company       || '',
      r.position      || '',
      r.applyTime     || '',
      r.interviewTime || '',
      r.note          || '',
      r.url           || ''
    ])];

    // ── Sheet2：详细记录（含隐藏 __id__ 列，便于本地管理）──
    const s2Header = ['__id__','公司名称','应聘岗位','投递时间','可能面试时间','备注','来源网址'];
    const s2Data = [s2Header, ...records.map(r => [
      r.id            || '',
      r.company       || '',
      r.position      || '',
      r.applyTime     || '',
      r.interviewTime || '',
      r.note          || '',
      r.url           || ''
    ])];

    try {
      const wb = XLSX.utils.book_new();

      // Sheet1
      const ws1 = XLSX.utils.aoa_to_sheet(s1Data);
      ws1['!cols'] = [6, 22, 22, 20, 22, 28, 40].map(w => ({ wch: w }));
      XLSX.utils.book_append_sheet(wb, ws1, '📋 投递汇总');

      // Sheet2：第一列（__id__）设为极窄以「隐藏」，但数据保留供导回
      const ws2 = XLSX.utils.aoa_to_sheet(s2Data);
      ws2['!cols'] = [{ wch: 2, hidden: true }, 22, 22, 20, 22, 28, 40].map(
        (v, i) => typeof v === 'object' ? v : { wch: v }
      );
      XLSX.utils.book_append_sheet(wb, ws2, '📑 详细记录');

      const fileName = `投递记录_${new Date().toLocaleDateString('zh-CN').replace(/\//g,'-')}.xlsx`;
      // 使用 chrome.downloads 并弹出「另存为」对话框，方便选择保存位置
      const wbout = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
      const blob = new Blob([wbout], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
      const url = URL.createObjectURL(blob);
      chrome.downloads.download({
        url,
        filename: fileName,
        saveAs: true  // 弹出另存为对话框
      }, (downloadId) => {
        setTimeout(() => URL.revokeObjectURL(url), 10000);
        if (chrome.runtime.lastError) {
          showStatus('导出失败：' + chrome.runtime.lastError.message);
        } else {
          showStatus(`✅ 已导出 ${records.length} 条记录`);
        }
      });
    } catch(e) {
      console.error('Export error', e);
      showStatus('导出失败，请重试');
    }
  });
}

// ─────────────────────────────────────────
//  STATUS BAR
// ─────────────────────────────────────────
function showStatus(message) {
  const statusBar = document.getElementById('statusBar');
  statusBar.textContent = message;
  statusBar.classList.add('show');
  setTimeout(() => statusBar.classList.remove('show'), 2500);
}
