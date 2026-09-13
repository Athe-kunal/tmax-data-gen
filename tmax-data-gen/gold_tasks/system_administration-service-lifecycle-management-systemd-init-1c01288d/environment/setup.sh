#!/bin/bash
set -e

# Ensure pytest is available
pip install pytest >/dev/null 2>&1 || python3 -m pip install pytest >/dev/null 2>&1 || true

# Create runtime directories
mkdir -p /home/user/var
mkdir -p /home/user/etc
mkdir -p /home/user/spool/incoming
mkdir -p /home/user/spool/shipped
mkdir -p /home/user/systemd
mkdir -p /home/user/tests

# Stub daemon (agent will replace)
cat > /home/user/logshipperd.py <<'EOF'
#!/usr/bin/env python3
# TODO: implement logshipperd daemon
EOF

# Stub CLI (agent will replace)
cat > /home/user/svcctl.py <<'EOF'
#!/usr/bin/env python3
# TODO: implement svcctl CLI
EOF

# pyproject.toml
cat > /home/user/pyproject.toml <<'EOF'
[build-system]
requires = ["setuptools>=61"]
build-backend = "setuptools.build_meta"

[project]
name = "logshipper"
version = "0.1.0"
requires-python = ">=3.8"

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"
EOF

# conftest.py
cat > /home/user/tests/conftest.py <<'EOF'
import json
import os
import signal
import time
from pathlib import Path
import pytest

PID_FILE   = Path("/home/user/var/logshipperd.pid")
LOG_FILE   = Path("/home/user/var/logshipperd.log")
ENABLED    = Path("/home/user/var/enabled.json")

def _kill_daemon():
    if PID_FILE.exists():
        try:
            os.kill(int(PID_FILE.read_text().strip()), signal.SIGTERM)
        except (ProcessLookupError, ValueError, PermissionError):
            pass
        time.sleep(0.3)
    for f in (PID_FILE, LOG_FILE, ENABLED):
        if f.exists():
            try: f.unlink()
            except IsADirectoryError: pass

@pytest.fixture(autouse=True)
def _isolate():
    _kill_daemon()
    # clean spool dirs except keep the dirs
    for d in ("/home/user/spool/incoming", "/home/user/spool/shipped"):
        for p in Path(d).iterdir():
            if p.is_file(): p.unlink()
    yield
    _kill_daemon()
EOF

# test_daemon.py
cat > /home/user/tests/test_daemon.py <<'EOF'
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

DAEMON  = "/home/user/logshipperd.py"
CONFIG  = "/home/user/etc/logshipper.conf"
PID_FILE = Path("/home/user/var/logshipperd.pid")
LOG_FILE = Path("/home/user/var/logshipperd.log")
INCOMING = Path("/home/user/spool/incoming")
SHIPPED  = Path("/home/user/spool/shipped")


