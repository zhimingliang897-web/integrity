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
  renderRecordsTab();
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
  // 本地备份导入
  const importBtn = document.getElementById('importLocalBtn');
  if (importBtn) importBtn.addEventListener('click', importFromLocal);
  const dedupBtn = document.getElementById('dedupBtn');
  if (dedupBtn) dedupBtn.addEventListener('click', deduplicateNow);

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
      renderRecordsTab();
      autoSaveToLocal(records);
    });
  });
}

// ─────────────────────────────────────────
//  本地文件自动备份 & 导入
// ─────────────────────────────────────────

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

/**
 * 双重去重：
 *   1层 — 按 id （同 id 保留最新版本）
 *   2层 — 按 公司+岗位+投递时间 内容指纹（防止 id 不同但内容相同）
 */
function deduplicateRecords(records) {
  // 第一层：id 去重（同 id 只保留最后出现的，即最新版本）
  const idMap = {};
  records.forEach(r => {
    const key = String(r.id || '');
    idMap[key] = r;
  });
  let deduped = Object.values(idMap);

  // 第二层：内容指纹去重（公司+岗位+投递时间 全相同才删）
  const seen = new Set();
  deduped = deduped.filter(r => {
    const fp = `${r.company}||${r.position}||${r.applyTime}`;
    if (seen.has(fp)) return false;
    seen.add(fp);
    return true;
  });

  deduped.sort((a, b) => (Number(b.id) || 0) - (Number(a.id) || 0));
  return deduped;
}

/**
 * 从本地文件导入投递记录，支持 JSON / Excel，
 * 并先让用户选择导入模式。
 */
function importFromLocal() {
  const input = document.createElement('input');
  input.type  = 'file';
  input.accept = '.json,.xlsx,application/json,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
  input.onchange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const isXlsx = file.name.toLowerCase().endsWith('.xlsx');
    const reader = new FileReader();

    reader.onload = (ev) => {
      try {
        let incoming;
        if (isXlsx) {
          const data = new Uint8Array(ev.target.result);
          const wb   = XLSX.read(data, { type: 'array' });
          // 优先读「📑 详细记录」sheet，fallback 到第一个
          const sheetName = wb.SheetNames.find(n => n.includes('详细')) || wb.SheetNames[0];
          const rows = XLSX.utils.sheet_to_json(wb.Sheets[sheetName], { defval: '' });
          incoming = rows.map(row => ({
            id:            Number(row['__id__'] || row['id']) || Math.floor(Date.now()),
            company:       String(row['公司名称'] || row['company']      || '').trim(),
            position:      String(row['应聘岗位'] || row['position']     || '').trim(),
            applyTime:     String(row['投递时间'] || row['applyTime']    || '').trim(),
            interviewTime: String(row['可能面试时间'] || row['interviewTime'] || '').trim(),
            note:          String(row['备注']     || row['note']         || '').trim(),
            url:           String(row['来源网址'] || row['url']          || '').trim(),
          })).filter(r => r.company);
        } else {
          const parsed = JSON.parse(ev.target.result);
          incoming = Array.isArray(parsed) ? parsed
            : (Array.isArray(parsed.records) ? parsed.records : null);
          if (!incoming) throw new Error('JSON 格式不对');
        }

        if (incoming.length === 0) {
          showStatus('⚠️ 文件里没有有效记录');
          return;
        }

        // 让用户选择导入模式
        const mode = chooseImportMode(incoming.length);
        if (!mode) return; // 用户取消

        chrome.storage.local.get(['applicationRecords'], (result) => {
          const existing = result.applicationRecords || [];
          let merged;

          if (mode === 'replace') {
            // 全套替换
            merged = deduplicateRecords(incoming);
          } else if (mode === 'append') {
            // 直接追加，不去重
            merged = [...existing, ...incoming];
            merged.sort((a, b) => (Number(b.id) || 0) - (Number(a.id) || 0));
          } else {
            // 默认：智能合并（双重去重）
            const combined = [...existing, ...incoming];
            // 同 id 的以文件里的为准（比如在 Excel 里加了备注）
            const idMap = {};
            existing.forEach(r => { idMap[String(r.id)] = r; });
            incoming.forEach(r => { idMap[String(r.id)] = r; }); // 导入的覆盖
            merged = deduplicateRecords(Object.values(idMap));
          }

          chrome.storage.local.set({ applicationRecords: merged }, () => {
            const modeLabel = { smart:'智能合并', replace:'覆盖替换', append:'追加全部' }[mode];
            showStatus(`✅ ${modeLabel}完成，共 ${merged.length} 条记录`);
            renderRecordsTab();
            autoSaveToLocal(merged);
          });
        });
      } catch (err) {
        console.error('Import error:', err);
        showStatus('❌ 文件读取失败，请确认格式正确');
      }
    };

    if (isXlsx) {
      reader.readAsArrayBuffer(file);
    } else {
      reader.readAsText(file, 'utf-8');
    }
  };
  input.click();
}

