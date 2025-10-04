#!/usr/bin/env node
/**
 * npm/npx launcher for the aimem Python CLI.
 *
 * This thin Node shim exists only so that `npx aimem ...` and
 * `npx github:kbeaugrand/Agent-Memory-Kit ...` work. It locates a Python 3
 * interpreter on PATH and runs the bundled, zero-dependency `aimem` package,
 * forwarding all arguments and the exit code. No pip install is required.
 */
'use strict';

const { spawnSync } = require('child_process');
const path = require('path');

const packageRoot = path.resolve(__dirname, '..');
const srcDir = path.join(packageRoot, 'src');

const MIN_PY = 'import sys; sys.exit(0 if sys.version_info[:2] >= (3, 9) else 1)';

/**
 * Return { cmd, prefixArgs } for a working Python >= 3.9, or null if none found.
 */
function findPython() {
  const candidates =
    process.platform === 'win32'
      ? [
          { cmd: 'py', prefixArgs: ['-3'] },
          { cmd: 'python', prefixArgs: [] },
          { cmd: 'python3', prefixArgs: [] },
        ]
      : [
          { cmd: 'python3', prefixArgs: [] },
          { cmd: 'python', prefixArgs: [] },
        ];

  for (const candidate of candidates) {
    try {
      const probe = spawnSync(
        candidate.cmd,
        [...candidate.prefixArgs, '-c', MIN_PY],
        { stdio: 'ignore' }
      );
      if (probe.status === 0) {
        return candidate;
      }
    } catch (err) {
      // Try the next candidate.
    }
  }
  return null;
}

function main() {
  const python = findPython();
  if (!python) {
    process.stderr.write(
      'aimem: could not find a Python 3.9+ interpreter on PATH.\n' +
        'Install Python from https://www.python.org/downloads/ and try again.\n'
    );
    process.exit(1);
  }

  const forwarded = process.argv.slice(2);
  const args = [...python.prefixArgs, '-m', 'aimem', ...forwarded];

  const env = Object.assign({}, process.env);
  env.PYTHONPATH = env.PYTHONPATH
    ? srcDir + path.delimiter + env.PYTHONPATH
    : srcDir;

  const result = spawnSync(python.cmd, args, { stdio: 'inherit', env });

  if (result.error) {
    process.stderr.write(`aimem: failed to launch Python: ${result.error.message}\n`);
    process.exit(1);
  }
  if (typeof result.status === 'number') {
    process.exit(result.status);
  }
  // Terminated by signal.
  process.exit(1);
}

main();
