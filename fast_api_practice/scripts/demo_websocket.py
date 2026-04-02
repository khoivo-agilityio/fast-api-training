#!/usr/bin/env python3
"""
WebSocket demo — end-to-end in a single script.

What it does
────────────
1. Registers two users:  owner  +  assignee
2. Owner creates a project, adds assignee as member
3. Owner creates a task assigned to assignee  (status = "todo")
4. Assignee opens a WebSocket connection and waits for notifications
5. Owner PATCHes the task status  →  "in_progress"
6. Script prints the JSON notification pushed to the assignee
7. Cleans up (WebSocket closed)

Usage (server must already be running):
  uv run uvicorn src.main:app --reload          # terminal 1
  uv run python scripts/demo_websocket.py       # terminal 2
"""

import json
import queue
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from http.client import HTTPConnection

# ── config ──────────────────────────────────────────────────────────────────
BASE = "http://localhost:8000"
WS_HOST = "localhost"
WS_PORT = 8000


# ── tiny HTTP helper (no extra deps) ────────────────────────────────────────
def http(
    method: str,
    path: str,
    body: dict | None = None,
    token: str | None = None,
    form: bool = False,
) -> dict:
    url = f"{BASE}{path}"
    if form and body:
        # application/x-www-form-urlencoded
        data = urllib.parse.urlencode(body).encode()
        content_type = "application/x-www-form-urlencoded"
    else:
        data = json.dumps(body).encode() if body else None
        content_type = "application/json"
    headers = {"Content-Type": content_type}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        msg = e.read().decode()
        print(f"  ✗  HTTP {e.code} {method} {path}: {msg}", file=sys.stderr)
        sys.exit(1)


# ── WebSocket listener (raw HTTP upgrade — stdlib only) ──────────────────────
def _ws_listen(token: str, msg_queue: queue.Queue, ready: threading.Event) -> None:
    """Open a WebSocket connection and push each received JSON frame to msg_queue."""
    import base64
    import os
    import socket
    import struct

    key = base64.b64encode(os.urandom(16)).decode()
    path = f"/ws/notifications?token={token}"

    conn = HTTPConnection(WS_HOST, WS_PORT, timeout=15)
    conn.request(
        "GET",
        path,
        headers={
            "Host": f"{WS_HOST}:{WS_PORT}",
            "Upgrade": "websocket",
            "Connection": "Upgrade",
            "Sec-WebSocket-Key": key,
            "Sec-WebSocket-Version": "13",
        },
    )
    resp = conn.getresponse()
    if resp.status != 101:
        msg_queue.put(RuntimeError(f"WebSocket upgrade failed: {resp.status}"))
        return

    # Drain response headers so the socket is ready for frame I/O
    resp.read(0)
    sock: socket.socket = conn.sock  # type: ignore[attr-defined]
    sock.settimeout(10)

    ready.set()  # signal: connection established

    # Read one text frame (opcode 0x81 or fragmented — we handle the simple case)
    try:
        # Frame header: 2 bytes minimum
        header = b""
        while len(header) < 2:
            header += sock.recv(2 - len(header))

        masked_len = header[1]
        payload_len = masked_len & 0x7F

        if payload_len == 126:
            ext = b""
            while len(ext) < 2:
                ext += sock.recv(2 - len(ext))
            payload_len = struct.unpack("!H", ext)[0]
        elif payload_len == 127:
            ext = b""
            while len(ext) < 8:
                ext += sock.recv(8 - len(ext))
            payload_len = struct.unpack("!Q", ext)[0]

        # Server → client frames are NOT masked
        payload = b""
        while len(payload) < payload_len:
            chunk = sock.recv(payload_len - len(payload))
            if not chunk:
                break
            payload += chunk

        msg_queue.put(payload.decode())
    except Exception as exc:
        msg_queue.put(exc)
    finally:
        # Send close frame (opcode 0x88, no payload, client-masked)
        try:
            mask = os.urandom(4)
            close_frame = bytes([0x88, 0x80]) + mask  # FIN+close, masked, len=0
            sock.sendall(close_frame)
        except Exception:
            pass
        conn.close()


