#!/bin/bash
set -e

# Install pytest if not already installed
pip install pytest 2>/dev/null || python3 -m pip install pytest 2>/dev/null || true

# Create directories
mkdir -p /home/user/var
mkdir -p /home/user/etc
mkdir -p /home/user/init.d
mkdir -p /home/user/rc.d
mkdir -p /home/user/systemd
mkdir -p /home/user/spool
mkdir -p /home/user/tests

# Create test files
cat > /home/user/tests/__init__.py << 'PYEOF'
PYEOF

cat > /home/user/tests/test_daemon.py << 'PYEOF'
import os
import signal
import subprocess
import time
import pytest

PID_FILE = "/home/user/var/metricsaggd.pid"
LOG_FILE = "/home/user/var/metricsaggd.log"
DAEMON = "/home/user/metricsaggd.py"
CONFIG = "/home/user/etc/metricsaggd.conf"


def _cleanup_daemon():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE) as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)
        except (OSError, ValueError):
            pass
        time.sleep(0.5)
    for f in [PID_FILE, LOG_FILE]:
        if os.path.exists(f):
            try:
                os.remove(f)
            except OSError:
                pass


@pytest.fixture(autouse=True)
def cleanup():
    _cleanup_daemon()
    yield
    _cleanup_daemon()


def _wait_for_pid():
    for _ in range(50):
        if os.path.exists(PID_FILE):
            return
        time.sleep(0.1)


def test_pid_file_and_start_log():
    p = subprocess.Popen(["python3", DAEMON, "--config", CONFIG])
    try:
        _wait_for_pid()
        assert os.path.exists(PID_FILE), "PID file not created"
        with open(PID_FILE) as f:
            pid = int(f.read().strip())
        assert pid == p.pid, f"PID mismatch: file={pid}, proc={p.pid}"
        with open(LOG_FILE) as f:
            content = f.read()
        assert f"START {pid}" in content, f"START log missing: {content}"
    finally:
        p.terminate()
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            p.kill()


def test_periodic_ticks():
    p = subprocess.Popen(["python3", DAEMON, "--config", CONFIG])
    try:
        _wait_for_pid()
        time.sleep(3)
        with open(LOG_FILE) as f:
            content = f.read()
        ticks = [l for l in content.split("\n") if l.startswith("TICK")]
        assert len(ticks) >= 2, f"Expected >=2 ticks, got {len(ticks)}"
    finally:
        p.terminate()
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            p.kill()


def test_sigterm_cleanup():
    p = subprocess.Popen(["python3", DAEMON, "--config", CONFIG])
    _wait_for_pid()
    p.send_signal(signal.SIGTERM)
    try:
        p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        p.kill()
        pytest.fail("Daemon did not exit on SIGTERM")
    assert not os.path.exists(PID_FILE), "PID file not removed"
    with open(LOG_FILE) as f:
        content = f.read()
    assert "STOP SIGTERM" in content, f"STOP SIGTERM log missing: {content}"


def test_sighup_reload():
    p = subprocess.Popen(["python3", DAEMON, "--config", CONFIG])
    try:
        _wait_for_pid()
        p.send_signal(signal.SIGHUP)
        time.sleep(1)
        assert p.poll() is None, "Process exited on SIGHUP"
        with open(LOG_FILE) as f:
            content = f.read()
        assert "RELOAD" in content, f"RELOAD log missing: {content}"
    finally:
        p.terminate()
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            p.kill()
PYEOF

cat > /home/user/tests/test_cli.py << 'PYEOF'
import os
import json
import subprocess
import time
import signal
import pytest

PID_FILE = "/home/user/var/metricsaggd.pid"
LOG_FILE = "/home/user/var/metricsaggd.log"
ENABLED_FILE = "/home/user/var/enabled.json"
CLI = "/home/user/svc.py"


def _cleanup():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE) as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)
        except (OSError, ValueError):
            pass
        time.sleep(0.5)
    for f in [PID_FILE, LOG_FILE, ENABLED_FILE]:
        if os.path.exists(f):
            try:
                os.remove(f)
            except OSError:
                pass


