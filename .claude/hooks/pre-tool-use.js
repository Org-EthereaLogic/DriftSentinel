#!/usr/bin/env node
'use strict';

const { appendToLog, readStdin } = require('./utils');

const DANGEROUS_RM_PATTERNS = [
  /\brm\s+.*-[a-z]*r[a-z]*f/i,
  /\brm\s+.*-[a-z]*f[a-z]*r/i,
  /\brm\s+--recursive\s+--force/i,
  /\brm\s+--force\s+--recursive/i,
  /\brm\s+-r\s+.*-f/i,
  /\brm\s+-f\s+.*-r/i,
];

const DANGEROUS_PATHS = [
  /^\s*\/\s*$/,
  /\/\*/,
  /^~\/?/,
  /\$HOME/,
  /\.\./,
  /^\s*\.\s*$/,
];

function isDangerousRm(command) {
  const normalized = command.toLowerCase().replace(/\s+/g, ' ').trim();
  for (const pattern of DANGEROUS_RM_PATTERNS) {
    if (pattern.test(normalized)) return true;
  }
  if (/\brm\s+.*-[a-z]*r/i.test(normalized)) {
    for (const pathPattern of DANGEROUS_PATHS) {
      if (pathPattern.test(normalized)) return true;
    }
  }
  return false;
}

function isEnvFileAccess(toolName, toolInput) {
  if (['Read', 'Edit', 'MultiEdit', 'Write'].includes(toolName)) {
    const filePath = toolInput.file_path || '';
    if (filePath.includes('.env') && !filePath.endsWith('.env.example') && !filePath.endsWith('.env.sample')) {
      return true;
    }
  }
  if (toolName === 'Bash') {
    const command = toolInput.command || '';
    const envPatterns = [
      /\bcat\s+.*\.env\b(?!\.example|\.sample)/,
      /\becho\s+.*>\s*.*\.env\b(?!\.example|\.sample)/,
      /\btouch\s+.*\.env\b(?!\.example|\.sample)/,
      /\bcp\s+.*\.env\b(?!\.example|\.sample)/,
      /\bmv\s+.*\.env\b(?!\.example|\.sample)/,
    ];
    for (const pattern of envPatterns) {
      if (pattern.test(command)) return true;
    }
  }
  return false;
}

async function main() {
  try {
    const input = await readStdin();
    const toolName = input.tool_name || '';
    const toolInput = input.tool_input || {};

    if (isEnvFileAccess(toolName, toolInput)) {
      process.stderr.write('BLOCKED: Access to .env files containing sensitive data is prohibited.\nUse .env.example for template files instead.\n');
      process.exit(2);
    }

    if (toolName === 'Bash') {
      const command = toolInput.command || '';
      if (isDangerousRm(command)) {
        process.stderr.write('BLOCKED: Dangerous rm command detected and prevented.\n');
        process.exit(2);
      }
    }

    const sessionId = input.session_id || 'unknown';
    appendToLog(sessionId, 'pre_tool_use.json', input);
    process.exit(0);
  } catch {
    process.exit(0);
  }
}

main();