def _wait_for_pid(timeout=3.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if PID_FILE.exists():
            try:
                return int(PID_FILE.read_text().strip())
            except ValueError:
                pass
        time.sleep(0.05)
    return None


def _wait_for_file(path, timeout=5.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if Path(path).exists():
            return True
        time.sleep(0.05)
    return False


def _kill_and_cleanup(proc=None):
    if proc is not None and proc.poll() is None:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
    if PID_FILE.exists():
        try:
            os.kill(int(PID_FILE.read_text().strip()), signal.SIGTERM)
        except Exception:
            pass
        time.sleep(0.3)
    for f in (PID_FILE, LOG_FILE):
        if f.exists():
            try: f.unlink()
            except IsADirectoryError: pass


@pytest.fixture
def daemon_proc():
    proc = subprocess.Popen(
        [sys.executable, DAEMON, "--config", CONFIG],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    pid = _wait_for_pid(3.0)
    assert pid is not None, "Daemon did not write PID file in time"
    yield proc, pid
    _kill_and_cleanup(proc)


def test_start_writes_pid_file(daemon_proc):
    proc, pid = daemon_proc
    assert PID_FILE.exists()
    text = PID_FILE.read_text().strip()
    assert text.isdigit()
    assert int(text) == pid


def test_start_logs_start_event(daemon_proc):
    proc, pid = daemon_proc
    # give the daemon a moment to flush the START line
    deadline = time.time() + 2.0
    contents = ""
    while time.time() < deadline:
        if LOG_FILE.exists():
            contents = LOG_FILE.read_text()
            if "START" in contents:
                break
        time.sleep(0.05)
    assert "START" in contents
    assert str(pid) in contents


def test_ships_new_file(daemon_proc):
    proc, pid = daemon_proc
    payload = b"hello world log\n"
    (INCOMING / "foo.log").write_bytes(payload)
    assert _wait_for_file(SHIPPED / "foo.log.shipped", timeout=5.0)
    assert (SHIPPED / "foo.log.shipped").read_bytes() == payload


def test_does_not_reship(daemon_proc):
    proc, pid = daemon_proc
    sentinel = b"ORIGINAL_SHIPPED_BYTES"
    (SHIPPED / "already.log.shipped").write_bytes(sentinel)
    (INCOMING / "already.log").write_bytes(b"DIFFERENT_NEW_BYTES")
    # Give the daemon time to poll
    time.sleep(2.5)
    assert (SHIPPED / "already.log.shipped").read_bytes() == sentinel


def test_sigterm_graceful_shutdown(daemon_proc):
    proc, pid = daemon_proc
    os.kill(pid, signal.SIGTERM)
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        pytest.fail("Daemon did not exit on SIGTERM")
    assert proc.returncode == 0
    # PID file should be removed
    deadline = time.time() + 2.0
    while time.time() < deadline and PID_FILE.exists():
        time.sleep(0.05)
    assert not PID_FILE.exists()
    contents = LOG_FILE.read_text()
    assert "STOP SIGTERM" in contents


def test_sighup_reloads(daemon_proc):
    proc, pid = daemon_proc
    pid_before = PID_FILE.read_text().strip()
    os.kill(pid, signal.SIGHUP)
    time.sleep(1.0)
    assert proc.poll() is None, "Daemon died on SIGHUP"
    assert PID_FILE.exists()
    assert PID_FILE.read_text().strip() == pid_before
    contents = LOG_FILE.read_text()
    assert "RELOAD" in contents
EOF

# test_svcctl.py
cat > /home/user/tests/test_svcctl.py <<'EOF'
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

SVCCTL = "/home/user/svcctl.py"
PID_FILE = Path("/home/user/var/logshipperd.pid")
LOG_FILE = Path("/home/user/var/logshipperd.log")
ENABLED  = Path("/home/user/var/enabled.json")


def _run(*args, **kwargs):
    return subprocess.run(
        [sys.executable, SVCCTL, *args],
        capture_output=True,
        text=True,
        **kwargs,
    )


def _kill_running():
    if PID_FILE.exists():
        try:
            os.kill(int(PID_FILE.read_text().strip()), signal.SIGTERM)
        except Exception:
            pass
        time.sleep(0.3)
    for f in (PID_FILE, LOG_FILE):
        if f.exists():
            try: f.unlink()
            except IsADirectoryError: pass


def test_svcctl_start_exits_zero():
    _kill_running()
    r = _run("start", "logshipperd")
    assert r.returncode == 0, r.stderr
    assert "started" in r.stdout
    assert PID_FILE.exists()
    _kill_running()


def test_svcctl_stop_exits_zero():
    _kill_running()
    _run("start", "logshipperd")
    time.sleep(0.5)
    r = _run("stop", "logshipperd")
    assert r.returncode == 0, r.stderr
    assert "stopped" in r.stdout
    deadline = time.time() + 3.0
    while time.time() < deadline and PID_FILE.exists():
        time.sleep(0.05)
    assert not PID_FILE.exists()
    _kill_running()


def test_svcctl_status_active():
    _kill_running()
    _run("start", "logshipperd")
    time.sleep(0.5)
    r = _run("status", "logshipperd")
    assert r.returncode == 0, r.stderr
    assert "active" in r.stdout
    _kill_running()


def test_svcctl_status_inactive():
    _kill_running()
    r = _run("status", "logshipperd")
    assert r.returncode == 3, r.stderr
    assert "inactive" in r.stdout


def test_svcctl_is_active_codes():
    _kill_running()
    r = _run("is-active", "logshipperd")
    assert r.returncode == 3
    _run("start", "logshipperd")
    time.sleep(0.5)
    r = _run("is-active", "logshipperd")
    assert r.returncode == 0
    _kill_running()


def test_svcctl_enable_persists():
    if ENABLED.exists():
        ENABLED.unlink()
    r = _run("enable", "logshipperd")
    assert r.returncode == 0, r.stderr
    assert "enabled" in r.stdout
    data = json.loads(ENABLED.read_text())
    assert "logshipperd" in data


def test_svcctl_disable_removes():
    if ENABLED.exists():
        ENABLED.unlink()
    _run("enable", "logshipperd")
    r = _run("disable", "logshipperd")
    assert r.returncode == 0, r.stderr
    assert "disabled" in r.stdout
    data = json.loads(ENABLED.read_text())
    assert "logshipperd" not in data


def test_svcctl_is_enabled_codes():
    if ENABLED.exists():
        ENABLED.unlink()
    r = _run("is-enabled", "logshipperd")
    assert r.returncode == 1
    _run("enable", "logshipperd")
    r = _run("is-enabled", "logshipperd")
    assert r.returncode == 0
    # cleanup
    if ENABLED.exists():
        ENABLED.unlink()


def test_svcctl_list_format():
    if ENABLED.exists():
        ENABLED.unlink()
    _run("enable", "logshipperd")
    _kill_running()
    r = _run("list")
    assert r.returncode == 0, r.stderr
    lines = [l for l in r.stdout.splitlines() if l.strip()]
    assert any("logshipperd" in l and ("active" in l or "inactive" in l) for l in lines)
    # tab-separated
    found = [l for l in lines if "logshipperd" in l]
    assert found
    assert "\t" in found[0]
    if ENABLED.exists():
        ENABLED.unlink()
EOF

# test_systemd.py
cat > /home/user/tests/test_systemd.py <<'EOF'
import configparser
from pathlib import Path

import pytest

UNIT = Path("/home/user/systemd/logshipper.service")


def test_unit_file_exists():
    assert UNIT.exists(), f"Missing unit file at {UNIT}"


def test_unit_parses_as_ini():
    cp = configparser.ConfigParser()
    cp.read(UNIT)
    assert cp.sections(), "Unit file has no sections"


def test_unit_has_required_sections():
    cp = configparser.ConfigParser()
    cp.read(UNIT)
    for s in ("Unit", "Service", "Install"):
        assert s in cp.sections(), f"Missing [{s}] section"


def test_unit_execstart():
    cp = configparser.ConfigParser()
    cp.read(UNIT)
    execstart = cp.get("Service", "ExecStart")
    assert "/home/user/logshipperd.py" in execstart
    assert "/home/user/etc/logshipper.conf" in execstart


def test_unit_pidfile():
    cp = configparser.ConfigParser()
    cp.read(UNIT)
    assert cp.get("Service", "PIDFile") == "/home/user/var/logshipperd.pid"


def test_unit_restart():
    cp = configparser.ConfigParser()
    cp.read(UNIT)
    assert cp.get("Service", "Restart") == "on-failure"


def test_unit_wantedby():
    cp = configparser.ConfigParser()
    cp.read(UNIT)
    assert cp.get("Install", "WantedBy") == "multi-user.target"


def test_unit_description_nonempty():
    cp = configparser.ConfigParser()
    cp.read(UNIT)
    assert cp.get("Unit", "Description").strip() != ""
EOF

# Make stubs executable (agent will keep them executable)
chmod +x /home/user/logshipperd.py /home/user/svcctl.py

# Ensure wide-open permissions
chmod -R 777 /home/user
