/**
 * Claude Code 工具日志查看器 - Node 本地服务
 * 与 Python server.py 行为一致：从 ~/.claude/projects 读 transcript，提供相同 API 与配置（explain-config、项目显示名等）。
 * 额外支持 ~/.claude/tool-logs 的 /api/sessions、/api/sessions/:id/log（可选）。
 */
const fs = require('fs');
const path = require('path');
const http = require('http');
const crypto = require('crypto');

const TOOL_LOGS_DIR = process.env.CLAUDE_TOOL_LOG_DIR || path.join(process.env.USERPROFILE || process.env.HOME || '.', '.claude', 'tool-logs');
const CLAUDE_PROJECTS_DIR = path.resolve(process.env.CLAUDE_PROJECTS_DIR || path.join(process.env.USERPROFILE || process.env.HOME || '.', '.claude', 'projects'));
const PORT = parseInt(process.env.CLAUDE_LOG_VIEWER_PORT || '3847', 10);
const VIEWER_DIR = path.join(__dirname, 'public');
const LOG_SCHEMA_VERSION = 1;
const TIMELINE_CACHE_TTL_MS = 2000;

let _timelineCache = { signature: '', builtAt: 0, data: null };

function loadProjectDisplayNames() {
  const p = path.join(__dirname, 'projects-display-names.json');
  if (!fs.existsSync(p)) return {};
  try {
    const raw = fs.readFileSync(p, 'utf8');
    const obj = JSON.parse(raw);
    return obj && typeof obj === 'object' ? obj : {};
  } catch (_) {
    return {};
  }
}

function loadExplainConfig() {
  const envApiUrl = (process.env.EXPLAIN_API_URL || '').trim();
  const envApiKey = (process.env.EXPLAIN_API_KEY || '').trim();
  const envModel = (process.env.EXPLAIN_MODEL || '').trim();
  const configPath = path.join(__dirname, 'explain-config.json');
  let fileConfig = {};
  if (fs.existsSync(configPath)) {
    try {
      fileConfig = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    } catch (_) {}
  }
  const rawUrl = envApiUrl || (fileConfig.apiUrl || '');
  return {
    apiUrl: rawUrl,
    apiKey: envApiKey || (fileConfig.apiKey || ''),
    model: envModel || (fileConfig.model || 'qwen-turbo')
  };
}

function ensureChatCompletionsUrl(url) {
  const s = (url || '').trim();
  if (!s) return '';
  if (s.endsWith('/chat/completions')) return s;
  return s.replace(/\/+$/, '') + '/chat/completions';
}

function sanitizeId(id) {
  if (!id || typeof id !== 'string') return '';
  return id.replace(/[^a-zA-Z0-9-_]/g, '');
}

