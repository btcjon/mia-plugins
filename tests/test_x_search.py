#!/usr/bin/env python3
"""Offline test for the x-search plugin. No real key, no network beyond 127.0.0.1.

1. Layout: manifest, logo, skill frontmatter, no MCP file, Rakazo's size and name rules.
2. The skill's request_secret and secret_request examples match Rakazo's input schemas
   (packages/contracts/src/bots/bot-secrets.ts, v0.13.0) and xAI's documented x_search shape.
3. Fake-key path: a fake key in a mode-600 temp file, a stand-in for Rakazo's secret_request
   (injects the bearer only at the saved origin, redacts echoes, cuts at 20,000 chars) and a
   local mock of POST /v1/responses that checks the auth header and the body. The answer and
   usage are then read at the paths the skill names. Error paths: wrong key 401, no credits 402.

Run: python3 -I tests/test_x_search.py   (exit 0 = pass)
"""
import http.server
import json
import os
import re
import stat
import struct
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN = ROOT / "x-search"
SKILL = PLUGIN / "skills" / "x-search" / "SKILL.md"
ORIGIN = "https://api.x.ai"
SECRET_NAME_RE = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")  # BotSecretName
PLUGIN_NAME_RE = re.compile(r"^[a-z0-9](?:[a-z0-9.-]{0,62}[a-z0-9])?$")
X_SEARCH_KEYS = {"type", "allowed_x_handles", "excluded_x_handles", "from_date", "to_date",
                 "enable_image_understanding", "enable_video_understanding"}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
FAILS = []


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        FAILS.append(msg)


# ---------- 1. layout ----------
def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    out, key = {}, None
    for line in m.group(1).splitlines():
        km = re.match(r"^([a-z_]+):\s*(.*)$", line)
        if km:
            key = km.group(1)
            out[key] = "" if km.group(2) in (">-", ">", "|") else km.group(2)
        elif key:
            out[key] = (out[key] + " " + line.strip()).strip()
    return out


def test_layout():
    manifest = json.loads((PLUGIN / ".grok-plugin" / "plugin.json").read_text())
    check(manifest.get("name") == "x-search", "manifest name is x-search")
    check(bool(PLUGIN_NAME_RE.match(manifest["name"])) and "--" not in manifest["name"], "manifest name follows Rakazo rules")
    for field in ("version", "description", "author", "repository", "license", "keywords", "logo"):
        check(field in manifest, f"manifest has {field}")
    desc = manifest.get("description", "")
    check("own xAI API key" in desc and "$" in desc, "manifest description names the user's key and the cost")
    logo = PLUGIN / manifest.get("logo", "")
    head = logo.read_bytes()[:24] if logo.is_file() else b""
    check(head[:8] == b"\x89PNG\r\n\x1a\n", "logo is a PNG")
    if head[:8] == b"\x89PNG\r\n\x1a\n":
        w, h = struct.unpack(">II", head[16:24])
        check((w, h) == (192, 192), "logo is 192x192 like the other cards")
    check(not (PLUGIN / ".mcp.json").exists() and not (PLUGIN / "mcp.json").exists(), "skills-only: no MCP file")
    text = SKILL.read_text()
    fm = frontmatter(text)
    check(fm.get("name") == "x-search" and len(fm["name"]) <= 80, "skill name x-search (<= 80 chars)")
    check(0 < len(fm.get("description", "")) <= 2000, "skill description present (<= 2000 chars)")
    other = {frontmatter(p.read_text()).get("name") for p in ROOT.glob("*/skills/*/SKILL.md") if p != SKILL}
    check("x-search" not in other and "read-x" not in other, "skill name distinct from the repo's other skills and read-x")
    files = [p for p in PLUGIN.rglob("*") if p.is_file()]
    check(len(files) <= 200 and all(p.stat().st_size <= 100_000 for p in files), "plugin within Rakazo file limits")
    check(not any(p.is_symlink() for p in PLUGIN.rglob("*")), "no symlinks")
    blob = "\n".join(p.read_text(errors="ignore") for p in files if p.suffix in (".md", ".json"))
    check(not re.search(r"xai-[A-Za-z0-9]{20,}", blob) and "${" not in blob, "no key or ${VAR} placeholder in plugin files")
    # user-facing text the brief asks for
    for needle, what in (("console.x.ai", "where to get a key"), ("$0.10 to $0.30", "cost per search"),
                         ("read-x", "free read-x fallback"), ("cannot search", "read-x limit"),
                         ("never into chat", "no key in chat"), ("Always allow", "approval note")):
        check(needle in text, f"skill text: {what}")
    return text


# ---------- 2. schema of the skill's examples ----------
def json_blocks(text):
    return [json.loads(b) for b in re.findall(r"```json\n(.*?)\n```", text, re.S)]