/**
 * 弹出导入模式选择层（内联 HTML，不用系统 prompt）
 * 返回 Promise<'smart'|'replace'|'append'|null>
 */
function chooseImportMode(incomingCount) {
  return new Promise(resolve => {
    // 如果已经有弹层就先关掉
    document.getElementById('importModeOverlay')?.remove();

    const overlay = document.createElement('div');
    overlay.id = 'importModeOverlay';
    overlay.style.cssText = `
      position:fixed;inset:0;background:rgba(15,23,42,0.6);
      z-index:3000;display:flex;align-items:center;justify-content:center;
    `;
    overlay.innerHTML = `
      <div style="background:white;border-radius:14px;padding:20px;width:320px;
                  box-shadow:0 20px 60px rgba(0,0,0,0.3);animation:modalIn .2s ease;">
        <h3 style="font-size:15px;font-weight:700;color:#1e293b;margin-bottom:6px;">
          📂 选择导入模式
        </h3>
        <p style="font-size:12px;color:#94a3b8;margin-bottom:14px;">
          文件内共 <b>${incomingCount}</b> 条记录
        </p>
        <div style="display:flex;flex-direction:column;gap:8px;">
          <button id="imode-smart" style="padding:9px 12px;border:1.5px solid #2563eb;
            border-radius:8px;background:#eff6ff;color:#1d4ed8;font-size:13px;
            font-weight:600;cursor:pointer;text-align:left;">
            ⚡ 智能合并（推荐）
            <span style="font-weight:400;font-size:11px;color:#64748b;display:block;margin-top:2px;">
              公司+岗位+时间去重，Excel 修改的内容优先
            </span>
          </button>
          <button id="imode-replace" style="padding:9px 12px;border:1.5px solid #e2e8f0;
            border-radius:8px;background:white;color:#475569;font-size:13px;
            font-weight:600;cursor:pointer;text-align:left;">
            🗑 覆盖替换
            <span style="font-weight:400;font-size:11px;color:#94a3b8;display:block;margin-top:2px;">
              删除当前全部，只保留文件里的
            </span>
          </button>
          <button id="imode-append" style="padding:9px 12px;border:1.5px solid #e2e8f0;
            border-radius:8px;background:white;color:#475569;font-size:13px;
            font-weight:600;cursor:pointer;text-align:left;">
            ➕ 全部追加
            <span style="font-weight:400;font-size:11px;color:#94a3b8;display:block;margin-top:2px;">
              不去重，全部导入（可能产生重复）
            </span>
          </button>
        </div>
        <button id="imode-cancel" style="width:100%;margin-top:10px;padding:7px;
          border:none;border-radius:7px;background:#f1f5f9;color:#64748b;
          font-size:12px;cursor:pointer;">取消</button>
      </div>
    `;
    document.body.appendChild(overlay);

    const close = (val) => { overlay.remove(); resolve(val); };
    overlay.querySelector('#imode-smart'  ).onclick = () => close('smart');
    overlay.querySelector('#imode-replace').onclick = () => close('replace');
    overlay.querySelector('#imode-append' ).onclick = () => close('append');
    overlay.querySelector('#imode-cancel' ).onclick = () => close(null);
    overlay.onclick = (e) => { if (e.target === overlay) close(null); };
  });
}

// ─────────────────────────────────────────
//  RECORDS TAB RENDER
// ─────────────────────────────────────────
function renderRecordsTab() {
  chrome.storage.local.get(['applicationRecords'], (result) => {
    const records = result.applicationRecords || [];
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
  });
}

function deleteRecord(recordId) {
  chrome.storage.local.get(['applicationRecords'], (result) => {
    const records = (result.applicationRecords || []).filter(r => r.id !== recordId);
    chrome.storage.local.set({ applicationRecords: records }, () => {
      renderRecordsTab();
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
      renderRecordsTab();
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

/** 对当前存储里的所有记录执行双重去重，直接保存回去 */
function deduplicateNow() {
  chrome.storage.local.get(['applicationRecords'], (result) => {
    const records = result.applicationRecords || [];
    const before = records.length;
    const deduped = deduplicateRecords(records);
    const removed = before - deduped.length;
    chrome.storage.local.set({ applicationRecords: deduped }, () => {
      if (removed === 0) {
        showStatus('✅ 没有重复记录，无需去重');
      } else {
        showStatus(`✅ 已去除 ${removed} 条重复，剩余 ${deduped.length} 条`);
        autoSaveToLocal(deduped);
      }
      renderRecordsTab();
    });
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

    // ── Sheet2：可编辑回传版（含隐藏 __id__ 列，改完可导回扩展）──
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
      XLSX.utils.book_append_sheet(wb, ws2, '📑 详细记录（可编辑后导回）');

      const fileName = `投递记录_${new Date().toLocaleDateString('zh-CN').replace(/\//g,'-')}.xlsx`;
      XLSX.writeFile(wb, fileName);
      showStatus(`✅ 已导出 ${records.length} 条，Sheet2 改完可直接导回`);
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
