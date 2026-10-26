import {createServer} from 'node:http';
import {readFile} from 'node:fs/promises';
import {fileURLToPath} from 'node:url';
import {dirname, join} from 'node:path';
import {POST as chat} from '../api/chat.js';
import {GET as status} from '../api/status.js';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const port = Number(process.env.PORT || 3000);
if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error('Invalid PORT');

async function writeResponse(response, outgoing) {
  outgoing.writeHead(response.status, Object.fromEntries(response.headers));
  outgoing.end(Buffer.from(await response.arrayBuffer()));
}

const server = createServer(async (incoming, outgoing) => {
  try {
    if (incoming.method === 'GET' && incoming.url === '/') {
      outgoing.writeHead(200, {'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store'});
      outgoing.end(await readFile(join(root, 'public/index.html')));
      return;
    }
    if (incoming.method === 'GET' && incoming.url === '/chat_state.js') {
      outgoing.writeHead(200, {'Content-Type': 'text/javascript; charset=utf-8', 'Cache-Control': 'no-store'});
      outgoing.end(await readFile(join(root, 'public/chat_state.js')));
      return;
    }
    if (incoming.method === 'GET' && incoming.url === '/api/status') {
      await writeResponse(await status(), outgoing);
      return;
    }
    if (incoming.method === 'POST' && incoming.url === '/api/chat') {
      const chunks = [];
      let total = 0;
      for await (const chunk of incoming) {
        total += chunk.length;
        if (total > 16384) { outgoing.writeHead(413); outgoing.end('Request too large'); return; }
        chunks.push(chunk);
      }
      const request = new Request(`http://127.0.0.1:${port}/api/chat`, {
        method: 'POST', headers: incoming.headers, body: Buffer.concat(chunks),
      });
      await writeResponse(await chat(request), outgoing);
      return;
    }
    outgoing.writeHead(404);
    outgoing.end('Not found');
  } catch (error) {
    console.error('Local web server error', error);
    outgoing.writeHead(500);
    outgoing.end('Local server error');
  }
});

server.listen(port, '127.0.0.1', () => {
  console.log(`Toruk Vercel site preview: http://127.0.0.1:${port}`);
});
