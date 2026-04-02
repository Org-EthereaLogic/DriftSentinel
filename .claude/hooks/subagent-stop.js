#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');
const { appendToLog, ensureSessionLogDir, readStdin } = require('./utils');

async function main() {
  try {
    const input = await readStdin();
    const sessionId = input.session_id || 'unknown';
    appendToLog(sessionId, 'subagent_stop.json', input);

    if (input.transcript_path && fs.existsSync(input.transcript_path)) {
      try {
        const raw = fs.readFileSync(input.transcript_path, 'utf8');
        const chatData = raw.split('\n')
          .filter(line => line.trim())
          .map(line => { try { return JSON.parse(line); } catch { return null; } })
          .filter(Boolean);
        const dir = ensureSessionLogDir(sessionId);
        fs.writeFileSync(path.join(dir, 'subagent_chat.json'), JSON.stringify(chatData, null, 2));
      } catch { /* non-fatal */ }
    }

    process.exit(0);
  } catch {
    process.exit(0);
  }
}

main();
