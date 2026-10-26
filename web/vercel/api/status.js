import {statusResponse} from '../lib/proxy.js';

export async function GET() {
  return statusResponse();
}