def validate_x_body(body):
    """xAI Responses + x_search request rules from docs.x.ai/developers/tools/x-search."""
    errs = []
    if not isinstance(body.get("model"), str):
        errs.append("model missing")
    if not body.get("input"):
        errs.append("input missing")
    mt = body.get("max_turns")
    if not (isinstance(mt, int) and 1 <= mt <= 2):
        errs.append("max_turns must be 1 or 2 (30 s secret_request deadline)")
    tools = body.get("tools")
    if not (isinstance(tools, list) and len(tools) == 1 and tools[0].get("type") == "x_search"):
        errs.append("tools must be exactly one x_search entry")
        return errs
    t = tools[0]
    if set(t) - X_SEARCH_KEYS:
        errs.append(f"unknown x_search keys {sorted(set(t) - X_SEARCH_KEYS)}")
    if "allowed_x_handles" in t and "excluded_x_handles" in t:
        errs.append("allowed and excluded handles together")
    for k in ("allowed_x_handles", "excluded_x_handles"):
        if k in t and (len(t[k]) > 20 or any(h.startswith("@") for h in t[k])):
            errs.append(f"{k}: max 20, no @")
    for k in ("from_date", "to_date"):
        if k in t and not DATE_RE.match(t[k]):
            errs.append(f"{k} not YYYY-MM-DD")
    if "from_date" in t and "to_date" in t and t["to_date"] <= t["from_date"]:
        errs.append("to_date must be after from_date (exclusive)")
    return errs


def test_examples(text):
    blocks = json_blocks(text)
    asks = [b for b in blocks if "credential" in b]
    reqs = [b for b in blocks if "url" in b]
    check(len(asks) == 1 and len(reqs) == 1, "skill has one request_secret and one secret_request example")
    ask, req = asks[0], reqs[0]
    cred = ask["credential"]
    check(set(ask) <= {"label", "purpose", "credential", "replace", "fields"} and ask.get("label"), "request_secret: allowed keys + label")
    check(ask.get("purpose") in ("otp", "password", "api_key"), "request_secret: purpose in Rakazo enum")
    check(bool(SECRET_NAME_RE.match(cred.get("name", ""))), "request_secret: credential name matches BotSecretName")
    check(cred.get("origin") == ORIGIN and cred.get("auth") == {"type": "bearer"}, "request_secret: https://api.x.ai with bearer auth")
    check(set(req) <= {"name", "url", "method", "body", "contentType"}, "secret_request: only SecretHttpRequest keys")
    check(req.get("name") == cred["name"], "secret_request uses the saved name")
    check(req.get("url", "").startswith(ORIGIN + "/") and req["method"] == "POST", "secret_request: POST at the saved origin")
    check(req.get("contentType", "application/json") == "application/json", "secret_request: JSON content type")
    check(isinstance(req.get("body"), str) and len(req["body"]) <= 100_000, "secret_request: body is a string <= 100k")
    body = json.loads(req["body"])
    errs = validate_x_body(body)
    check(not errs, "skill body passes x_search rules " + (str(errs) if errs else ""))
    check("$" not in req["body"] and "xai_api_key" not in req["body"], "body carries no secret placeholder")
    # the validator itself rejects bad bodies
    bad = dict(body, tools=[{"type": "x_search", "allowed_x_handles": ["@a"], "excluded_x_handles": ["b"], "from_date": "11/14/2026"}])
    check(len(validate_x_body(bad)) >= 3, "validator rejects @handles, both handle lists and bad dates")
    return ask, req


# ---------- 3. fake-key path ----------
CANNED = {
    "id": "resp_fake",
    "object": "response",
    "model": "grok-4.3",
    "output": [
        {"type": "custom_tool_call", "call_id": "xs_1", "name": "x_semantic_search", "input": "{\"query\":\"electric bikes\"}"},
        {"type": "message", "role": "assistant", "content": [{
            "type": "output_text",
            "text": "@bikefan (2026-11-18): \"E-bikes beat my car commute\" https://x.com/bikefan/status/1990000000000000001",
            "annotations": [{"type": "url_citation", "url": "https://x.com/bikefan/status/1990000000000000001",
                             "start_index": 0, "end_index": 10, "title": "1"}],
        }]},
    ],
    "usage": {"input_tokens": 9000, "output_tokens": 300,
              "server_side_tool_usage_details": {"x_search_calls": 2, "x_posts_fetched": 24, "x_users_fetched": 0}},
}


