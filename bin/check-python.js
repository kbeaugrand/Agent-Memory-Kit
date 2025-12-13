#!/usr/bin/env node
'use strict';

const { spawnSync } = require('child_process');

const MIN_PY = 'import sys; sys.exit(0 if sys.version_info[:2] >= (3, 9) else 1)';

function hasPython() {
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

  return candidates.some((candidate) => {
    try {
      const probe = spawnSync(
        candidate.cmd,
        [...candidate.prefixArgs, '-c', MIN_PY],
        { stdio: 'ignore' }
      );
      return probe.status === 0;
    } catch (err) {
      return false;
    }
  });
}

if (!hasPython()) {
  process.stderr.write(
    'aimem: Python 3.9+ is required to install this package.\n' +
      'Install Python from https://www.python.org/downloads/ and try again.\n'
  );
  process.exit(1);
}