// content.js - 核心表单填充逻辑，支持多条经历智能匹配

// 字段映射字典 - 扩展版
// 需要排除的上下文关键词（如果出现这些词，说明不是我们要填的字段）
const EXCLUDE_CONTEXTS = {
  company: ['家庭', '家属', '父亲', '母亲', '配偶', '紧急联系', '紧急联络', '科研', '论文', '项目', '校园经历'],
  position: ['家庭', '家属', '父亲', '母亲', '配偶', '科研', '论文'],
  job: ['实习', '工作经历', '社会实践', '科研'],
  type: ['工作', '实习', '岗位', '职位', '科研', '奖励', '证书', '荣誉'],  // 语言类型不应出现在这些区域
  level: ['工作', '实习', '岗位', '职位', '科研', '论文', '奖励', '证书', '荣誉'],  // 语言成绩不应出现在这些区域
  certName: ['工作', '实习', '单位', '社会实践'],  // 证书名称不应出现在工作区域
  thesis: ['科研项目'],  // 毕业论文不应匹配"科研项目/论文"这种独立字段
  fullName: ['奖励', '证书', '荣誉', '奖项', '项目', '论文', '成果'],  // 姓名不应出现在这些区域
};

const FIELD_MAPPING = {
  // ===== 静态/基础字段 =====
  // 姓名字段放在最前面优先匹配
  fullName: ['fullname', 'realname', 'applicantname', 'candidatename', 'truename', '姓名', '真实姓名', '申请人姓名', '您的姓名', '你的姓名', '本人姓名'],
  idType: ['idtype', 'documenttype', 'cardtype', '证件类型', '证件类别'],
  idCard: ['idcard', 'idnumber', 'identity', 'passport', 'cardno', 'cardnumber', '证件号码', '身份证', '证件号', '身份证号'],
  gender: ['gender', 'sex', '性别'],
  birthday: ['birthday', 'birth', 'born', 'birthdate', 'dateofbirth', '出生日期', '出生年月', '生日'],
  nation: ['nation', 'nationality', 'ethnicity', 'ethnic', '民族', '国籍'],
  weight: ['weight', '体重'],
  height: ['height', '身高'],
  hometown: ['hometown', 'native', 'nativeplace', 'hukou', '籍贯', '户籍', '生源地', '籍 贯', '户口所在地'],
  birthplace: ['birthplace', 'placeofbirth', '出生地'],
  marriage: ['marriage', 'marital', 'married', '婚姻状况', '婚姻', '婚否'],
  political: ['political', 'politics', 'party', '政治面貌', '党派', '政治身份'],
  email: ['email', 'mail', 'e-mail', '邮箱', '电子邮箱', '邮件', '电子邮件'],
  phone: ['phone', 'mobile', 'tel', 'telephone', 'cellphone', '手机', '手机号', '手机号码', '电话', '联系电话'],
  currentAddress: ['address', 'currentaddress', 'location', '居住地址', '住所', '现居住地', '联系地址', '通讯地址', '住址'],
  expectCity: ['expectcity', 'expectedcity', 'workcity', 'targetcity', '期望城市', '面试期望城市', '意向城市', '工作城市', '期望工作地'],
  source: ['source', 'channel', 'howknow', '来源', '招聘信息来源', '获知渠道', '了解渠道'],
  hasWorked: ['hasworked', 'workexperience', 'hasworkexp', '是否参加过正式工作', '有无工作经验'],
  expectedSalary: ['salary', 'expectedsalary', 'expectsalary', 'pay', '薪资', '期望薪资', '期望年薪', '月薪', '薪酬', '初始预期薪资', '预期薪资', '薪资期望'],
  intro: ['intro', 'introduction', 'about', 'summary', 'selfdesc', 'selfintro', '自我介绍', '简介', '个人简介', '自我评价', '补充说明'],

  // ===== 岗位类型 =====
  positionType: ['positiontype', 'jobtype', 'jobcategory', '岗位类型', '职位类型', '工作类型', '岗位类别'],

  // ===== 教育经历子字段 =====
  school: ['school', 'university', '学校', '院校', '毕业院校', '学校名称'],
  degree: ['degree', 'education', '学历', '学位', '最高学历'],
  department: ['department', 'faculty', '院系', '学院', '学部'],
  major: ['major', 'specialty', '专业', '所学专业'],
  endDate: ['enddate', 'graduation', 'graduate', '毕业时间', '结束时间', '离校时间'],
  rank: ['rank', 'ranking', '专业排名', '排名', '绩点'],
  fulltime: ['fulltime', '全日制', '学习方式'],
  thesis: ['thesis', 'graduationdesign', '毕业设计', '毕业论文'],

  // ===== 工作/实习经历子字段（更严格的匹配）=====
  company: ['实习单位', '工作单位', '公司名称', '所在单位'],
  position: ['从事工作', '职务', '岗位名称', 'jobtitle'],
  time: ['起止时间', '工作时间', '实习时间'],
  desc: ['工作描述', '工作内容', '实习内容', '职责描述', '实践描述'],
  contact: ['证明人', '推荐人', 'reference', 'referee'],
  contactPhone: ['证明人电话', '推荐人电话', 'refphone'],

  // ===== 语言能力子字段（更严格）=====
  type: ['语言类型', '外语类别', '语种', '外语名称'],
  level: ['语言等级', '外语水平', '语言成绩', '掌握程度', '外语等级'],

  // ===== 证书/获奖子字段 =====
  certName: ['证书名称', '奖项名称', '荣誉名称', '获奖名称'],
  org: ['颁发机构', '授奖单位', '颁发单位', '发证机关'],

  // ===== 家庭成员子字段 =====
  relation: ['与本人关系', '关系', '称谓', '家庭关系'],
  familyName: ['家庭成员姓名', '家属姓名', '成员姓名'],
  job: ['工作单位及职务', '家属工作单位', '家庭成员工作'],
  familyPhone: ['家庭联系电话', '家庭电话', '家属电话', '家属联系方式']
};

