#!/usr/bin/env node
'use strict';

const { appendToLog, readStdin } = require('./utils');

async function main() {
  try {
    const input = await readStdin();
    const sessionId = input.session_id || 'unknown';
    appendToLog(sessionId, 'user_prompt_submit.json', input);
    process.exit(0);
  } catch {
    process.exit(0);
  }
}

main();
