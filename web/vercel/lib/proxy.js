const MAX_MESSAGES = 20;
const MAX_MESSAGE_BYTES = 1024;
const MAX_HISTORY_BYTES = 8192;
const MAX_BODY_BYTES = 16384;
const MAX_NEW_TOKENS = 64;
const TIMEOUT_MS = 60000;

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
    return json({ready: data.ready, backend: 'Toruk', experimental: true, chat_quality: 'unqualified', efficiency_claim: 'unsupported', selector_sha256: data.selector_sha256 ?? null, model: data.model || 'Unavailable', backbone: data.backbone || data.model || 'Unavailable', context_tokens: data.context_tokens ?? null, memory_supported: data.memory_supported === true, modes: Array.isArray(data.modes) ? data.modes : ['BASELINE'], error: data.error || null});
  } catch {
    return json({ready: false, backend: 'Toruk', model: 'Unavailable', error: 'Toruk inference host is unavailable.'});
  }
}

export async function chatResponse(request, {env = process.env, fetchImpl = fetch, logger = console} = {}) {
  if (request.method !== 'POST') return json({error: 'POST required.'}, 405);
  const length = Number(request.headers.get('content-length') || 0);
  if (length > MAX_BODY_BYTES) return json({error: 'Request body is too large.'}, 413);
  let payload;
  try {
    const raw = await request.text();
    if (Buffer.byteLength(raw, 'utf8') > MAX_BODY_BYTES) return json({error: 'Request body is too large.'}, 413);
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
      const bad = await response.json();
      return json({error: bad.error || 'Invalid generation request.'}, 400);
    }
    if (!response.ok) throw new Error('backend response failed');
    const data = await response.json();
    const m = data.metrics;
    if (typeof data.answer !== 'string' || !m || m.backend !== 'Toruk' || !Number.isInteger(m.input_tokens) || !Number.isInteger(m.selected_context_tokens) || !Number.isInteger(m.output_tokens) || !Number.isInteger(m.total_tokens) || typeof m.response_ms !== 'number' || typeof m.model !== 'string' || typeof m.backbone !== 'string' || m.mode !== payload.mode || typeof m.memory_used !== 'boolean' || !Array.isArray(m.selected_message_ids) || m.selected_message_ids.some(id => !/^m(?:[0-9]|1[0-9])$/.test(id))) throw new Error('invalid backend response');
    const metrics = {...m, proxy_ms: Math.round((performance.now() - started) * 1000) / 1000};
    logger.info(JSON.stringify({event: 'toruk_chat', mode: payload.mode, input_tokens: m.input_tokens, selected_context_tokens: m.selected_context_tokens, output_tokens: m.output_tokens, response_ms: m.response_ms, proxy_ms: metrics.proxy_ms}));
    return json({answer: data.answer, metrics});
  } catch (error) {
    const timeout = error?.name === 'TimeoutError' || error?.name === 'AbortError';
    logger.error(JSON.stringify({event: 'toruk_chat_error', backend: 'Toruk', reason: timeout ? 'timeout' : 'unavailable'}));
    return json({error: timeout ? 'Toruk inference timed out. Try again later.' : 'Toruk inference is unavailable. No answer was generated.'}, timeout ? 504 : 503);
  }
}