// ---------- projects/timeline API (与 Python server 同构，从 ~/.claude/projects 读 transcript) ----------
function sha1Text(text) {
  return crypto.createHash('sha1').update(String(text || ''), 'utf8').digest('hex');
}
function jsonDumpsStable(value) {
  try {
    if (value === null || value === undefined) return 'null';
    if (typeof value !== 'object') return JSON.stringify(value);
    if (Array.isArray(value)) return '[' + value.map(jsonDumpsStable).join(',') + ']';
    const keys = Object.keys(value).sort();
    return '{' + keys.map(k => JSON.stringify(k) + ':' + jsonDumpsStable(value[k])).join(',') + '}';
  } catch (_) {
    return String(value);
  }
}
function safeJsonLoads(text) {
  try {
    return JSON.parse(text || '{}');
  } catch (_) {
    return null;
  }
}
function extractTextFromContent(content) {
  if (typeof content === 'string') return content;
  if (!Array.isArray(content)) return '';
  const parts = [];
  for (const item of content) {
    if (typeof item === 'string') {
      parts.push(item);
      continue;
    }
    if (!item || typeof item !== 'object') continue;
    const t = item.type;
    if (t === 'text' || t === 'thinking') {
      const text = item.text || item.thinking;
      if (text) parts.push(String(text));
    }
  }
  return parts.filter(Boolean).join('\n').trim();
}
function normalizeToolOutput(value) {
  if (typeof value === 'string') {
    const s = value.trim();
    if (!s) return '';
    const j = safeJsonLoads(s);
    return j != null ? j : s;
  }
  return value;
}
function buildEvent(opts) {
  const toolInput = opts.toolInput != null ? opts.toolInput : {};
  const toolOutput = normalizeToolOutput(opts.toolOutput);
  const data = {
    schemaVersion: LOG_SCHEMA_VERSION,
    sessionId: opts.sessionId || '',
    traceId: opts.traceId || '',
    source: 'transcript',
    sourceConfidence: 100,
    eventType: opts.eventType || 'system',
    toolName: opts.toolName || '',
    toolInput: toolInput,
    toolOutput: toolOutput != null ? toolOutput : {},
    error: opts.error || '',
    content: opts.content || '',
    timestamp: (opts.timestamp || '').trim(),
    cwd: opts.cwd || '',
    raw: opts.raw != null ? opts.raw : {},
  };
  const digest = [
    data.sessionId,
    data.eventType,
    data.traceId,
    (data.timestamp || '').slice(0, 19),
    data.toolName,
    sha1Text(jsonDumpsStable(data.toolInput)).slice(0, 12),
    sha1Text(jsonDumpsStable(data.toolOutput)).slice(0, 12),
    sha1Text((data.content || '').slice(0, 320)).slice(0, 12),
  ].join('|');
  data.eventId = sha1Text(digest).slice(0, 20);
  return data;
}
function eventDedupeKey(event) {
  const traceId = String(event.traceId || '').trim();
  if (traceId) return `${event.eventType}|${traceId}`;
  return [
    event.eventType || '',
    event.toolName || '',
    (event.timestamp || '').slice(0, 19),
    sha1Text(jsonDumpsStable(event.toolInput || {})).slice(0, 8),
    sha1Text(jsonDumpsStable(event.toolOutput || {})).slice(0, 8),
    sha1Text(String(event.content || '').slice(0, 220)).slice(0, 8),
  ].join('|');
}
function parseTranscriptLine(obj, fallbackSession) {
  const result = [];
  let sessionId = String(obj.sessionId || fallbackSession || '');
  const timestamp = String(obj.timestamp || '');
  const cwd = String(obj.cwd || '');
  const lineType = String(obj.type || '').trim().toLowerCase();

  if (!lineType && typeof obj.role === 'string') {
    const role = String(obj.role).toLowerCase();
    const message = obj.message || {};
    let content = '';
    if (message && typeof message === 'object') content = extractTextFromContent(message.content);
    const eventType = role === 'user' ? 'user_input' : 'assistant_output';
    if (content) {
      result.push(buildEvent({ sessionId, eventType, timestamp, content, cwd, raw: obj }));
    }
    return result;
  }

  if (lineType === 'user') {
    const message = obj.message || {};
    if (message && typeof message === 'object') {
      const content = message.content;
      if (Array.isArray(content)) {
        for (const item of content) {
          if (!item || typeof item !== 'object') continue;
          if (item.type === 'tool_result') {
            const traceId = String(item.tool_use_id || '');
            const output = item.content;
            const error = item.is_error === true ? 'tool_result_error' : '';
            const eventType = error ? 'tool_failure' : 'post_tool';
            result.push(buildEvent({ sessionId, eventType, timestamp, traceId, toolOutput: output, error, cwd, raw: obj }));
          }
        }
        const plain = extractTextFromContent(content);
        if (plain) result.push(buildEvent({ sessionId, eventType: 'user_input', timestamp, content: plain, cwd, raw: obj }));
      } else if (typeof content === 'string') {
        result.push(buildEvent({ sessionId, eventType: 'user_input', timestamp, content, cwd, raw: obj }));
      }
    }
    return result;
  }

  if (lineType === 'assistant') {
    const message = obj.message || {};
    const msgContent = message && typeof message === 'object' ? message.content : null;
    if (Array.isArray(msgContent)) {
      for (const item of msgContent) {
        if (!item || typeof item !== 'object') continue;
        const ctype = String(item.type || '');
        if (ctype === 'tool_use') {
          result.push(buildEvent({
            sessionId,
            eventType: 'pre_tool',
            timestamp,
            traceId: String(item.id || ''),
            toolName: String(item.name || ''),
            toolInput: item.input || {},
            cwd,
            raw: obj,
          }));
        } else if (ctype === 'text') {
          const text = String(item.text || '');
          if (text.trim()) {
            result.push(buildEvent({ sessionId, eventType: 'assistant_output', timestamp, content: text, cwd, raw: obj }));
          }
        }
      }
    } else if (typeof msgContent === 'string' && msgContent.trim()) {
      result.push(buildEvent({ sessionId, eventType: 'assistant_output', timestamp, content: msgContent, cwd, raw: obj }));
    }
    return result;
  }

  if (lineType === 'file-history-snapshot') {
    const snap = obj.snapshot || {};
    result.push(buildEvent({
      sessionId,
      eventType: 'system',
      timestamp: timestamp || String(snap.timestamp || ''),
      content: 'file-history-snapshot',
      cwd,
      raw: obj,
    }));
  }
  return result;
}
function projectKeyForFile(filePath) {
  try {
    const rel = path.relative(CLAUDE_PROJECTS_DIR, path.resolve(filePath));
    const parts = rel.split(path.sep).filter(Boolean);
    if (parts.length) return parts[0];
  } catch (_) {}
  return 'unknown-project';
}
function parseTranscriptFile(filePath) {
  const events = [];
  let sessionId = path.basename(filePath, '.jsonl');
  const content = fs.readFileSync(filePath, 'utf8');
  for (const rawLine of content.split('\n')) {
    const line = rawLine.trim();
    if (!line) continue;
    const obj = safeJsonLoads(line);
    if (!obj || typeof obj !== 'object') continue;
    sessionId = String(obj.sessionId || sessionId);
    events.push(...parseTranscriptLine(obj, sessionId));
  }
  return { events, sessionId };
}
function discoverProjectTranscripts() {
  const files = [];
  if (!fs.existsSync(CLAUDE_PROJECTS_DIR)) return { files: [], signature: '' };
  function walk(dir) {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const e of entries) {
      const full = path.join(dir, e.name);
      if (e.isDirectory()) {
        if (e.name.toLowerCase() !== 'subagents') walk(full);
      } else if (e.isFile() && e.name.endsWith('.jsonl')) {
        if (!path.relative(CLAUDE_PROJECTS_DIR, full).split(path.sep).some(p => p.toLowerCase() === 'subagents')) {
          files.push(path.resolve(full));
        }
      }
    }
  }
  walk(CLAUDE_PROJECTS_DIR);
  const records = files.map(fp => {
    try {
      const st = fs.statSync(fp);
      return [fp, (st.mtime && st.mtime.getTime ? st.mtime.getTime() : 0), st.size];
    } catch (_) {
      return [fp, 0, 0];
    }
  });
  const signature = sha1Text(JSON.stringify(records.sort((a, b) => a[0].localeCompare(b[0]))));
  return { files: files.sort(), signature };
}
function buildTimelineData() {
  const buildStart = Date.now();
  const { files, signature } = discoverProjectTranscripts();
  const now = Date.now();
  if (_timelineCache.data && _timelineCache.signature === signature && (now - _timelineCache.builtAt) < TIMELINE_CACHE_TTL_MS) {
    return _timelineCache.data;
  }
  const displayNames = loadProjectDisplayNames();
  const projectDisplayName = (id) => (displayNames[id] != null && String(displayNames[id]).trim()) ? String(displayNames[id]).trim() : id;
  const eventsBySession = {};
  const sessionMeta = {};
  const projects = {};
  for (const filePath of files) {
    let parsed;
    try {
      parsed = parseTranscriptFile(filePath);
    } catch (_) {
      continue;
    }
    const { events, sessionId: sid } = parsed;
    const projectId = projectKeyForFile(filePath);
    let st;
    try {
      st = fs.statSync(filePath);
    } catch (_) {
      st = null;
    }
    if (!projects[projectId]) {
      projects[projectId] = { id: projectId, name: projectDisplayName(projectId), sessionCount: 0, eventCount: 0, mtime: '' };
    }
    if (sid) {
      const meta = sessionMeta[sid] || {
        id: sid,
        filename: path.basename(filePath),
        mtime: '',
        size: 0,
        cwd: null,
        projectId,
        projectName: projectDisplayName(projectId),
      };
      sessionMeta[sid] = meta;
      meta.projectId = projectId;
      meta.projectName = projectDisplayName(projectId);
      meta.filename = path.basename(filePath);
      if (st) {
        meta.size = st.size;
        meta.mtime = st.mtime ? new Date(st.mtime).toISOString().replace(/\.000Z$/, 'Z') : '';
      }
    }
    for (const event of events) {
      const sid2 = event.sessionId || sid || path.basename(filePath, '.jsonl');
      event.sessionId = sid2;
      if (!eventsBySession[sid2]) eventsBySession[sid2] = [];
      eventsBySession[sid2].push(event);
    }
  }
  const sessions = {};
  const sessionsByProject = {};
  for (const [sid, rawEvents] of Object.entries(eventsBySession)) {
    const dedupeMap = {};
    let duplicateCount = 0;
    for (const event of rawEvents) {
      const key = eventDedupeKey(event);
      if (dedupeMap[key]) duplicateCount++;
      else dedupeMap[key] = event;
    }
    const mergedEvents = Object.values(dedupeMap);
    mergedEvents.sort((a, b) => (b.timestamp || '').localeCompare(a.timestamp || ''));
    const preIds = new Set(mergedEvents.filter(e => e.eventType === 'pre_tool' && (e.traceId || '').trim()).map(e => e.traceId));
    const postIds = new Set(mergedEvents.filter(e => (e.eventType === 'post_tool' || e.eventType === 'tool_failure') && (e.traceId || '').trim()).map(e => e.traceId));
    const missingPost = [...preIds].filter(id => !postIds.has(id)).sort();
    const health = {
      totalEvents: mergedEvents.length,
      preToolCount: mergedEvents.filter(e => e.eventType === 'pre_tool').length,
      postToolCount: mergedEvents.filter(e => e.eventType === 'post_tool').length,
      failureCount: mergedEvents.filter(e => e.eventType === 'tool_failure').length,
      userInputCount: mergedEvents.filter(e => e.eventType === 'user_input').length,
      assistantOutputCount: mergedEvents.filter(e => e.eventType === 'assistant_output').length,
      duplicateCollapsed: duplicateCount,
      missingPostCount: missingPost.length,
      missingPostTraceIds: missingPost.slice(0, 30),
      sourceCountsBeforeMerge: { transcript: rawEvents.length },
    };
    const tools = [...new Set(mergedEvents.map(e => e.toolName).filter(Boolean))].sort();
    const meta = sessionMeta[sid] || { id: sid, filename: sid + '.txt', mtime: '', size: 0, cwd: null };
    let lastActivity = meta.mtime || '';
    if (mergedEvents.length && mergedEvents[0].timestamp) lastActivity = mergedEvents[0].timestamp;
    meta.mtime = lastActivity;
    sessions[sid] = {
      meta,
      events: mergedEvents,
      health,
      tools,
      projectId: meta.projectId || 'unknown-project',
    };
    const projectId = meta.projectId || 'unknown-project';
    sessionsByProject[projectId] = sessionsByProject[projectId] || [];
    sessionsByProject[projectId].push({
      id: sid,
      projectId,
      projectName: meta.projectName || projectDisplayName(projectId),
      mtime: lastActivity,
      cwd: meta.cwd,
      size: meta.size || 0,
      eventCount: mergedEvents.length,
      health: { missingPostCount: health.missingPostCount, failureCount: health.failureCount, duplicateCollapsed: health.duplicateCollapsed },
    });
    const p = projects[projectId] || { id: projectId, name: projectDisplayName(projectId), sessionCount: 0, eventCount: 0, mtime: '' };
    p.sessionCount = (p.sessionCount || 0) + 1;
    p.eventCount = (p.eventCount || 0) + mergedEvents.length;
    if (String(lastActivity) > String(p.mtime || '')) p.mtime = lastActivity;
    projects[projectId] = p;
  }
  for (const pid of Object.keys(sessionsByProject)) {
    sessionsByProject[pid].sort((a, b) => String(b.mtime || '').localeCompare(a.mtime || ''));
  }
  const projectsIndex = Object.values(projects).sort((a, b) => String(b.mtime || '').localeCompare(a.mtime || ''));
  const data = { projects, projectsIndex, sessions, sessionsByProject };
  _timelineCache = { data, signature, builtAt: now };
  const elapsed = Date.now() - buildStart;
  console.log(`[timeline] build ${elapsed}ms, ${files.length} files, ${Object.keys(sessions).length} sessions`);
  return data;
}

