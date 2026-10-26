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