// 字段对应的类别映射
const FIELD_TO_CATEGORY = {
  // 教育相关
  school: ['edu'],
  degree: ['edu'],
  department: ['edu'],
  major: ['edu'],
  endDate: ['edu'],
  rank: ['edu'],
  fulltime: ['edu'],
  thesis: ['edu'],

  // 工作/实习相关
  company: ['work', 'intern'],
  position: ['work', 'intern'],
  contact: ['work', 'intern'],
  contactPhone: ['work', 'intern'],
  time: ['work', 'intern'],
  desc: ['work', 'intern', 'project'],

  // 项目/证书相关
  certName: ['cert', 'project'],
  org: ['cert'],

  // 家庭相关
  relation: ['family'],
  familyName: ['family'],
  job: ['family'],
  familyPhone: ['family'],

  // 语言相关
  type: ['lang'],
  level: ['lang']
};

// 监听来自 Popup 的消息
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'FILL_FORM') {
    fillForm(request.data).then(count => {
      sendResponse({ success: true, count: count });
    });
    return true; 
  }
});

// 主填充函数
async function fillForm(data) {
  let filledCount = 0;
  // 追踪每个字段在页面上出现的次数
  const fieldCounters = {};
  // 记录已填充的元素，避免重复填充
  const filledElements = new Set();

  // 扩展选择器，支持更多 SPA 框架（飞书、钉钉等）
  const inputs = document.querySelectorAll(`
    input:not([type="hidden"]):not([type="submit"]):not([type="button"]):not([type="reset"]):not([type="file"]):not([type="checkbox"]):not([type="radio"]),
    textarea,
    select,
    [contenteditable="true"],
    [contenteditable="plaintext-only"],
    [role="textbox"],
    [data-testid*="input"],
    [class*="editor"]:not(script):not(style)
  `.replace(/\s+/g, ' ').trim());

  console.log('[EasyApply] 找到表单元素:', inputs.length);

  for (const input of inputs) {
    // 跳过不可见、禁用、只读或已填充的元素
    if (!isVisible(input) || input.disabled || input.readOnly) continue;
    if (filledElements.has(input)) continue;

    // 检查是否已有值（兼容 contenteditable）
    const currentValue = input.value || input.innerText || input.textContent || '';
    if (currentValue.trim() !== '' && currentValue.trim() !== 'Type here' && currentValue.trim() !== '请输入') continue;

    const attrStr = getElementSignature(input);
    let matched = false;

    console.log('[EasyApply] 检查元素:', attrStr.substring(0, 100));

    for (const [fieldType, keywords] of Object.entries(FIELD_MAPPING)) {
      if (matchesKeywords(attrStr, keywords)) {
        // 检查是否应该排除（上下文不匹配）
        if (shouldExclude(fieldType, attrStr)) {
          console.log('[EasyApply] 排除字段（上下文不匹配）:', fieldType);
          continue;
        }

        // 特殊处理：如果匹配到姓名，但上下文是"XX名称"类字段，则跳过
        if (fieldType === 'fullName' && isNonPersonNameField(attrStr)) {
          console.log('[EasyApply] 排除姓名字段（是其他名称类字段）');
          continue;
        }

        // 特殊处理：如果匹配到语言级别，但上下文是"XX级别"类字段，则跳过
        if (fieldType === 'level' && isNonLanguageLevelField(attrStr)) {
          console.log('[EasyApply] 排除语言级别字段（是其他级别类字段）');
          continue;
        }

        console.log('[EasyApply] 匹配到字段:', fieldType);

        // 1. 处理静态字段
        if (data[fieldType] && typeof data[fieldType] === 'string') {
          await setValue(input, data[fieldType]);
          filledElements.add(input);
          filledCount++;
          matched = true;
          console.log('[EasyApply] 填充静态字段:', fieldType, '=', data[fieldType]);
          break;
        }

        // 2. 处理动态列表字段
        const categories = FIELD_TO_CATEGORY[fieldType] || [];
        for (const cat of categories) {
          const list = data[cat];
          if (list && Array.isArray(list)) {
            // 初始化计数器
            const counterKey = `${cat}_${fieldType}`;
            const index = fieldCounters[counterKey] || 0;

            if (list[index]) {
              // 寻找对象中对应的属性 (匹配 "field-school" 这种格式)
              const val = list[index][`field-${fieldType}`];
              if (val) {
                await setValue(input, val);
                filledElements.add(input);
                fieldCounters[counterKey] = index + 1;
                filledCount++;
                matched = true;
                console.log('[EasyApply] 填充列表字段:', fieldType, '=', val);
                break;
              }
            }
          }
        }
        if (matched) break;
      }
    }
  }
  console.log('[EasyApply] 填充完成，共填充:', filledCount, '个字段');
  return filledCount;
}