const mime = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.ico': 'image/x-icon',
};

const server = http.createServer((req, res) => {
  const url = new URL(req.url || '', `http://localhost:${PORT}`);
  const pathname = url.pathname;

  if (pathname === '/api/sessions') {
    if (req.method !== 'GET') {
      res.writeHead(405);
      res.end();
      return;
    }
    try {
      if (!fs.existsSync(TOOL_LOGS_DIR)) {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify([]));
        return;
      }
      function readCwdFromLog(filePath) {
        try {
          const buf = Buffer.allocUnsafe(4096);
          const fd = fs.openSync(filePath, 'r');
          const n = fs.readSync(fd, buf, 0, 4096, 0);
          fs.closeSync(fd);
          const head = buf.slice(0, n).toString('utf8');
          const m = head.match(/\|\s*cwd:\s*([^\n]+)/);
          return m ? m[1].trim() : null;
        } catch (_) {
          return null;
        }
      }

      const files = fs.readdirSync(TOOL_LOGS_DIR)
        .filter((f) => f.endsWith('.txt'))
        .map((f) => {
          const fp = path.join(TOOL_LOGS_DIR, f);
          const stat = fs.statSync(fp);
          const id = f.slice(0, -4);
          const cwd = readCwdFromLog(fp);
          return {
            id,
            filename: f,
            mtime: stat.mtime.toISOString(),
            size: stat.size,
            cwd: cwd || null,
          };
        })
        .sort((a, b) => new Date(b.mtime) - new Date(a.mtime));
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(files));
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: String(err.message) }));
    }
    return;
  }

  if (pathname === '/api/explain-config') {
    const configPath = path.join(__dirname, 'explain-config.json');
    if (req.method === 'GET') {
      try {
        const raw = fs.existsSync(configPath)
          ? fs.readFileSync(configPath, 'utf8')
          : '{}';
        const j = JSON.parse(raw);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          apiUrl: j.apiUrl || '',
          apiKey: j.apiKey || '',
          model: j.model || 'qwen-turbo'
        }));
      } catch (err) {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ apiUrl: '', apiKey: '', model: 'qwen-turbo' }));
      }
      return;
    }
    if (req.method === 'POST') {
      let body = '';
      req.on('data', (chunk) => { body += chunk; });
      req.on('end', () => {
        const send = (status, obj) => {
          try {
            if (!res.writableEnded) {
              res.writeHead(status, { 'Content-Type': 'application/json' });
              res.end(JSON.stringify(obj));
            }
          } catch (e) {}
        };
        try {
          const j = JSON.parse(body || '{}');
          let apiUrl = (j.apiUrl || j.baseUrl || '').trim();
          if (apiUrl && !apiUrl.endsWith('/chat/completions')) {
            apiUrl = apiUrl.replace(/\/+$/, '') + '/chat/completions';
          }
          const config = {
            apiUrl: apiUrl || '',
            apiKey: (j.apiKey || '').trim(),
            model: (j.model || 'qwen-turbo').trim()
          };
          const dir = path.dirname(configPath);
          if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
          fs.writeFileSync(configPath, JSON.stringify(config, null, 2), 'utf8');
          send(200, { ok: true });
        } catch (err) {
          send(400, { error: String(err.message) });
        }
      });
      return;
    }
    res.writeHead(405);
    res.end();
    return;
  }

  if (pathname === '/api/explain' && req.method === 'POST') {
    let body = '';
    req.on('data', (chunk) => { body += chunk; });
    req.on('end', () => {
      const config = loadExplainConfig();
      if (!config.apiUrl || !config.apiKey) {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: '未配置解说 API。请在 log-viewer/explain-config.json 中填写 apiUrl、apiKey，或设置环境变量 EXPLAIN_API_URL、EXPLAIN_API_KEY。' }));
        return;
      }
      let payload;
      try {
        payload = JSON.parse(body);
      } catch (_) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Invalid JSON' }));
        return;
      }
      const toolName = payload.toolName || payload.tool_name || '?';
      const toolInput = payload.toolInput || payload.tool_input || {};
      const toolResponse = payload.toolResponse ?? payload.tool_response ?? {};
      const event = payload.event || '';
      const inputSummary = typeof toolInput === 'string' ? toolInput.slice(0, 500) : JSON.stringify(toolInput).slice(0, 500);
      const outputSummary = typeof toolResponse === 'string' ? toolResponse.slice(0, 800) : JSON.stringify(toolResponse).slice(0, 800);
      const prompt = `你是一个简洁的日志解说员。用一两句中文说明下面这条「Claude Code 工具调用」在做什么、结果如何。不要复述 JSON，只输出解说本身。

事件: ${event}
工具: ${toolName}
输入摘要: ${inputSummary}
输出摘要: ${outputSummary}

请只回复一句解说：`;

      const reqBody = JSON.stringify({
        model: config.model,
        messages: [{ role: 'user', content: prompt }],
        max_tokens: 150
      });
      const apiUrl = ensureChatCompletionsUrl(config.apiUrl);
      const u = new URL(apiUrl);
      const opt = {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + config.apiKey,
          'Content-Length': Buffer.byteLength(reqBody, 'utf8')
        }
      };
      const client = u.protocol === 'https:' ? require('https') : require('http');
      const apiReq = client.request(apiUrl, { ...opt, method: 'POST' }, (apiRes) => {
        let data = '';
        apiRes.on('data', (c) => { data += c; });
        apiRes.on('end', () => {
          const send = (status, obj) => {
            if (!res.writableEnded) {
              res.writeHead(status, { 'Content-Type': 'application/json' });
              res.end(JSON.stringify(obj));
            }
          };
          try {
            let out;
            try {
              out = data ? JSON.parse(data) : {};
            } catch (_) {
              send(200, { error: '解说 API 返回非 JSON: ' + (data ? data.slice(0, 200) : '空响应') });
              return;
            }
            if (apiRes.statusCode >= 400) {
              const msg = out.message || out.error?.message || out.msg || out.error || String(out.code || apiRes.statusCode);
              send(200, { error: '解说 API HTTP ' + apiRes.statusCode + ': ' + msg });
              return;
            }
            if (out.code && String(out.code) !== '0' && String(out.code) !== '') {
              const msg = out.message || out.error?.message || out.msg || out.error || String(out.code);
              send(200, { error: 'API 错误: ' + msg });
              return;
            }
            if (out.error && (out.error.code || out.error.message)) {
              const msg = out.error.message || out.error.code || JSON.stringify(out.error);
              send(200, { error: 'API 错误: ' + msg });
              return;
            }
            let text = '';
            if (out.output && out.output.choices && out.output.choices[0]) {
              const m = out.output.choices[0].message || out.output.choices[0];
              if (Array.isArray(m.content)) {
                text = m.content.map((x) => (typeof x === 'string' ? x : x.text || '')).join('').trim();
              } else {
                text = (m.content || m.text || '').trim();
              }
            }
            if (!text && out.output) {
              const o = out.output;
              if (typeof o === 'string') text = o.trim();
              else if (o.text) text = String(o.text).trim();
              else if (o.choices && o.choices[0]) {
                const m = o.choices[0].message || o.choices[0];
                text = (m.content || m.text || '').trim();
              }
            }
            if (!text && out.choices && out.choices[0]) {
              const msg = out.choices[0].message || out.choices[0];
              if (Array.isArray(msg.content)) {
                text = msg.content.map((x) => (typeof x === 'string' ? x : x.text || '')).join('').trim();
              } else {
                text = (msg.content || msg.text || '').trim();
              }
            }
            if (!text) text = (out.content || out.text || '').trim();
            if (!text && out.result) {
              const r = out.result;
              text = (r.output && (typeof r.output === 'string' ? r.output : r.output.text || r.output.content)) || r.text || '';
              text = String(text).trim();
            }
            send(200, { explanation: text || '（模型未返回文本，请检查 API 与模型）' });
          } catch (e) {
            send(200, { error: 'API 返回解析失败: ' + e.message });
          }
        });
      });
      apiReq.on('error', (e) => {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: '请求解说 API 失败: ' + e.message }));
      });
      apiReq.write(reqBody);
      apiReq.end();
    });
    return;
  }

  if (pathname === '/api/question' && req.method === 'POST') {
    let body = '';
    req.on('data', (chunk) => { body += chunk; });
    req.on('end', () => {
      const config = loadExplainConfig();
      if (!config.apiUrl || !config.apiKey) {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: '未配置解说 API。请在 log-viewer/explain-config.json 中填写 apiUrl、apiKey，或设置环境变量 EXPLAIN_API_URL、EXPLAIN_API_KEY。' }));
        return;
      }
      let payload;
      try {
        payload = JSON.parse(body || '{}');
      } catch (_) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Invalid JSON' }));
        return;
      }
      const question = (payload.question || '').trim();
      const logJson = (payload.logJson || '').trim();
      if (!question) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: '请提供问题' }));
        return;
      }
      if (!logJson) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: '请提供日志内容' }));
        return;
      }
      const prompt = `你是一个 Claude Code 日志分析专家。用户对一条工具调用日志有疑问，请根据日志内容回答用户的问题。\n\n日志内容:\n${logJson.slice(0, 3000)}\n\n用户问题: ${question}\n\n请根据日志内容给出详细、准确的中文回答。如果日志中没有足够信息回答，请说明需要查看更多信息：`;
      const reqBody = JSON.stringify({
        model: config.model,
        messages: [{ role: 'user', content: prompt }],
        max_tokens: 400
      });
      const apiUrl = ensureChatCompletionsUrl(config.apiUrl);
      const u = new URL(apiUrl);
      const client = u.protocol === 'https:' ? require('https') : require('http');
      const apiReq = client.request(apiUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + config.apiKey,
          'Content-Length': Buffer.byteLength(reqBody, 'utf8')
        }
      }, (apiRes) => {
        let data = '';
        apiRes.on('data', (c) => { data += c; });
        apiRes.on('end', () => {
          const send = (status, obj) => {
            if (!res.writableEnded) {
              res.writeHead(status, { 'Content-Type': 'application/json' });
              res.end(JSON.stringify(obj));
            }
          };
          try {
            let out;
            try {
              out = data ? JSON.parse(data) : {};
            } catch (_) {
              send(200, { error: 'API 返回非 JSON: ' + (data ? data.slice(0, 200) : '空响应') });
              return;
            }
            if (apiRes.statusCode >= 400) {
              const msg = out.message || (out.error && out.error.message) || out.msg || out.error || String(out.code || apiRes.statusCode);
              send(200, { error: 'API HTTP ' + apiRes.statusCode + ': ' + msg });
              return;
            }
            if (out.code != null && String(out.code) !== '0' && String(out.code) !== '') {
              const msg = out.message || (out.error && out.error.message) || out.msg || out.error || String(out.code);
              send(200, { error: 'API 错误: ' + msg });
              return;
            }
            if (out.error && (out.error.code || out.error.message)) {
              send(200, { error: 'API 错误: ' + (out.error.message || out.error.code) });
              return;
            }
            let text = '';
            if (out.output && out.output.choices && out.output.choices[0]) {
              const m = out.output.choices[0].message || out.output.choices[0];
              if (Array.isArray(m.content)) {
                text = m.content.map((x) => (typeof x === 'string' ? x : x.text || '')).join('').trim();
              } else {
                text = (m.content || m.text || '').trim();
              }
            }
            if (!text && out.output) {
              const o = out.output;
              if (typeof o === 'string') text = o.trim();
              else if (o.text) text = String(o.text).trim();
              else if (o.choices && o.choices[0]) {
                const m = o.choices[0].message || o.choices[0];
                text = (m.content || m.text || '').trim();
              }
            }
            if (!text && out.choices && out.choices[0]) {
              const msg = out.choices[0].message || out.choices[0];
              if (Array.isArray(msg.content)) {
                text = msg.content.map((x) => (typeof x === 'string' ? x : x.text || '')).join('').trim();
              } else {
                text = (msg.content || msg.text || '').trim();
              }
            }
            if (!text) text = (out.content || out.text || '').trim();
            if (!text && out.result) {
              const r = out.result;
              text = (r.output && (typeof r.output === 'string' ? r.output : r.output.text || r.output.content)) || r.text || '';
              text = String(text).trim();
            }
            send(200, { answer: text || '（模型未返回文本，请检查 API 与模型）' });
          } catch (e) {
            send(200, { error: 'API 返回解析失败: ' + (e.message || e) + (data ? ' ' + data.slice(0, 150) : '') });
          }
        });
      });
      apiReq.on('error', (e) => {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: '请求 API 失败: ' + e.message }));
      });
      apiReq.write(reqBody);
      apiReq.end();
    });
    return;
  }

  if (pathname === '/api/projects' && req.method === 'GET') {
    try {
      const data = buildTimelineData();
      res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
      res.end(JSON.stringify({ schemaVersion: LOG_SCHEMA_VERSION, projects: data.projectsIndex || [] }));
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: String(err.message) }));
    }
    return;
  }

  const projectSessionsMatch = pathname.match(/^\/api\/projects\/([^/]+)\/sessions$/);
  if (projectSessionsMatch && req.method === 'GET') {
    const projectId = decodeURIComponent(projectSessionsMatch[1]);
    try {
      const data = buildTimelineData();
      const sessions = data.sessionsByProject && data.sessionsByProject[projectId] ? data.sessionsByProject[projectId] : [];
      res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
      res.end(JSON.stringify({ schemaVersion: LOG_SCHEMA_VERSION, projectId, sessions }));
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: String(err.message) }));
    }
    return;
  }

  const timelineEventsMatch = pathname.match(/^\/api\/timelines\/([^/]+)\/events$/);
  if (timelineEventsMatch && req.method === 'GET') {
    const sessionId = decodeURIComponent(timelineEventsMatch[1]);
    const query = Object.fromEntries(url.searchParams || []);
    try {
      const data = buildTimelineData();
      const session = data.sessions && data.sessions[sessionId];
      if (!session) {
        res.writeHead(404, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Session not found' }));
        return;
      }
      let events = session.events || [];
      const eventType = (query.eventType || '').trim();
      const toolName = (query.toolName || '').trim();
      const keyword = (query.q || '').trim().toLowerCase();
      if (eventType) events = events.filter(e => String(e.eventType || '') === eventType);
      if (toolName) events = events.filter(e => String(e.toolName || '') === toolName);
      if (keyword) {
        const dump = (o) => (typeof o === 'string' ? o : JSON.stringify(o || {})).toLowerCase();
        events = events.filter(e =>
          dump(e.toolInput).includes(keyword) ||
          dump(e.toolOutput).includes(keyword) ||
          String(e.content || '').toLowerCase().includes(keyword) ||
          String(e.toolName || '').toLowerCase().includes(keyword)
        );
      }
      const offset = Math.max(0, parseInt(query.offset, 10) || 0);
      const limit = Math.min(2000, Math.max(1, parseInt(query.limit, 10) || 300));
      const paged = events.slice(offset, offset + limit);
      res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
      res.end(JSON.stringify({
        schemaVersion: LOG_SCHEMA_VERSION,
        sessionId,
        offset,
        limit,
        total: events.length,
        tools: session.tools || [],
        health: session.health || {},
        projectId: session.projectId,
        events: paged,
      }));
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: String(err.message) }));
    }
    return;
  }

  const timelineHealthMatch = pathname.match(/^\/api\/timelines\/([^/]+)\/health$/);
  if (timelineHealthMatch && req.method === 'GET') {
    const sessionId = decodeURIComponent(timelineHealthMatch[1]);
    try {
      const data = buildTimelineData();
      const session = data.sessions && data.sessions[sessionId];
      if (!session) {
        res.writeHead(404, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: 'Session not found' }));
        return;
      }
      res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
      res.end(JSON.stringify({
        schemaVersion: LOG_SCHEMA_VERSION,
        sessionId,
        health: session.health || {},
      }));
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: String(err.message) }));
    }
    return;
  }

  const sessionLogMatch = pathname.match(/^\/api\/sessions\/([^/]+)\/log$/);
  if (sessionLogMatch) {
    const rawId = sessionLogMatch[1];
    const id = sanitizeId(rawId);
    if (id !== rawId) {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Invalid session id' }));
      return;
    }
    const filePath = path.join(TOOL_LOGS_DIR, id + '.txt');
    if (!path.resolve(filePath).startsWith(path.resolve(TOOL_LOGS_DIR)) || !fs.existsSync(filePath)) {
      res.writeHead(404, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: 'Not found' }));
      return;
    }
    try {
      const content = fs.readFileSync(filePath, 'utf8');
      res.writeHead(200, { 'Content-Type': 'text/plain; charset=utf-8' });
      res.end(content);
    } catch (err) {
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ error: String(err.message) }));
    }
    return;
  }

  let filePath = path.join(VIEWER_DIR, pathname === '/' ? 'index.html' : pathname);
  if (!path.resolve(filePath).startsWith(path.resolve(VIEWER_DIR))) {
    res.writeHead(404);
    res.end();
    return;
  }
  if (fs.existsSync(filePath) && fs.statSync(filePath).isFile()) {
    const ext = path.extname(filePath);
    res.writeHead(200, { 'Content-Type': mime[ext] || 'application/octet-stream' });
    res.end(fs.readFileSync(filePath));
    return;
  }
  res.writeHead(404);
  res.end();
});

const MAX_PORT_TRIES = 20;
let _listenPort = PORT;

function tryListen() {
  server.once('error', (err) => {
    if ((err.code === 'EADDRINUSE' || err.code === 'EACCES') && _listenPort - PORT < MAX_PORT_TRIES) {
      _listenPort += 1;
      tryListen();
    } else {
      console.error('无法绑定端口，请设置环境变量 CLAUDE_LOG_VIEWER_PORT 为可用端口后重试。');
      process.exit(1);
    }
  });
  server.listen(_listenPort, '127.0.0.1', () => {
    const bound = server.address().port;
    if (bound !== PORT) console.log(`提示: 端口 ${PORT} 不可用，已自动切换到 ${bound}`);
    console.log(`Claude 工具日志查看器: http://127.0.0.1:${bound}`);
    console.log(`项目/会话 数据源: ${CLAUDE_PROJECTS_DIR}`);
    console.log(`tool-logs 目录: ${TOOL_LOGS_DIR}`);
    console.log('API: /api/projects, /api/explain, /api/question 已就绪');
  });
}
tryListen();
