const MAX_MESSAGES = 20;
const MAX_MESSAGE_BYTES = 1024;
const MAX_HISTORY_BYTES = 8192;
const MAX_BODY_BYTES = 16384;
const MAX_NEW_TOKENS = 64;
const TIMEOUT_MS = 60000;

class BodyTooLarge extends Error {}

async function readLimitedBody(request) {
  if (!request.body) return '';
  const reader = request.body.getReader();
  const chunks = [];
  let bytes = 0;
  try {
    while (true) {
      const {done, value} = await reader.read();
      if (done) break;
      bytes += value.byteLength;
      if (bytes > MAX_BODY_BYTES) {
        void reader.cancel().catch(() => {});
        throw new BodyTooLarge();
      }
      chunks.push(Buffer.from(value));
    }
    return new TextDecoder('utf-8', {fatal: true}).decode(Buffer.concat(chunks, bytes));
  } finally {
    reader.releaseLock();
  }
}

function validMetrics(m, payload) {
  const counts = ['input_tokens', 'selected_context_tokens', 'output_tokens', 'total_tokens'];
  if (!m || counts.some(key => !Number.isSafeInteger(m[key]) || m[key] < 0)) return false;
  if (!Number.isFinite(m.response_ms) || m.response_ms < 0 || m.output_tokens > payload.max_new_tokens) return false;
  if (m.total_tokens !== m.selected_context_tokens + m.output_tokens) return false;
  if (m.backend !== 'Toruk' || typeof m.model !== 'string' || !m.model.trim() || typeof m.backbone !== 'string' || !m.backbone.trim()) return false;
  if (m.mode !== payload.mode || typeof m.memory_used !== 'boolean' || (m.mode === 'BASELINE' && m.memory_used)) return false;
  const ids = m.selected_message_ids;
  return Array.isArray(ids) && ids.length > 0 && new Set(ids).size === ids.length
    && ids.every(id => typeof id === 'string' && /^m(?:[0-9]|1[0-9])$/.test(id) && Number(id.slice(1)) < payload.messages.length);
}

// Only these fixed messages may describe a model-load failure in the browser.
const READINESS_ERRORS = {
  CHECKPOINT_MISSING: 'The selected demo model is missing. Start Toruk with the installed chat backbone; see the local chat guide.',
  CHECKPOINT_INCOMPATIBLE: 'The selected model is incompatible. Start Toruk with the supported chat backbone.',
  CHECKPOINT_INVALID: 'The selected demo model cannot be read. Use the chat backbone described in the local chat guide.',
  BACKBONE_MISSING: 'Chat model files are missing. Complete the local model setup, then restart Toruk.',
  BACKBONE_INVALID: 'Chat model files failed verification. Restore the pinned model using the local chat guide, then restart Toruk.',
  CHAT_DEPENDENCIES_MISSING: 'Chat support is not installed. Complete the chat dependency setup in the local chat guide, then restart Toruk.',
  BACKBONE_INCOMPATIBLE: 'The installed chat model cannot load. Check the local chat setup and restart Toruk.',
  SELECTOR_UNAVAILABLE: 'The optional Toruk memory model cannot load. Start basic chat without the optional memory model, or restore the evaluated memory model.',
  STARTUP_TIMEOUT: 'Chat model startup timed out. Close unused applications and restart Toruk; check that the laptop has enough available memory.',
  MODEL_LOAD_FAILED: 'The chat model could not start. Check the backend terminal and the local chat guide, then restart Toruk.',
  WORKER_STOPPED: 'The chat model stopped. Restart the backend, then retry the connection.',
};

function readinessError(code) {
  const known = typeof code === 'string' && Object.hasOwn(READINESS_ERRORS, code);
  return {error_code: known ? code : 'MODEL_LOAD_FAILED', error: READINESS_ERRORS[known ? code : 'MODEL_LOAD_FAILED']};
}

function json(value, status = 200) {
  return Response.json(value, {status, headers: {'Cache-Control': 'no-store'}});
}

function backendConfig(env) {
  if (!env.TORUK_BACKEND_URL || !env.TORUK_BACKEND_TOKEN) return null;
  try {
    const url = new URL(env.TORUK_BACKEND_URL);
    const local = ['localhost', '127.0.0.1'].includes(url.hostname);
    if (['production', 'preview'].includes(env.VERCEL_ENV) && url.protocol !== 'https:') return null;
    if ((url.protocol !== 'https:' && !(local && url.protocol === 'http:')) || url.username || url.password || url.search || url.hash || url.pathname !== '/') return null;
    return {origin: url.origin, token: env.TORUK_BACKEND_TOKEN};
  } catch { return null; }
}

function validate(body) {
  if (!body || typeof body !== 'object' || Array.isArray(body)) throw new Error('Expected a JSON object.');
  const {messages, max_new_tokens: budget = 32, mode = 'BASELINE', temperature = 0, top_p: topP = 1} = body;
  if (!Array.isArray(messages) || messages.length < 1 || messages.length > MAX_MESSAGES) throw new Error(`Provide 1–${MAX_MESSAGES} messages.`);
  if (!Number.isInteger(budget) || budget < 1 || budget > MAX_NEW_TOKENS) throw new Error(`Generation length must be 1–${MAX_NEW_TOKENS} tokens.`);
  if (!['BASELINE', 'TORUK'].includes(mode)) throw new Error('Mode must be BASELINE or TORUK.');
  if (typeof temperature !== 'number' || !Number.isFinite(temperature) || temperature < 0 || temperature > 2) throw new Error('Temperature must be 0–2.');
  if (typeof topP !== 'number' || !Number.isFinite(topP) || topP <= 0 || topP > 1) throw new Error('Top-p must be above 0 and at most 1.');
  let total = 0;
  const clean = messages.map(item => {
    if (!item || typeof item !== 'object' || !['user', 'assistant'].includes(item.role) || typeof item.content !== 'string' || !item.content.trim()) throw new Error('Messages need a user/assistant role and nonempty text.');
    const size = Buffer.byteLength(item.content, 'utf8');
    if (size > MAX_MESSAGE_BYTES) throw new Error(`Each message is limited to ${MAX_MESSAGE_BYTES} UTF-8 bytes.`);
    total += size;
    return {role: item.role, content: item.content};
  });
  if (total > MAX_HISTORY_BYTES) throw new Error('Conversation is too long; start a new chat.');
  if (clean.at(-1).role !== 'user') throw new Error('The final message must be from the user.');
  return {messages: clean, max_new_tokens: budget, mode, temperature, top_p: topP};
}