@pytest.fixture(autouse=True)
def cleanup():
    _cleanup()
    yield
    _cleanup()


def run_cli(*args):
    return subprocess.run(["python3", CLI] + list(args), capture_output=True, text=True)


def test_start_stop():
    r = run_cli("start", "metricsaggd")
    assert r.returncode == 0, f"start failed: {r.stderr}"
    time.sleep(0.5)
    r = run_cli("stop", "metricsaggd")
    assert r.returncode == 0, f"stop failed: {r.stderr}"


def test_status_active_inactive():
    r = run_cli("start", "metricsaggd")
    assert r.returncode == 0, f"start failed: {r.stderr}"
    time.sleep(1)
    r = run_cli("status", "metricsaggd")
    assert r.returncode == 0, f"status active failed: {r.stderr}"
    assert "active" in r.stdout, f"Expected 'active' in: {r.stdout}"
    r = run_cli("stop", "metricsaggd")
    assert r.returncode == 0
    time.sleep(1)
    r = run_cli("status", "metricsaggd")
    assert r.returncode == 3, f"status inactive should return 3, got {r.returncode}"
    assert "inactive" in r.stdout, f"Expected 'inactive' in: {r.stdout}"


def test_is_active():
    r = run_cli("start", "metricsaggd")
    assert r.returncode == 0
    time.sleep(1)
    r = run_cli("is-active", "metricsaggd")
    assert r.returncode == 0, f"is-active should return 0 when active"
    r = run_cli("stop", "metricsaggd")
    assert r.returncode == 0
    time.sleep(1)
    r = run_cli("is-active", "metricsaggd")
    assert r.returncode == 3, f"is-active should return 3 when inactive"


def test_enable_disable():
    r = run_cli("enable", "metricsaggd")
    assert r.returncode == 0, f"enable failed: {r.stderr}"
    assert os.path.exists(ENABLED_FILE)
    with open(ENABLED_FILE) as f:
        data = json.load(f)
    assert "metricsaggd" in data, f"metricsaggd not in enabled: {data}"
    r = run_cli("disable", "metricsaggd")
    assert r.returncode == 0, f"disable failed: {r.stderr}"
    with open(ENABLED_FILE) as f:
        data = json.load(f)
    assert "metricsaggd" not in data, f"metricsaggd should not be in enabled: {data}"


def test_is_enabled():
    r = run_cli("is-enabled", "metricsaggd")
    assert r.returncode == 1, f"is-enabled should return 1 when not enabled, got {r.returncode}"
    r = run_cli("enable", "metricsaggd")
    assert r.returncode == 0
    r = run_cli("is-enabled", "metricsaggd")
    assert r.returncode == 0, f"is-enabled should return 0 when enabled"
    r = run_cli("disable", "metricsaggd")
    assert r.returncode == 0
    r = run_cli("is-enabled", "metricsaggd")
    assert r.returncode == 1, f"is-enabled should return 1 after disable"


def test_list():
    r = run_cli("enable", "metricsaggd")
    assert r.returncode == 0
    r = run_cli("list")
    assert r.returncode == 0, f"list failed: {r.stderr}"
    lines = r.stdout.strip().split("\n")
    matching = [l for l in lines if l.startswith("metricsaggd\t")]
    assert len(matching) >= 1, f"Expected metricsaggd in list: {r.stdout}"
    parts = matching[0].split("\t")
    assert len(parts) >= 2
    assert parts[1] in ["active", "inactive"], f"Unexpected state: {parts[1]}"
PYEOF

cat > /home/user/tests/test_init.py << 'PYEOF'
import os
import subprocess
import time
import signal
import pytest

PID_FILE = "/home/user/var/metricsaggd.pid"
LOG_FILE = "/home/user/var/metricsaggd.log"
INIT_SCRIPT = "/home/user/init.d/metricsaggd"
DAEMON = "/home/user/metricsaggd.py"
CONFIG = "/home/user/etc/metricsaggd.conf"


