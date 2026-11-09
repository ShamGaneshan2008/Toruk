import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import test from 'node:test';
import vm from 'node:vm';
import * as state from '../public/chat_state.js';

// Execute the actual inline page handlers with a small DOM stand-in. This is a
// control/transport test, not a claim of visual or interactive browser validation.
async function pageHarness(fetchImpl, html) {
  html ??= await readFile(new URL('../public/index.html', import.meta.url), 'utf8');
  class Element {
    disabled = true;
    textContent = '';
    value = '';
    children = [];
    events = {};
    addEventListener(name, handler) { this.events[name] = handler; }
    append(...items) { this.children.push(...items); }
    replaceChildren() { this.children = []; }
    focus() {}
    querySelector() { return this.option ??= new Element(); }
  }
  const elements = new Map();
  const get = id => {
    if (!elements.has(id)) elements.set(id, new Element());
    return elements.get(id);
  };
  get('mode').value = 'BASELINE';
  get('length').value = '32';
  get('temperature').value = '0';
  get('top-p').value = '1';
  const inline = html.match(/<script type="module">([\s\S]*?)<\/script>/)[1];
  const script = inline.replace(/import \{[^}]+\} from '\.\/chat_state\.js';/, '');
  vm.runInNewContext(script, {
    ...state,
    document: {getElementById: get, createElement: () => new Element()},
    fetch: fetchImpl,
  });
  await new Promise(resolve => setImmediate(resolve));
  return {
    get,
    retry: () => get('retry').events.click(),
    clear: () => get('clear').events.click(),
    async send(content) {
      assert.equal(get('message').disabled, false, 'message box must allow typing');
      assert.equal(get('send').disabled, false, 'Send must be enabled');
      get('message').value = content;
      await get('form').events.submit({preventDefault(){}});
    },
  };
}

test('page disables chat with a reason, recovers on Retry, and sends generated history', async () => {
  let ready = false;
  let offline = false;
  const requests = [];
  const ui = await pageHarness(async (url, options) => {
    if (offline) throw new Error('private-fetch-detail');
    if (url === '/api/status') return Response.json({ready, backend: 'Toruk', model: 'Qwen:test', error: ready ? null : 'Chat model files are missing. Complete setup and restart.'});
    requests.push(JSON.parse(options.body));
    assert.equal(ui.get('message').disabled, true, 'typing pauses during generation');
    assert.equal(ui.get('send').disabled, true);
    assert.equal(ui.get('retry').disabled, true);
    return Response.json({answer: requests.length === 1 ? 'Your name is Mira.' : 'Mira.', metrics: {mode: 'BASELINE', backbone: 'Qwen', input_tokens: 40, selected_context_tokens: 40, output_tokens: 5, response_ms: 20, memory_used: false}});
  });
  assert.equal(ui.get('message').disabled, true);
  assert.equal(ui.get('send').disabled, true);
  assert.match(ui.get('error').textContent, /files are missing/);
  ready = true;
  await ui.retry();
  assert.equal(ui.get('error').textContent, '');
  await ui.send('My name is Mira.');
  assert.equal(ui.get('transcript').children[1].children[0].textContent, 'Assistant');
  await ui.send('What is my name?');
  assert.deepEqual(requests[1].messages, [
    {role: 'user', content: 'My name is Mira.'},
    {role: 'assistant', content: 'Your name is Mira.'},
    {role: 'user', content: 'What is my name?'},
  ]);
  assert.equal(ui.get('message').disabled, false);
  assert.equal(ui.get('message').value, '');
  offline = true;
  await ui.retry();
  assert.equal(ui.get('message').disabled, true);
  assert.equal(ui.get('send').disabled, true);
  assert.doesNotMatch(ui.get('error').textContent, /private-fetch-detail/);
});

test('live page handlers send a normal question and follow-up through the real proxy', {
  skip: !process.env.TORUK_LIVE_WEB_URL,
  timeout: 120000,
}, async () => {
  const origin = process.env.TORUK_LIVE_WEB_URL;
  const page = await fetch(origin + '/');
  assert.equal(page.status, 200);
  const turns = [];
  const ui = await pageHarness(async (path, options) => {
    const response = await fetch(origin + path, options);
    if (path === '/api/chat') {
      const body = await response.clone().json();
      turns.push({request: JSON.parse(options.body), http_status: response.status, response: body});
      assert.equal(response.status, 200);
      if (process.env.TORUK_TEST_BACKBONE) {
        assert.equal(body.metrics.backbone, process.env.TORUK_TEST_BACKBONE);
      } else {
        assert.match(body.metrics.backbone, /Qwen2\.5-0\.5B-Instruct/);
      }
    }
    return response;
  }, await page.text());
  // The real status request is asynchronous; await the same explicit retry path.
  await ui.retry();
  await ui.send('What is the capital of France?');
  ui.clear();
  await ui.send('My name is Mira.');
  await ui.send('What is my name?');
  ui.clear();
  await ui.send('The meeting is on Monday.');
  await ui.send('Correction: the meeting is on Friday. Which day is it now?');
  ui.clear();
  await ui.send('What is my childhood teacher\'s name? I have not provided it.');
  assert.equal(turns.length, 6);
  assert.equal(turns[2].request.messages[1].content, turns[1].response.answer);
  if (process.env.TORUK_TEST_CONTEXT === 'lexical-v2') {
    ui.clear();
    ui.get('mode').value = 'TORUK';
    await ui.send('My parcel code is PINE-54.');
    await ui.send('What is 2 + 3?');
    await ui.send('What parcel code did I give you? Reply with only the code.');
    const last = turns.at(-1);
    assert.equal(last.response.metrics.mode, 'TORUK');
    assert.equal(last.response.metrics.selector_id, 'lexical-v2');
    assert.equal(last.response.metrics.memory_used, true);
    assert.ok(last.response.metrics.selected_message_ids.includes('m0'));
    assert.match(last.response.answer, /PINE-54/);
  }
  assert.equal(ui.get('message').disabled, false);
  assert.equal(ui.get('send').disabled, false);
  console.log(JSON.stringify({surface: 'actual page handlers in DOM harness; interactive browser unrun', controls_enabled: true, turns}));
});