// 统一设置值的方法
async function setValue(input, value) {
  if (input.tagName === 'SELECT') {
    setSelectValue(input, value);
  } else if (input.getAttribute('contenteditable') === 'true' || input.isContentEditable) {
    // 处理 contenteditable 元素（飞书等使用）
    input.focus();
    // 清空现有内容
    input.innerHTML = '';
    // 使用 document.execCommand 或直接设置（兼容性更好）
    try {
      document.execCommand('insertText', false, value);
    } catch (e) {
      input.innerText = value;
    }
    // 触发各种事件确保框架能检测到变化
    triggerEvent(input, 'input');
    triggerEvent(input, 'change');
    triggerEvent(input, 'blur');
    // 额外触发 compositionend 事件（某些框架需要）
    const compositionEvent = new CompositionEvent('compositionend', { data: value, bubbles: true });
    input.dispatchEvent(compositionEvent);
  } else {
    await simulateHumanTyping(input, value);
  }
}

function setSelectValue(selectElement, value) {
  const options = selectElement.options;
  const lowerValue = value.toLowerCase();
  for (let i = 0; i < options.length; i++) {
    const text = options[i].text.toLowerCase();
    const val = options[i].value.toLowerCase();
    if (text === lowerValue || val === lowerValue || text.includes(lowerValue) || lowerValue.includes(text)) {
      selectElement.selectedIndex = i;
      triggerEvent(selectElement, 'change', { bubbles: true });
      return;
    }
  }
}