# ── main demo ────────────────────────────────────────────────────────────────
def main() -> None:
    sep = "─" * 60

    print(sep)
    print("  WebSocket Notification Demo")
    print(sep)

    # ── 1. Register users ────────────────────────────────────────────────────
    import random

    suffix = random.randint(10000, 99999)
    owner_username = f"owner_{suffix}"
    assignee_username = f"assignee_{suffix}"
    owner_email = f"owner_{suffix}@example.com"
    assignee_email = f"assignee_{suffix}@example.com"

    print("\n[1/6] Registering users …")
    http(
        "POST",
        "/api/v1/auth/register",
        {"username": owner_username, "email": owner_email, "password": "Demo1234!"},
    )
    http(
        "POST",
        "/api/v1/auth/register",
        {
            "username": assignee_username,
            "email": assignee_email,
            "password": "Demo1234!",
        },
    )
    print(f"      owner    → {owner_username} ({owner_email})")
    print(f"      assignee → {assignee_username} ({assignee_email})")
    time.sleep(3)  # wait for bcrypt background tasks + DB commit

    # ── 2. Login both users ───────────────────────────────────────────────────
    print("\n[2/6] Logging in …")
    owner_tokens = http(
        "POST",
        "/api/v1/auth/login",
        {"username": owner_username, "password": "Demo1234!"},
        form=True,
    )
    assignee_tokens = http(
        "POST",
        "/api/v1/auth/login",
        {"username": assignee_username, "password": "Demo1234!"},
        form=True,
    )
    owner_token = owner_tokens["access_token"]
    assignee_token = assignee_tokens["access_token"]

    assignee_me = http("GET", "/api/v1/users/me", token=assignee_token)
    assignee_id = assignee_me["id"]
    print(f"      assignee user_id = {assignee_id}")

    # ── 3. Create project + add assignee as member ────────────────────────────
    print("\n[3/6] Creating project and adding assignee …")
    project = http(
        "POST",
        "/api/v1/projects",
        {"name": "Demo Project", "description": "WS demo"},
        token=owner_token,
    )
    project_id = project["id"]
    print(f"      project_id = {project_id}")

    http(
        "POST",
        f"/api/v1/projects/{project_id}/members",
        {"user_id": assignee_id, "role": "member"},
        token=owner_token,
    )
    print("      added assignee as member ✓")

    # ── 4. Create task assigned to assignee ───────────────────────────────────
    print("\n[4/6] Creating task (status=todo, assigned to assignee) …")
    task = http(
        "POST",
        f"/api/v1/projects/{project_id}/tasks",
        {
            "title": "Implement login page",
            "description": "OAuth2 flow",
            "status": "todo",
            "assignee_id": assignee_id,
        },
        token=owner_token,
    )
    task_id = task["id"]
    print(f"      task_id = {task_id}  title = \"{task['title']}\"")

    # ── 5. Open WebSocket as assignee ─────────────────────────────────────────
    print("\n[5/6] Assignee opens WebSocket connection …")
    msg_queue: queue.Queue = queue.Queue()
    ready = threading.Event()
    t = threading.Thread(
        target=_ws_listen, args=(assignee_token, msg_queue, ready), daemon=True
    )
    t.start()

    if not ready.wait(timeout=5):
        print("  ✗  WebSocket did not connect within 5 s", file=sys.stderr)
        sys.exit(1)
    print("      WebSocket connected ✓  (listening for notifications …)")

    time.sleep(0.3)  # small grace period so server registers the connection

    # ── 6. Owner PATCHes the task ─────────────────────────────────────────────
    print('\n[6/6] Owner PATCHes task status → "in_progress" …')
    updated = http(
        "PATCH",
        f"/api/v1/projects/{project_id}/tasks/{task_id}",
        {"status": "in_progress"},
        token=owner_token,
    )
    print(f"      task status is now: {updated['status']}")

    # ── 7. Print the notification ─────────────────────────────────────────────
    print()
    print(sep)
    print("  📨  Notification received by assignee:")
    print(sep)
    try:
        raw = msg_queue.get(timeout=5)
        if isinstance(raw, Exception):
            raise raw
        parsed = json.loads(raw)
        print(json.dumps(parsed, indent=2))
    except queue.Empty:
        print("  ✗  No notification received within 5 s", file=sys.stderr)
        sys.exit(1)

    t.join(timeout=2)
    print(sep)
    print("  ✅  Demo complete!")
    print(sep)


if __name__ == "__main__":
    main()
