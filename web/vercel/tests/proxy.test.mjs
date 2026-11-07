import assert from 'node:assert/strict';
import test from 'node:test';
import {readFile} from 'node:fs/promises';
import {chatResponse, statusResponse} from '../lib/proxy.js';
import {clearedMessages, completedMessages, pendingMessages} from '../public/chat_state.js';

const env = {TORUK_BACKEND_URL: 'http://127.0.0.1:8766', TORUK_BACKEND_TOKEN: 'private-token'};
const request = (messages, budget = 16) => new Request('http://localhost/api/chat', {
  method: 'POST', headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({messages, max_new_tokens: budget}),
});
const user = [{role: 'user', content: 'hello'}];
const metrics = {input_tokens: 20, selected_context_tokens: 16, output_tokens: 3, total_tokens: 19, response_ms: 4.5, backend: 'Toruk', model: 'toruk-ordinary-v1:test', backbone: 'Toruk ordinary byte LM', mode: 'BASELINE', memory_used: false, selected_message_ids: ['m0']};

test('HTTP backend deadlines and busy responses retain actionable safe semantics', async () => {
  const logger = {info(){}, error(){}};
  const deadline = await chatResponse(request(user), {
    env, logger, fetchImpl: async () => Response.json({error: 'private-deadline-detail'}, {status: 504}),
  });
  assert.equal(deadline.status, 504);
  assert.match((await deadline.json()).error, /restart.*backend/i);
  const busy = await chatResponse(request(user), {
    env, logger, fetchImpl: async () => Response.json({error_code: 'INFERENCE_BUSY', error: 'private-busy-detail'}, {status: 503}),
  });
  assert.equal(busy.status, 503);
  const body = await busy.json();
  assert.match(body.error, /busy.*retry/i);
  assert.doesNotMatch(body.error, /private-/);
});

test('long conversations fail visibly instead of silently dropping the earliest turns', async () => {
  let history = [];
  for (let i = 0; i < 10; i++) history = completedMessages(pendingMessages(history, `question ${i}`), `answer ${i}`);
  const pending = pendingMessages(history, 'new question');
  assert.equal(pending.length, 21);
  assert.equal(pending[0].content, 'question 0');
  assert.equal(history.length, 20);
  const response = await chatResponse(request(pending), {
    env, fetchImpl: async () => { throw new Error('oversized history reached backend'); },
  });
  assert.equal(response.status, 400);
  assert.match((await response.json()).error, /20 messages/);
});

test('empty backend replies cannot poison the next browser history', async () => {
  for (const answer of ['', ' \n\t ']) {
    const response = await chatResponse(request(user), {
      env, fetchImpl: async () => Response.json({answer, metrics}), logger: {info(){},error(){}},
    });
    assert.equal(response.status, 503);
    assert.equal((await response.json()).answer, undefined);
  }
});

test('backend request errors do not expose private exception details', async () => {
  const response = await chatResponse(request(user), {
    env, fetchImpl: async () => Response.json({error: 'private-token C:/private/path'}, {status: 400}),
  });
  assert.equal(response.status, 400);
  assert.doesNotMatch(JSON.stringify(await response.json()), /private-token|private\/path/);
});

test('chunked request bodies are cancelled when they cross the byte limit', async () => {
  let pulls = 0;
  let cancelled = false;
  const stream = new ReadableStream({
    pull(controller) {
      pulls++;
      controller.enqueue(new Uint8Array(8192));
      if (pulls === 5) controller.close();
    },
    cancel() { cancelled = true; },
  });
  const response = await chatResponse(new Request('http://localhost/api/chat', {
    method: 'POST', body: stream, duplex: 'half',
  }), {env});
  assert.equal(response.status, 413);
  assert.equal(cancelled, true);
  assert.ok(pulls < 5);
});

test('impossible token counts, timings and source IDs are rejected', async () => {
  for (const invalid of [
    {input_tokens: -1}, {selected_context_tokens: -1}, {output_tokens: -1},
    {output_tokens: 17, total_tokens: 33}, {total_tokens: 999}, {response_ms: -1},
    {selected_message_ids: ['m1']}, {selected_message_ids: ['m0', 'm0']},
    {memory_used: true},
  ]) {
    const response = await chatResponse(request(user), {
      env, fetchImpl: async () => Response.json({answer: 'abc', metrics: {...metrics, ...invalid}}),
      logger: {info(){},error(){}},
    });
    assert.equal(response.status, 503, JSON.stringify(invalid));
  }
});