function getElementSignature(input) {
  const parts = [input.id, input.name, input.className, input.placeholder, input.getAttribute('aria-label'), input.getAttribute('data-field'), input.getAttribute('data-name'), input.getAttribute('title')];
  try {
    if (input.labels && input.labels.length > 0) parts.push(input.labels[0].textContent);
  } catch (e) {}

  // 获取 label[for] 关联的标签
  if (input.id) {
    const labelFor = document.querySelector(`label[for="${input.id}"]`);
    if (labelFor) parts.push(labelFor.textContent);
  }

  // 向上遍历父元素，寻找标签文本（支持飞书等 SPA 框架）
  let current = input;
  for (let i = 0; i < 5 && current; i++) {
    const parent = current.parentElement;
    if (!parent) break;

    // 查找同级的前一个元素（通常是标签）
    const prev = current.previousElementSibling;
    if (prev) {
      const prevText = prev.textContent?.trim();
      if (prevText && prevText.length < 50) {
        parts.push(prevText);
      }
    }

    // 查找父元素中的标签元素
    const labelEl = parent.querySelector('label, [class*="label"], [class*="title"], [class*="question"], [class*="field-name"]');
    if (labelEl && labelEl !== input) {
      parts.push(labelEl.textContent?.trim());
    }

    // 获取父元素自身的文本（排除子元素）
    const clone = parent.cloneNode(true);
    clone.querySelectorAll('input, textarea, select, [contenteditable]').forEach(el => el.remove());
    const parentText = clone.textContent?.trim().substring(0, 100);
    if (parentText) parts.push(parentText);

    current = parent;
  }

  return parts.filter(Boolean).join(' ').toLowerCase();
}

function matchesKeywords(str, keywords) {
  return keywords.some(k => str.includes(k.toLowerCase()));
}

// 检查是否应该排除这个字段（基于上下文）
function shouldExclude(fieldType, contextStr) {
  const excludeList = EXCLUDE_CONTEXTS[fieldType];
  if (!excludeList) return false;
  const shouldEx = excludeList.some(ex => contextStr.includes(ex.toLowerCase()));
  if (shouldEx) {
    console.log('[EasyApply] 排除检查:', fieldType, '因为上下文包含排除词');
  }
  return shouldEx;
}

// 检查是否是"名称"类字段但不是"姓名"（避免奖励名称、证书名称等被误匹配）
function isNonPersonNameField(contextStr) {
  // 如果上下文包含这些词 + "名称"，则不是人名字段
  const prefixes = ['奖励', '证书', '项目', '论文', '成果', '荣誉', '奖项', '课题', '作品', '专利'];
  return prefixes.some(prefix => contextStr.includes(prefix.toLowerCase() + '名称') ||
                                  contextStr.includes(prefix.toLowerCase() + ' 名 称'));
}

// 检查是否是"级别"类字段但不是语言级别
function isNonLanguageLevelField(contextStr) {
  const prefixes = ['奖励', '证书', '荣誉', '奖项', '职称', '职务', '岗位', '学历'];
  return prefixes.some(prefix => contextStr.includes(prefix.toLowerCase() + '级别') ||
                                  contextStr.includes(prefix.toLowerCase() + ' 级 别'));
}

function isVisible(el) {
  const style = window.getComputedStyle(el);
  return style.display !== 'none' && style.visibility !== 'hidden' && el.offsetParent !== null;
}

async function simulateHumanTyping(element, text) {
  element.focus();
  element.value = '';
  triggerEvent(element, 'input');
  
  for (const char of text) {
    const delay = Math.floor(Math.random() * 10) + 5; // 5-15ms，比原来快5倍
    await new Promise(r => setTimeout(r, delay));
    element.value += char;
    triggerEvent(element, 'input', { bubbles: true });
  }
  triggerEvent(element, 'change', { bubbles: true });
  element.blur();
}

function triggerEvent(el, type, options = {}) {
  const event = new Event(type, Object.assign({ bubbles: true, cancelable: true }, options));
  el.dispatchEvent(event);
}

