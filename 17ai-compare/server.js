const http = require("http");
const fs = require("fs");
const path = require("path");
const { URL } = require("url");

const port = Number(process.env.PORT || 3000);
const rootDir = __dirname;
const publicDir = path.join(rootDir, "public");
const apiPath = path.resolve(rootDir, "..", "API.md");

const envKeyMap = {
  "阿里云千问 (Qwen)": "QWEN_API_KEY",
  "豆包 (Doubao)": "DOUBAO_API_KEY",
  DeepSeek: "DEEPSEEK_API_KEY",
  "Kimi (Moonshot AI)": "KIMI_API_KEY",
  OpenAI: "OPENAI_API_KEY"
};

function extractBacktickValues(line) {
  const matches = line.matchAll(/`([^`]+)`/g);
  return Array.from(matches, m => m[1].trim());
}

function normalizeName(name) {
  return name.trim();
}

function loadProviders() {
  const content = fs.existsSync(apiPath) ? fs.readFileSync(apiPath, "utf8") : "";
  const lines = content.split(/\r?\n/);
  const providers = [];
  let current = null;

  for (const line of lines) {
    if (line.startsWith("## ")) {
      if (current) providers.push(current);
      current = { name: normalizeName(line.replace(/^##\s+/, "")), apiKey: "", models: [], baseUrl: "" };
      continue;
    }
    if (!current) continue;
    if (line.includes("API Key:")) {
      const values = extractBacktickValues(line);
      if (values.length > 0) current.apiKey = values[0];
      continue;
    }
    if (line.includes("模型:")) {
      current.models = extractBacktickValues(line);
      continue;
    }
    if (line.includes("Base URL:")) {
      const values = extractBacktickValues(line);
      if (values.length > 0) current.baseUrl = values[0];
      continue;
    }
  }
  if (current) providers.push(current);

  for (const provider of providers) {
    const envKey = envKeyMap[provider.name];
    if (envKey && process.env[envKey]) provider.apiKey = process.env[envKey];
  }

  return providers;
}

function jsonResponse(res, status, payload) {
  const body = JSON.stringify(payload);
  res.writeHead(status, {
    "Content-Type": "application/json; charset=utf-8",
    "Content-Length": Buffer.byteLength(body)
  });
  res.end(body);
}

function notFound(res) {
  res.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
  res.end("Not Found");
}

function safeParseBody(req) {
  return new Promise((resolve, reject) => {
    let data = "";
    req.on("data", chunk => {
      data += chunk;
      if (data.length > 5 * 1024 * 1024) {
        reject(new Error("Payload too large"));
      }
    });
    req.on("end", () => {
      try {
        resolve(data ? JSON.parse(data) : {});
      } catch (err) {
        reject(err);
      }
    });
    req.on("error", reject);
  });
}

function buildChatUrl(baseUrl) {
  const trimmed = String(baseUrl || "").trim().replace(/\/+$/, "");
  if (!trimmed) return "";
  if (trimmed.endsWith("/chat/completions")) return trimmed;
  return `${trimmed}/chat/completions`;
}

async function callProvider({ name, apiKey, model, baseUrl, question, systemPrompt, temperature }) {
  if (!apiKey) {
    return { name, model, error: "缺少 API Key", latencyMs: 0 };
  }
  if (!model) {
    return { name, model, error: "缺少模型名称", latencyMs: 0 };
  }
  const url = buildChatUrl(baseUrl);
  if (!url) {
    return { name, model, error: "缺少 Base URL", latencyMs: 0 };
  }

  const messages = [];
  if (systemPrompt) messages.push({ role: "system", content: systemPrompt });
  messages.push({ role: "user", content: question });

  const payload = {
    model,
    messages,
    stream: false
  };
  if (Number.isFinite(temperature)) payload.temperature = temperature;

  const started = Date.now();
  const response = await fetch(url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });
  const latencyMs = Date.now() - started;

  if (!response.ok) {
    const text = await response.text();
    return { name, model, error: `请求失败 ${response.status}: ${text}`, latencyMs };
  }
  const data = await response.json();
  const content = data?.choices?.[0]?.message?.content ?? data?.choices?.[0]?.text ?? "";
  if (!content) {
    return { name, model, error: "未获取到有效内容", latencyMs };
  }
  return { name, model, content, latencyMs };
}

function serveStatic(req, res) {
  const url = new URL(req.url, `http://${req.headers.host}`);
  let filePath = url.pathname === "/" ? "/index.html" : url.pathname;
  filePath = path.join(publicDir, filePath);

  if (!filePath.startsWith(publicDir)) {
    return notFound(res);
  }

  fs.readFile(filePath, (err, data) => {
    if (err) {
      return notFound(res);
    }
    const ext = path.extname(filePath).toLowerCase();
    const typeMap = {
      ".html": "text/html; charset=utf-8",
      ".js": "text/javascript; charset=utf-8",
      ".css": "text/css; charset=utf-8"
    };
    res.writeHead(200, { "Content-Type": typeMap[ext] || "application/octet-stream" });
    res.end(data);
  });
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`);

  if (req.method === "GET" && url.pathname === "/api/providers") {
    const providers = loadProviders().map(p => ({
      name: p.name,
      models: p.models || [],
      baseUrl: p.baseUrl || "",
      keyPresent: Boolean(p.apiKey)
    }));
    return jsonResponse(res, 200, { providers });
  }

  if (req.method === "POST" && url.pathname === "/api/compare") {
    try {
      const body = await safeParseBody(req);
      const question = String(body.question || "").trim();
      const systemPrompt = String(body.systemPrompt || "").trim();
      const temperature = Number.isFinite(Number(body.temperature)) ? Number(body.temperature) : undefined;
      const selectedRequests = Array.isArray(body.requests) ? body.requests : [];

      if (!question) {
        return jsonResponse(res, 400, { error: "问题不能为空" });
      }
      if (!selectedRequests.length) {
        return jsonResponse(res, 400, { error: "至少选择一个模型" });
      }

      const providerMap = new Map(loadProviders().map(p => [p.name, p]));
      const tasks = selectedRequests.map(item => {
        const name = String(item.name || "").trim();
        const model = String(item.model || "").trim();
        const baseUrl = String(item.baseUrl || "").trim();
        const entry = providerMap.get(name) || { name, apiKey: "" };
        return callProvider({
          name,
          apiKey: entry.apiKey,
          model,
          baseUrl: baseUrl || entry.baseUrl,
          question,
          systemPrompt,
          temperature
        });
      });

      const results = await Promise.all(tasks);
      return jsonResponse(res, 200, { results });
    } catch (err) {
      return jsonResponse(res, 500, { error: err.message || "服务异常" });
    }
  }

  return serveStatic(req, res);
});

function start() {
  server.listen(port, () => {
    process.stdout.write(`AI Compare running at http://localhost:${port}\n`);
  });
}

if (require.main === module) {
  start();
}

module.exports = { loadProviders };