def _cleanup():
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE) as f:
                pid = int(f.read().strip())
            os.kill(pid, signal.SIGTERM)
        except (OSError, ValueError):
            pass
        time.sleep(0.5)
    for f in [PID_FILE, LOG_FILE]:
        if os.path.exists(f):
            try:
                os.remove(f)
            except OSError:
                pass


@pytest.fixture(autouse=True)
def cleanup():
    _cleanup()
    yield
    _cleanup()


def test_status_inactive():
    r = subprocess.run([INIT_SCRIPT, "status"], capture_output=True, text=True)
    assert r.returncode == 3, f"Expected 3 when inactive, got {r.returncode}: {r.stdout} {r.stderr}"


def test_status_active():
    p = subprocess.Popen(["python3", DAEMON, "--config", CONFIG])
    try:
        for _ in range(50):
            if os.path.exists(PID_FILE):
                break
            time.sleep(0.1)
        r = subprocess.run([INIT_SCRIPT, "status"], capture_output=True, text=True)
        assert r.returncode == 0, f"Expected 0 when active, got {r.returncode}: {r.stdout} {r.stderr}"
        assert "active" in r.stdout, f"Expected 'active' in: {r.stdout}"
    finally:
        p.terminate()
        try:
            p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            p.kill()


def test_lsb_header():
    with open(INIT_SCRIPT) as f:
        content = f.read()
    assert "### BEGIN INIT INFO" in content
    assert "### END INIT INFO" in content
    assert "# Provides: metricsaggd" in content
    assert "# Required-Start:" in content
    assert "# Default-Start:" in content
    assert "# Default-Stop:" in content
    assert "# Description:" in content


def test_executable():
    assert os.access(INIT_SCRIPT, os.X_OK), "Init script not executable"
PYEOF

cat > /home/user/tests/test_systemd.py << 'PYEOF'
import os
import configparser

UNIT_FILE = "/home/user/systemd/metricsaggd.service"


def test_exists():
    assert os.path.exists(UNIT_FILE), f"Unit file not found: {UNIT_FILE}"


def test_parse():
    config = configparser.ConfigParser()
    config.read(UNIT_FILE)
    assert config.has_section("Unit"), "Missing [Unit] section"
    assert config.has_section("Service"), "Missing [Service] section"
    assert config.has_section("Install"), "Missing [Install] section"


def test_execstart():
    config = configparser.ConfigParser()
    config.read(UNIT_FILE)
    execstart = config["Service"]["ExecStart"]
    assert "metricsaggd.py" in execstart, f"ExecStart missing daemon: {execstart}"
    assert "/home/user/etc/metricsaggd.conf" in execstart, f"ExecStart missing config: {execstart}"


def test_pidfile():
    config = configparser.ConfigParser()
    config.read(UNIT_FILE)
    assert config["Service"]["PIDFile"] == "/home/user/var/metricsaggd.pid"


def test_restart():
    config = configparser.ConfigParser()
    config.read(UNIT_FILE)
    assert config["Service"]["Restart"] == "on-failure"


def test_execreload():
    config = configparser.ConfigParser()
    config.read(UNIT_FILE)
    assert "HUP" in config["Service"]["ExecReload"]


def test_wantedby():
    config = configparser.ConfigParser()
    config.read(UNIT_FILE)
    assert config["Install"]["WantedBy"] == "multi-user.target"
PYEOF

cat > /home/user/tests/test_runlevels.py << 'PYEOF'
import os


def test_s_symlink():
    path = "/home/user/rc.d/S99metricsaggd"
    assert os.path.islink(path), f"{path} is not a symlink"
    assert os.readlink(path) == "../init.d/metricsaggd", f"Wrong target: {os.readlink(path)}"


def test_k_symlink():
    path = "/home/user/rc.d/K01metricsaggd"
    assert os.path.islink(path), f"{path} is not a symlink"
    assert os.readlink(path) == "../init.d/metricsaggd", f"Wrong target: {os.readlink(path)}"
PYEOF

# Set permissions
chmod -R 777 /home/user