class MockXai(http.server.BaseHTTPRequestHandler):
    good_key = ""
    mode = "ok"
    seen = []

    def log_message(self, *a):
        pass

    def _send(self, code, obj):
        data = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        MockXai.seen.append({"path": self.path, "auth_ok": self.headers.get("Authorization") == f"Bearer {MockXai.good_key}", "body": body})
        if self.path != "/v1/responses":
            return self._send(404, {"error": "not found"})
        if self.headers.get("Authorization") != f"Bearer {MockXai.good_key}":
            # echo the bad key, as some APIs do, to test redaction
            return self._send(401, {"error": f"Incorrect API key provided: {self.headers.get('Authorization', '')[7:]}"})
        errs = validate_x_body(body)
        if errs:
            return self._send(400, {"error": "; ".join(errs)})
        if MockXai.mode == "no_credits":
            return self._send(402, {"error": "Your team has run out of credits."})
        resp = dict(CANNED)
        resp["echo"] = f"key was {MockXai.good_key}"  # an echo the backend must redact
        return self._send(200, resp)


def fake_secret_request(vault, mock_base, req):
    """Stand-in for Rakazo's secret_request: origin pinning, bearer injection, redaction, 20k cap."""
    saved = vault[req["name"]]
    if not req["url"].startswith(saved["origin"] + "/"):
        return {"error": "origin mismatch"}
    key = Path(saved["key_path"]).read_text().strip()
    url = mock_base + req["url"][len(saved["origin"]):]  # route api.x.ai to the local mock
    r = urllib.request.Request(url, data=req["body"].encode(), method=req["method"],
                               headers={"Content-Type": req.get("contentType", "application/json"),
                                        "Authorization": f"Bearer {key}"})
    try:
        with urllib.request.urlopen(r, timeout=30) as resp:
            status, text = resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        status, text = e.code, e.read().decode()
    text = text.replace(key, "[redacted]")[:20_000]
    return {"status": status, "body": text}


def read_answer(resp_json):
    """The paths SKILL.md step 3 tells the bot to read."""
    texts, urls = [], []
    for item in resp_json.get("output", []):
        if item.get("type") == "message":
            for c in item.get("content", []):
                if c.get("type") == "output_text":
                    texts.append(c["text"])
                    urls += [a["url"] for a in c.get("annotations", []) if a.get("type") == "url_citation"]
    usage = resp_json.get("usage", {}).get("server_side_tool_usage_details", {})
    return "\n".join(texts), urls, usage


def test_fake_key_path(ask, req):
    tmp = tempfile.mkdtemp(prefix="xsearch-test-")
    key_path = Path(tmp) / "fake-xai-key"
    fake_key = "xai-FAKE" + os.urandom(16).hex()
    fd = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.write(fd, fake_key.encode())
    os.close(fd)
    check(stat.S_IMODE(key_path.stat().st_mode) == 0o600, "fake key file is mode 600")
    MockXai.good_key = fake_key
    srv = http.server.HTTPServer(("127.0.0.1", 0), MockXai)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_port}"
    cred = ask["credential"]
    vault = {cred["name"]: {"origin": cred["origin"], "key_path": str(key_path)}}
    try:
        out = fake_secret_request(vault, base, req)
        check(out.get("status") == 200, f"search with the fake key returns 200 (got {out.get('status')})")
        check(MockXai.seen and MockXai.seen[-1]["auth_ok"], "mock saw Authorization: Bearer <fake key>")
        check(fake_key not in json.dumps(out), "fake key never appears in the result the bot reads")
        text, urls, usage = read_answer(json.loads(out["body"]))
        check("x.com/bikefan/status/" in text and urls, "answer text and post links found at the skill's paths")
        check(usage.get("x_posts_fetched") == 24, "usage x_posts_fetched found at the skill's path")
        check(len(json.dumps(CANNED)) < 20_000, "typical response fits the 20,000-char cap")
        # wrong origin is refused by the stand-in (mirrors Rakazo origin pinning)
        check("error" in fake_secret_request(vault, base, dict(req, url="https://evil.example/v1/responses")), "other origin refused")
        # wrong key -> 401, echo redacted
        bad_path = Path(tmp) / "wrong-key"
        fd = os.open(bad_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        os.write(fd, b"xai-WRONGWRONGWRONG")
        os.close(fd)
        out = fake_secret_request({cred["name"]: {"origin": cred["origin"], "key_path": str(bad_path)}}, base, req)
        check(out.get("status") == 401 and "WRONGWRONG" not in out["body"], "wrong key gives 401 and its echo is redacted")
        MockXai.mode = "no_credits"
        out = fake_secret_request(vault, base, req)
        check(out.get("status") == 402, "no credits gives 402")
        skill = SKILL.read_text()
        check("401" in skill and '"replace": true' in skill, "skill handles 401 with a replace card")
        check("402" in skill and "credits" in skill and "Never retry" in skill, "skill handles 402 without retry loops")
    finally:
        srv.shutdown()
        for p in Path(tmp).iterdir():
            p.unlink()
        os.rmdir(tmp)


if __name__ == "__main__":
    text = test_layout()
    ask, req = test_examples(text)
    test_fake_key_path(ask, req)
    print(f"\n{'PASS' if not FAILS else 'FAIL'}: {len(FAILS)} failed")
    sys.exit(1 if FAILS else 0)
