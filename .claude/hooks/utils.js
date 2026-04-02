#!/usr/bin/env node
'use strict';

const fs = require('fs');
const path = require('path');

const LOG_BASE_DIR =
  process.env.CLAUDE_HOOKS_LOG_DIR ||
  path.join(process.env.CLAUDE_PROJECT_DIR || '.', 'logs', 'hooks');

function getSessionLogDir(sessionId) {
  return path.join(LOG_BASE_DIR, sessionId);
}

function ensureSessionLogDir(sessionId) {
  const dir = getSessionLogDir(sessionId);
  fs.mkdirSync(dir, { recursive: true });
  return dir;
}

function appendToLog(sessionId, filename, entry) {
  const dir = ensureSessionLogDir(sessionId);
  const logPath = path.join(dir, filename);
  let data = [];
  if (fs.existsSync(logPath)) {
    try {
      data = JSON.parse(fs.readFileSync(logPath, 'utf8'));
    } catch {
      data = [];
    }
  }
  data.push(entry);
  fs.writeFileSync(logPath, JSON.stringify(data, null, 2));
}

function readStdin() {
  return new Promise((resolve, reject) => {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', chunk => {
      data += chunk;
    });
    process.stdin.on('end', () => {
      try {
        resolve(JSON.parse(data));
      } catch (error) {
        reject(error);
      }
    });
    process.stdin.on('error', reject);
  });
}

module.exports = { LOG_BASE_DIR, getSessionLogDir, ensureSessionLogDir, appendToLog, readStdin };
