#!/usr/bin/env node
/**
 * Claude Code 详细工具日志 Hook（用户级）
 * 任意目录运行 claude 时，将每次工具调用的完整 JSON 追加到 C:\Users\1\.claude\tool-logs\detailed-tool-log.txt
 */

const fs = require('fs');
const path = require('path');

const LOG_DIR = process.env.CLAUDE_TOOL_LOG_DIR || path.join(process.env.USERPROFILE || process.env.HOME || '.', '.claude', 'tool-logs');

function main() {
  let input = '';
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', (chunk) => { input += chunk; });
  process.stdin.on('end', () => {
    try {
      const raw = input.replace(/^\uFEFF/, '');
      const data = JSON.parse(raw);
      const sessionId = data.session_id || data.sessionId || data.conversation_id
        || data.generation_id
        || (data.cwd ? 'cwd_' + String(data.cwd).replace(/[^a-zA-Z0-9-_]/g, '_').slice(-50) : 'unknown');
      const event = data.hook_event_name || data.hookEventName || 'Unknown';
      const toolName = data.tool_name || data.toolName || '-';
      const cwd = data.cwd || '-';
      const ts = new Date().toISOString();

      if (!fs.existsSync(LOG_DIR)) {
        fs.mkdirSync(LOG_DIR, { recursive: true });
      }

      const safeSessionId = sessionId.replace(/[^a-zA-Z0-9-_]/g, '_');
      const logFile = path.join(LOG_DIR, safeSessionId + '.txt');

      const block = [
        '',
        '═'.repeat(80),
        `[${ts}] ${event} | tool: ${toolName} | cwd: ${cwd}`,
        '─'.repeat(80),
        'FULL INPUT (JSON):',
        JSON.stringify(data, null, 2),
        ''
      ].join('\n');

      fs.appendFileSync(logFile, block, 'utf8');
    } catch (e) {
      const logDir = process.env.CLAUDE_TOOL_LOG_DIR || path.join(process.env.USERPROFILE || process.env.HOME || '.', '.claude', 'tool-logs');
      const logFile = path.join(logDir, 'unknown.txt');
      if (!fs.existsSync(logDir)) fs.mkdirSync(logDir, { recursive: true });
      fs.appendFileSync(logFile, `\n[${new Date().toISOString()}] Parse error: ${e.message}\nRaw: ${input.replace(/^\uFEFF/, '').slice(0, 500)}\n`, 'utf8');
    }
    process.exit(0);
  });
}

main();