test('unready model has an actionable reason and never forwards backend exception text', async () => {
  for (const code of ['CHECKPOINT_MISSING', 'BACKBONE_MISSING', 'CHAT_DEPENDENCIES_MISSING', 'WORKER_STOPPED', 'unknown-private-code']) {
    const backend = {ready: false, backend: 'Toruk', error_code: code, error: 'private-token C:/private/path raw-exception'};
    const response = await statusResponse({env, fetchImpl: async () => Response.json(backend)});
    const body = await response.json();
    assert.equal(body.ready, false);
    assert.match(body.error, /Start|setup|Restart|restart|guide/);
    assert.doesNotMatch(JSON.stringify(body), /private-token|private\/path|raw-exception|unknown-private-code/);
    const post = await chatResponse(request(user), {env, fetchImpl: async () => Response.json(backend, {status: 503})});
    assert.equal(post.status, 503);
    assert.equal((await post.json()).error_code, body.error_code);
  }
});

test('unconfigured and unavailable inference return errors, never answers', async () => {
  const status = await statusResponse({env: {}});
  assert.equal((await status.json()).ready, false);
  const missing = await chatResponse(request(user), {env: {}, logger: {info(){},error(){}}});
  assert.equal(missing.status, 503);
  assert.match((await missing.json()).error, /not configured/);
  const outage = await chatResponse(request(user), {env, fetchImpl: async () => {throw new Error('offline');}, logger: {info(){},error(){}}});
  assert.equal(outage.status, 503);
  assert.ok((await outage.json()).error);
});

test('normal Toruk proxy validates metrics and keeps token off the browser response', async () => {
  const logs = [];
  const response = await chatResponse(request(user), {
    env,
    fetchImpl: async (url, options) => {
      assert.equal(url, 'http://127.0.0.1:8766/api/infer');
      assert.equal(options.headers.Authorization, 'Bearer private-token');
      assert.equal(JSON.parse(options.body).messages[0].content, 'hello');
      return Response.json({answer: 'abc', metrics});
    },
    logger: {info: value => logs.push(JSON.parse(value)), error(){}},
  });
  assert.equal(response.status, 200);
  const result = await response.json();
  assert.equal(result.answer, 'abc');
  assert.equal(result.metrics.selected_context_tokens, 16);
  assert.equal(result.metrics.memory_used, false);
  assert.equal(result.metrics.mode, 'BASELINE');
  assert.equal(logs[0].input_tokens, 20);
  assert.equal(JSON.stringify(result).includes('private-token'), false);
});

test('empty and long messages, invalid budget, and malformed backend are rejected', async () => {
  for (const messages of [[], [{role: 'user', content: ' '}], [{role: 'user', content: 'é'.repeat(600)}]]) {
    const response = await chatResponse(request(messages), {env, logger: {info(){},error(){}}});
    assert.equal(response.status, 400);
  }
  assert.equal((await chatResponse(request(user, 65), {env})).status, 400);
  assert.equal((await chatResponse(new Request('http://localhost/api/chat', {method: 'POST', body: JSON.stringify({messages: user, mode: 'INVALID'})}), {env})).status, 400);
  const malformed = await chatResponse(request(user), {
    env, fetchImpl: async () => Response.json({answer: 'fake'}), logger: {info(){},error(){}},
  });
  assert.equal(malformed.status, 503);
});

test('status and client history clear remain independent of backend sessions', async () => {
  const status = await statusResponse({env, fetchImpl: async () => Response.json({ready: true, backend: 'Toruk', model: 'toruk-ordinary-v1:test', context_tokens: 32})});
  assert.equal((await status.json()).model, 'toruk-ordinary-v1:test');
  const pending = pendingMessages([], 'hello');
  const finished = completedMessages(pending, 'abc');
  assert.deepEqual(finished.map(item => item.role), ['user', 'assistant']);
  assert.deepEqual(clearedMessages(), []);
  assert.deepEqual(finished.map(item => item.role), ['user', 'assistant']);
});

test('status retains the full backbone and trained selector identities', async () => {
  const digest = 'a'.repeat(64);
  const response = await statusResponse({
    env,
    fetchImpl: async () => Response.json({
      ready: true, backend: 'Toruk', model: 'ollama/llama3.2:latest@aaaaaaaaaaaa',
      backbone: 'ollama/llama3.2:latest', backbone_digest: digest,
      selector_sha256: 'b'.repeat(64), selector_kind: 'toruk-chat-selector-v1',
    }),
  });
  const status = await response.json();
  assert.equal(status.backbone_digest, digest);
  assert.equal(status.selector_sha256, 'b'.repeat(64));
  assert.equal(status.selector_kind, 'toruk-chat-selector-v1');
});

