import {chatResponse} from '../lib/proxy.js';

export async function POST(request) {
  return chatResponse(request);
}