async function backendFetch(config, path, options, fetchImpl) {
  return fetchImpl(`${config.origin}${path}`, {
    ...options,
    headers: {
      Authorization: `Bearer ${config.token}`,
      ...(options.headers || {}),
    },
    signal: AbortSignal.timeout(TIMEOUT_MS),
  });
}

export async function statusResponse({env = process.env, fetchImpl = fetch} = {}) {
  const config = backendConfig(env);
  if (!config) return json({ready: false, backend: 'Toruk', model: 'Unconfigured', error: 'Toruk inference host is not configured.'});
  try {
    const response = await backendFetch(config, '/api/status', {}, fetchImpl);
    if (!response.ok) throw new Error('backend status error');
    const data = await response.json();
    if (data.backend !== 'Toruk' || typeof data.ready !== 'boolean') throw new Error('invalid backend status');
    return json({ready: data.ready, backend: 'Toruk', experimental: true, chat_quality: 'unqualified', efficiency_claim: 'unsupported', selector_id: data.selector_id ?? null, selector_kind: data.selector_kind ?? null, backbone_digest: data.backbone_digest ?? null, backbone_revision: data.backbone_revision ?? null, backbone_sha256: data.backbone_sha256 ?? null, selector_sha256: data.selector_sha256 ?? null, model: data.model || 'Unavailable', backbone: data.backbone || data.model || 'Unavailable', context_tokens: data.context_tokens ?? null, memory_supported: data.memory_supported === true, modes: Array.isArray(data.modes) ? data.modes : ['BASELINE'], ...(data.ready ? {error: null, error_code: null} : readinessError(data.error_code))});
  } catch {
    return json({ready: false, backend: 'Toruk', model: 'Unavailable', error_code: 'BACKEND_UNAVAILABLE', error: 'Toruk inference is unavailable. Start or restart the backend, then retry the connection.'});
  }
}

export async function chatResponse(request, {env = process.env, fetchImpl = fetch, logger = console} = {}) {
  if (request.method !== 'POST') return json({error: 'POST required.'}, 405);
  const length = Number(request.headers.get('content-length') || 0);
  if (length > MAX_BODY_BYTES) return json({error: 'Request body is too large.'}, 413);
  let raw;
  try {
    raw = await readLimitedBody(request);
  } catch (error) {
    return json({error: error instanceof BodyTooLarge ? 'Request body is too large.' : 'Could not read a valid UTF-8 request body.'}, error instanceof BodyTooLarge ? 413 : 400);
  }
  let payload;
  try {
    payload = validate(JSON.parse(raw));
  } catch (error) {
    return json({error: error instanceof SyntaxError ? 'Invalid JSON.' : error.message}, 400);
  }
  const config = backendConfig(env);
  if (!config) return json({error: 'Toruk inference is not configured. No answer was generated.'}, 503);
  const started = performance.now();
  try {
    const response = await backendFetch(config, '/api/infer', {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload),
    }, fetchImpl);
    if (response.status === 400) {
      return json({error: 'The inference backend rejected this request. Check the context mode and generation settings, or shorten the message and start a new chat.'}, 400);
    }
    if (response.status === 504) return json({error: 'Generation timed out. Restart the backend, then retry the connection.'}, 504);
    if (response.status === 503) {
      const unavailable = await response.json();
      if (unavailable.error_code === 'INFERENCE_BUSY') return json({error_code: 'INFERENCE_BUSY', error: 'Inference is busy. Wait for the current reply, then retry.'}, 503);
      if (unavailable.error_code) return json(readinessError(unavailable.error_code), 503);
    }
    if (!response.ok) throw new Error('backend response failed');
    const data = await response.json();
    const m = data.metrics;
    if (typeof data.answer !== 'string' || !data.answer.trim() || !validMetrics(m, payload)) throw new Error('invalid backend response');
    const metrics = {...m, proxy_ms: Math.round((performance.now() - started) * 1000) / 1000};
    logger.info(JSON.stringify({event: 'toruk_chat', mode: payload.mode, input_tokens: m.input_tokens, selected_context_tokens: m.selected_context_tokens, output_tokens: m.output_tokens, response_ms: m.response_ms, proxy_ms: metrics.proxy_ms}));
    return json({answer: data.answer, metrics});
  } catch (error) {
    const timeout = error?.name === 'TimeoutError' || error?.name === 'AbortError';
    logger.error(JSON.stringify({event: 'toruk_chat_error', backend: 'Toruk', reason: timeout ? 'timeout' : 'unavailable'}));
    return json({error: timeout ? 'Toruk inference timed out. Try again later.' : 'Toruk inference is unavailable. No answer was generated.'}, timeout ? 504 : 503);
  }
}