test('follow-up request forwards the browser history in order', async () => {
  const refusal = "I'm sorry for any confusion, but as a chatbot, I don't have the capability to access or interact with online content.";
  const first = completedMessages(pendingMessages([], 'open youtube'), refusal);
  const second = completedMessages(pendingMessages(first, 'what is 5'), refusal);
  const history = pendingMessages(second, 'what is 5+5');
  assert.deepEqual(history.map(item => item.role), ['user', 'assistant', 'user', 'assistant', 'user']);
  const response = await chatResponse(request(history), {
    env,
    fetchImpl: async (_url, options) => {
      assert.deepEqual(JSON.parse(options.body).messages, history);
      return Response.json({answer: '10', metrics: {...metrics, input_tokens: 120, selected_context_tokens: 120, total_tokens: 123, selected_message_ids: ['m0', 'm1', 'm2', 'm3', 'm4']}});
    },
    logger: {info(){}, error(){}},
  });
  assert.equal(response.status, 200);
  assert.equal((await response.json()).answer, '10');
  assert.deepEqual(pendingMessages(clearedMessages(), 'what is 5+5'), [
    {role: 'user', content: 'what is 5+5'},
  ]);
});

test('full reported history reaches inference without dropped or rewritten turns', async () => {
  const refusal = "I'm sorry for any confusion, but as a chatbot, I don't have the capability to access or interact with online content.";
  const history = [
    {role: 'user', content: 'hello'},
    {role: 'assistant', content: 'Hello! How can I help you today?'},
    {role: 'user', content: 'what are you?'},
    {role: 'assistant', content: "I'm a chatbot designed to assist users with various topics."},
    {role: 'user', content: 'i am JinSakai'},
    {role: 'assistant', content: "I'm sorry for any confusion, but as a chatbot, I don't have the ability to assist with specific queries or provide information about specific topics."},
    {role: 'user', content: 'open youtube'},
    {role: 'assistant', content: refusal},
    {role: 'user', content: 'what is 5'},
    {role: 'assistant', content: refusal},
  ];
  const pending = pendingMessages(history, 'what is 5+5');
  const response = await chatResponse(request(pending, 32), {
    env,
    fetchImpl: async (_url, options) => {
      assert.deepEqual(JSON.parse(options.body).messages, pending);
      return Response.json({answer: refusal, metrics: {...metrics, input_tokens: 300, selected_context_tokens: 300, total_tokens: 303, selected_message_ids: pending.map((_, index) => `m${index}`)}});
    },
    logger: {info(){}, error(){}},
  });
  assert.equal(response.status, 200);
  assert.equal((await response.json()).answer, refusal);
  assert.deepEqual(pendingMessages(clearedMessages(), 'what is 5+5'), [
    {role: 'user', content: 'what is 5+5'},
  ]);
});

test('TORUK metrics are accepted only for a matching TORUK request', async () => {
  const torukRequest = new Request('http://localhost/api/chat', {
    method: 'POST', body: JSON.stringify({messages: user, mode: 'TORUK'}),
  });
  const response = await chatResponse(torukRequest, {
    env,
    fetchImpl: async () => Response.json({answer: 'remembered', metrics: {...metrics, mode: 'TORUK', memory_used: true}}),
    logger: {info(){},error(){}},
  });
  assert.equal(response.status, 200);
  assert.equal((await response.json()).metrics.memory_used, true);
});

test('production and preview reject a plaintext backend URL', async () => {
  for (const target of ['production', 'preview']) {
    const response = await chatResponse(request(user), {
      env: {...env, VERCEL_ENV: target},
      fetchImpl: async () => { throw new Error('should not fetch'); },
    });
    assert.equal(response.status, 503);
  }
});

test('backend timeout is a bounded visible error', async () => {
  const response = await chatResponse(request(user), {
    env,
    fetchImpl: async () => { throw new DOMException('Timed out', 'TimeoutError'); },
    logger: {info(){},error(){}},
  });
  assert.equal(response.status, 504);
  assert.match((await response.json()).error, /timed out/);
});

test('static Vercel project declares bounded API functions and visible mode labels', async () => {
  const config = JSON.parse(await readFile(new URL('../vercel.json', import.meta.url), 'utf8'));
  const page = await readFile(new URL('../public/index.html', import.meta.url), 'utf8');
  assert.equal(config.functions['api/chat.js'].maxDuration, 70);
  assert.match(page, /BASELINE: recent turns/);
  assert.match(page, /TORUK: selected turns/);
  assert.match(page, /Experimental chat/);
  assert.match(page, /% retained/);
  assert.match(page, /History clears on refresh/);
});
