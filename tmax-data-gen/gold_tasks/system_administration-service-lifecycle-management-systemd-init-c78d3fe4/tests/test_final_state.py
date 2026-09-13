# test_final_state.py
"""
Final-state validation suite for the metricsaggd deployment task.

This suite verifies that all deliverables exist, are correctly structured,
and behave as specified after the student's deployment is complete.

Run with:
    cd /home/user && python -m pytest -v test_final_state.py
"""
import os
import sys
import time
import json
import signal
import configparser
import subprocess
from pathlib import Path
from datetime import datetime

import pytest


# ---------------------------------------------------------------------------
# Absolute paths (no relative paths allowed per task constraints)
# ---------------------------------------------------------------------------
HOME = Path("/home/user")
DAEMON = HOME / "metricsaggd.py"
SVC = HOME / "svc.py"
INIT_SCRIPT = HOME / "init.d" / "metricsaggd"
SYSTEMD_UNIT = HOME / "systemd" / "metricsaggd.service"
RC_S_START = HOME / "rc.d" / "S99metricsaggd"
RC_K_STOP = HOME / "rc.d" / "K01metricsaggd"
DAEMON_CONF = HOME / "etc" / "metricsaggd.conf"
SERVICES_CONF = HOME / "etc" / "services.conf"
VAR_DIR = HOME / "var"
ETC_DIR = HOME / "etc"
INIT_DIR = HOME / "init.d"
RC_DIR = HOME / "rc.d"
SYSTEMD_DIR = HOME / "systemd"
SPOOL_DIR = HOME / "spool"
PID_FILE = VAR_DIR / "metricsaggd.pid"
LOG_FILE = VAR_DIR / "metricsaggd.log"
ENABLED_JSON = VAR_DIR / "enabled.json"


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------
def _cleanup_state():
    """Kill any running daemon and remove state files."""
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            os.kill(pid, signal.SIGTERM)
        except (ValueError, ProcessLookupError, PermissionError, OSError):
            pass
        # Wait briefly for the daemon to remove its PID file
        for _ in range(30):
            if not PID_FILE.exists():
                break
            time.sleep(0.1)
    for f in (PID_FILE, LOG_FILE, ENABLED_JSON):
        if f.exists():
            try:
                f.unlink()
            except OSError:
                pass


@pytest.fixture(autouse=True)
def cleanup_daemon_state():
    """Ensure no daemon is running and clean state files before/after each test."""
    _cleanup_state()
    yield
    _cleanup_state()


def _read_pid():
    """Read PID from PID file, return None if not present or invalid."""
    if not PID_FILE.exists():
        return None
    try:
        return int(PID_FILE.read_text().strip())
    except (ValueError, OSError):
        return None


def _wait_for_pid_file(timeout=3.0):
    """Wait for PID file to appear, return PID or None."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        pid = _read_pid()
        if pid is not None:
            return pid
        time.sleep(0.05)
    return None


def _wait_for_pid_file_gone(timeout=5.0):
    """Wait for PID file to disappear, return True if gone."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not PID_FILE.exists():
            return True
        time.sleep(0.05)
    return not PID_FILE.exists()


def _terminate_proc(proc, timeout=5.0):
    """Terminate a subprocess and wait for it to exit."""
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


# ---------------------------------------------------------------------------
# Directory tests
# ---------------------------------------------------------------------------
class TestDirectories:
    """Verify all required runtime directories exist."""

    @pytest.mark.parametrize("directory", [
        VAR_DIR, ETC_DIR, INIT_DIR, RC_DIR, SYSTEMD_DIR, SPOOL_DIR
    ])
    def test_directory_exists(self, directory):
        assert directory.is_dir(), (
            f"Required directory {directory} does not exist or is not a directory"
        )


# ---------------------------------------------------------------------------
# Daemon tests
# ---------------------------------------------------------------------------
class TestDaemon:
    """Verify the daemon script exists, is executable, and behaves correctly."""

    def test_daemon_script_exists(self):
        assert DAEMON.exists(), f"Daemon script {DAEMON} does not exist"

    def test_daemon_is_executable(self):
        assert os.access(DAEMON, os.X_OK), (
            f"Daemon script {DAEMON} must be executable (chmod +x)"
        )

    def test_daemon_is_valid_python(self):
        """Verify daemon compiles without syntax errors."""
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(DAEMON)],
            capture_output=True, text=True
        )
        assert result.returncode == 0, (
            f"Daemon script has syntax errors: {result.stderr}"
        )

    def test_daemon_writes_pid_file_on_start(self):
        """Daemon must write its PID to the PID file on startup."""
        proc = subprocess.Popen(
            [sys.executable, str(DAEMON), "--config", str(DAEMON_CONF)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        try:
            pid = _wait_for_pid_file(timeout=3.0)
            assert pid is not None, (
                f"PID file {PID_FILE} was not created within 3 seconds"
            )
            assert pid == proc.pid, (
                f"PID file contains {pid} but daemon's actual PID is {proc.pid}"
            )
        finally:
            _terminate_proc(proc)

    def test_daemon_pid_file_contains_only_pid(self):
        """PID file must contain only the PID as an integer string (trailing newline allowed)."""
        proc = subprocess.Popen(
            [sys.executable, str(DAEMON), "--config", str(DAEMON_CONF)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        try:
            pid = _wait_for_pid_file(timeout=3.0)
            assert pid is not None, "PID file was not created"
            content = PID_FILE.read_text()
            stripped = content.strip()
            assert stripped.isdigit(), (
                f"PID file should contain only a numeric PID, got: {content!r}"
            )
            assert int(stripped) == pid, (
                f"PID file content {stripped!r} does not match daemon PID {pid}"
            )
        finally:
            _terminate_proc(proc)

    def test_daemon_logs_start_entry(self):
        """Daemon must append 'START <pid> <iso8601>' to log file."""
        proc = subprocess.Popen(
            [sys.executable, str(DAEMON), "--config", str(DAEMON_CONF)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        try:
            deadline = time.time() + 3.0
            content = ""
            while time.time() < deadline:
                if LOG_FILE.exists():
                    content = LOG_FILE.read_text()
                    if "START" in content:
                        break
                time.sleep(0.05)
            assert "START" in content, (
                f"Log file does not contain START entry. Content: {content!r}"
            )
            lines = [l for l in content.splitlines() if l.startswith("START")]
            assert len(lines) >= 1, "No START line found in log"
            parts = lines[0].split()
            assert len(parts) == 3, (
                f"START line should have 3 parts (START, pid, timestamp), got: {lines[0]!r}"
            )
            assert parts[0] == "START"
            assert parts[1].isdigit(), (
                f"PID in START line should be numeric, got: {parts[1]!r}"
            )
            try:
                datetime.fromisoformat(parts[2])
            except ValueError:
                pytest.fail(
                    f"Timestamp in START line is not valid ISO 8601: {parts[2]!r}"
                )
        finally:
            _terminate_proc(proc)

    def test_daemon_writes_periodic_ticks(self):
        """Daemon must write TICK entries every tick_interval seconds."""
        proc = subprocess.Popen(
            [sys.executable, str(DAEMON), "--config", str(DAEMON_CONF)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        try:
            # Wait at least 3 seconds; tick_interval=1 should produce >=2 ticks
            time.sleep(3.5)
            assert LOG_FILE.exists(), "Log file was not created"
            content = LOG_FILE.read_text()
            tick_lines = [l for l in content.splitlines() if l.startswith("TICK ")]
            assert len(tick_lines) >= 2, (
                f"Expected at least 2 TICK entries after 3 seconds, "
                f"got {len(tick_lines)}: {tick_lines!r}"
            )
            parts = tick_lines[0].split()
            assert len(parts) == 2, (
                f"TICK line should have 2 parts (TICK, timestamp), got: {tick_lines[0]!r}"
            )
            try:
                datetime.fromisoformat(parts[1])
            except ValueError:
                pytest.fail(
                    f"Timestamp in TICK line is not valid ISO 8601: {parts[1]!r}"
                )
        finally:
            _terminate_proc(proc)

    def test_daemon_sigterm_clean_shutdown(self):
        """SIGTERM must remove PID file and write STOP SIGTERM log entry."""
        proc = subprocess.Popen(
            [sys.executable, str(DAEMON), "--config", str(DAEMON_CONF)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        pid = _wait_for_pid_file(timeout=3.0)
        assert pid is not None, "PID file was not created"

        proc.send_signal(signal.SIGTERM)
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            pytest.fail("Daemon did not terminate within 5 seconds of SIGTERM")

        gone = _wait_for_pid_file_gone(timeout=5.0)
        assert gone, f"PID file {PID_FILE} was not removed after SIGTERM"

        assert LOG_FILE.exists(), "Log file missing"
        content = LOG_FILE.read_text()
        assert "STOP SIGTERM" in content, (
            f"Expected 'STOP SIGTERM' in log, got: {content!r}"
        )

    def test_daemon_sighup_reload(self):
        """SIGHUP must write RELOAD log entry without killing the process."""
        proc = subprocess.Popen(
            [sys.executable, str(DAEMON), "--config", str(DAEMON_CONF)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        try:
            pid = _wait_for_pid_file(timeout=3.0)
            assert pid is not None, "PID file was not created"

            proc.send_signal(signal.SIGHUP)
            time.sleep(1.0)

            assert proc.poll() is None, (
                "Daemon terminated after SIGHUP (should only reload)"
            )

            assert LOG_FILE.exists(), "Log file missing"
            content = LOG_FILE.read_text()
            assert "RELOAD" in content, (
                f"Expected 'RELOAD' in log after SIGHUP, got: {content!r}"
            )
        finally:
            _terminate_proc(proc)


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------
class TestCLI:
    """Verify the service control CLI exists, is executable, and behaves correctly."""

    def test_cli_script_exists(self):
        assert SVC.exists(), f"CLI script {SVC} does not exist"

    def test_cli_is_executable(self):
        assert os.access(SVC, os.X_OK), (
            f"CLI script {SVC} must be executable (chmod +x)"
        )

    def test_cli_is_valid_python(self):
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", str(SVC)],
            capture_output=True, text=True
        )
        assert result.returncode == 0, (
            f"CLI script has syntax errors: {result.stderr}"
        )

    def test_cli_start_exit_zero(self):
        """CLI 'start' must exit 0 on success."""
        result = subprocess.run(
            [sys.executable, str(SVC), "start", "metricsaggd"],
            capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0, (
            f"'start' should exit 0, got {result.returncode}. stderr: {result.stderr}"
        )
        assert "started" in result.stdout.lower(), (
            f"'start' stdout should mention 'started', got: {result.stdout!r}"
        )

    def test_cli_stop_exit_zero(self):
        """CLI 'stop' must exit 0 on success."""
        subprocess.run(
            [sys.executable, str(SVC), "start", "metricsaggd"],
            capture_output=True, text=True, timeout=10
        )
        result = subprocess.run(
            [sys.executable, str(SVC), "stop", "metricsaggd"],
            capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0, (
            f"'stop' should exit 0, got {result.returncode}. stderr: {result.stderr}"
        )

    def test_cli_status_active_returns_zero(self):
        """CLI 'status' must exit 0 when service is active."""
        subprocess.run(
            [sys.executable, str(SVC), "start", "metricsaggd"],
            capture_output=True, text=True, timeout=10
        )
        result = subprocess.run(
            [sys.executable, str(SVC), "status", "metricsaggd"],
            capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0, (
            f"'status' should exit 0 when active, got {result.returncode}. "
            f"stdout: {result.stdout!r}"
        )
        assert "active" in result.stdout.lower(), (
            f"'status' stdout should mention 'active', got: {result.stdout!r}"
        )

    def test_cli_status_inactive_returns_three(self):
        """CLI 'status' must exit 3 when service is inactive."""
        result = subprocess.run(
            [sys.executable, str(SVC), "status", "metricsaggd"],
            capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 3, (
            f"'status' should exit 3 when inactive, got {result.returncode}"
        )
        assert "inactive" in result.stdout.lower(), (
            f"'status' stdout should mention 'inactive', got: {result.stdout!r}"
        )

    def test_cli_is_active_returns_zero_when_active(self):
        """CLI 'is-active' must exit 0 when service is active."""
        subprocess.run(
            [sys.executable, str(SVC), "start", "metricsaggd"],
            capture_output=True, text=True, timeout=10
        )
        result = subprocess.run(
            [sys.executable, str(SVC), "is-active", "metricsaggd"],
            capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0, (
            f"'is-active' should exit 0 when active, got {result.returncode}"
        )

    def test_cli_is_active_returns_three_when_inactive(self):
        """CLI 'is-active' must exit 3 when service is inactive."""
        result = subprocess.run(
            [sys.executable, str(SVC), "is-active", "metricsaggd"],
            capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 3, (
            f"'is-active' should exit 3 when inactive, got {result.returncode}"
        )

    def test_cli_enable_creates_and_persists_to_enabled_json(self):
        """CLI 'enable' must create enabled.json (as []) and add the service."""
        if ENABLED_JSON.exists():
            ENABLED_JSON.unlink()
        result = subprocess.run(
            [sys.executable, str(SVC), "enable", "metricsaggd"],
            capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0, (
            f"'enable' should exit 0, got {result.returncode}. stderr: {result.stderr}"
        )
        assert ENABLED_JSON.exists(), (
            f"enabled.json was not created at {ENABLED_JSON}"
        )
        data = json.loads(ENABLED_JSON.read_text())
        assert isinstance(data, list), (
            f"enabled.json should be a JSON list, got: {type(data).__name__}"
        )
        assert "metricsaggd" in data, (
            f"enabled.json should contain 'metricsaggd', got: {data!r}"
        )

    def test_cli_disable_removes_from_enabled_json(self):
        """CLI 'disable' must remove service from enabled.json."""
        subprocess.run(
            [sys.executable, str(SVC), "enable", "metricsaggd"],
            capture_output=True, text=True, timeout=10
        )
        result = subprocess.run(
            [sys.executable, str(SVC), "disable", "metricsaggd"],
            capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0, (
            f"'disable' should exit 0, got {result.returncode}. stderr: {result.stderr}"
        )
        if ENABLED_JSON.exists():
            data = json.loads(ENABLED_JSON.read_text())
            assert "metricsaggd" not in data, (
                f"enabled.json should not contain 'metricsaggd' after disable, got: {data!r}"
            )

    def test_cli_is_enabled_returns_zero_when_enabled(self):
        """CLI 'is-enabled' must exit 0 when service is enabled."""
        subprocess.run(
            [sys.executable, str(SVC), "enable", "metricsaggd"],
            capture_output=True, text=True, timeout=10
        )
        result = subprocess.run(
            [sys.executable, str(SVC), "is-enabled", "metricsaggd"],
            capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0, (
            f"'is-enabled' should exit 0 when enabled, got {result.returncode}"
        )

    def test_cli_is_enabled_returns_one_when_disabled(self):
        """CLI 'is-enabled' must exit 1 when service is disabled."""
        if ENABLED_JSON.exists():
            ENABLED_JSON.unlink()
        result = subprocess.run(
            [sys.executable, str(SVC), "is-enabled", "metricsaggd"],
            capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 1, (
            f"'is-enabled' should exit 1 when disabled, got {result.returncode}"
        )

    def test_cli_list_prints_enabled_services(self):
        """CLI 'list' must print tab-separated <service>\t<state> lines for enabled services."""
        subprocess.run(
            [sys.executable, str(SVC), "enable", "metricsaggd"],
            capture_output=True, text=True, timeout=10
        )
        result = subprocess.run(
            [sys.executable, str(SVC), "list"],
            capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0, (
            f"'list' should exit 0, got {result.returncode}. stderr: {result.stderr}"
        )
        lines = [l for l in result.stdout.splitlines() if l.strip()]
        assert len(lines) >= 1, (
            f"'list' should print at least one line, got: {result.stdout!r}"
        )
        found = False
        for line in lines:
            if line.startswith("metricsaggd\t"):
                found = True
                parts = line.split("\t")
                assert len(parts) == 2, (
                    f"'list' line should have 2 tab-separated parts, got: {line!r}"
                )
                assert parts[1] in ("active", "inactive"), (
                    f"'list' state should be 'active' or 'inactive', got: {parts[1]!r}"
                )
        assert found, (
            f"'list' output should contain 'metricsaggd\\t<state>' line, "
            f"got: {result.stdout!r}"
        )


# ---------------------------------------------------------------------------
# Init script tests
# ---------------------------------------------------------------------------
class TestInitScript:
    """Verify the SysVinit init script."""

    def test_init_script_exists(self):
        assert INIT_SCRIPT.exists(), f"Init script {INIT_SCRIPT} does not exist"

    def test_init_script_is_executable(self):
        assert os.access(INIT_SCRIPT, os.X_OK), (
            f"Init script {INIT_SCRIPT} must be executable (chmod +x)"
        )

    def test_init_script_has_lsb_header(self):
        content = INIT_SCRIPT.read_text()
        assert "### BEGIN INIT INFO" in content, (
            "Init script missing '### BEGIN INIT INFO' marker"
        )
        assert "### END INIT INFO" in content, (
            "Init script missing '### END INIT INFO' marker"
        )
        begin = content.index("### BEGIN INIT INFO")
        end = content.index("### END INIT INFO")
        header = content[begin:end]
        required_fields = [
            "# Provides:",
            "metricsaggd",
            "# Required-Start:",
            "# Default-Start:",
            "# Default-Stop:",
            "# Description:",
        ]
        for field in required_fields:
            assert field in header, (
                f"LSB header missing required field: {field!r}"
            )

    def test_init_script_status_inactive_returns_three(self):
        """Init script 'status' must exit 3 when service is inactive."""
        result = subprocess.run(
            [str(INIT_SCRIPT), "status"],
            capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 3, (
            f"Init 'status' should exit 3 when inactive, got {result.returncode}. "
            f"stdout: {result.stdout!r}"
        )
        assert "inactive" in result.stdout.lower(), (
            f"Init 'status' stdout should mention 'inactive', got: {result.stdout!r}"
        )

    def test_init_script_status_active_returns_zero(self):
        """Init script 'status' must exit 0 when service is active."""
        proc = subprocess.Popen(
            [sys.executable, str(DAEMON), "--config", str(DAEMON_CONF)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            start_new_session=True
        )
        try:
            pid = _wait_for_pid_file(timeout=3.0)
            assert pid is not None, "PID file was not created"

            result = subprocess.run(
                [str(INIT_SCRIPT), "status"],
                capture_output=True, text=True, timeout=10
            )
            assert result.returncode == 0, (
                f"Init 'status' should exit 0 when active, got {result.returncode}. "
                f"stdout: {result.stdout!r}"
            )
            assert "active" in result.stdout.lower(), (
                f"Init 'status' stdout should mention 'active', got: {result.stdout!r}"
            )
        finally:
            _terminate_proc(proc)


# ---------------------------------------------------------------------------
# systemd unit tests
# ---------------------------------------------------------------------------
class TestSystemdUnit:
    """Verify the systemd unit file."""

    def test_systemd_unit_exists(self):
        assert SYSTEMD_UNIT.exists(), (
            f"systemd unit {SYSTEMD_UNIT} does not exist"
        )

    def test_systemd_unit_parses_as_ini(self):
        config = configparser.ConfigParser()
        config.read(SYSTEMD_UNIT)
        assert len(config.sections()) > 0, (
            f"systemd unit file {SYSTEMD_UNIT} does not parse as INI with sections"
        )

    def test_systemd_unit_has_required_sections(self):
        config = configparser.ConfigParser()
        config.read(SYSTEMD_UNIT)
        for section in ("Unit", "Service", "Install"):
            assert config.has_section(section), (
                f"systemd unit missing [{section}] section"
            )

    def test_systemd_unit_execstart_references_daemon_and_config(self):
        config = configparser.ConfigParser()
        config.read(SYSTEMD_UNIT)
        execstart = config.get("Service", "ExecStart", fallback="")
        assert "metricsaggd.py" in execstart, (
            f"ExecStart should reference metricsaggd.py, got: {execstart!r}"
        )
        assert "/home/user/etc/metricsaggd.conf" in execstart, (
            f"ExecStart should reference config path, got: {execstart!r}"
        )

    def test_systemd_unit_pidfile(self):
        config = configparser.ConfigParser()
        config.read(SYSTEMD_UNIT)
        pidfile = config.get("Service", "PIDFile", fallback="")
        assert pidfile == "/home/user/var/metricsaggd.pid", (
            f"PIDFile should be /home/user/var/metricsaggd.pid, got: {pidfile!r}"
        )

    def test_systemd_unit_restart(self):
        config = configparser.ConfigParser()
        config.read(SYSTEMD_UNIT)
        restart = config.get("Service", "Restart", fallback="")
        assert restart == "on-failure", (
            f"Restart should be 'on-failure', got: {restart!r}"
        )

    def test_systemd_unit_execreload(self):
        config = configparser.ConfigParser()
        config.read(SYSTEMD_UNIT)
        execreload = config.get("Service", "ExecReload", fallback="")
        assert "HUP" in execreload, (
            f"ExecReload should contain 'HUP', got: {execreload!r}"
        )

    def test_systemd_unit_wantedby(self):
        config = configparser.ConfigParser()
        config.read(SYSTEMD_UNIT)
        wantedby = config.get("Install", "WantedBy", fallback="")
        assert wantedby == "multi-user.target", (
            f"WantedBy should be 'multi-user.target', got: {wantedby!r}"
        )


# ---------------------------------------------------------------------------
# Runlevel symlink tests
# ---------------------------------------------------------------------------
class TestRunlevelSymlinks:
    """Verify the runlevel symlinks."""

    def test_s_start_symlink_exists(self):
        assert RC_S_START.is_symlink() or RC_S_START.exists(), (
            f"Symlink {RC_S_START} does not exist"
        )

    def test_k_stop_symlink_exists(self):
        assert RC_K_STOP.is_symlink() or RC_K_STOP.exists(), (
            f"Symlink {RC_K_STOP} does not exist"
        )

    def test_s_start_is_symlink(self):
        assert os.path.islink(RC_S_START), (
            f"{RC_S_START} is not a symlink"
        )

    def test_k_stop_is_symlink(self):
        assert os.path.islink(RC_K_STOP), (
            f"{RC_K_STOP} is not a symlink"
        )

    def test_s_start_target(self):
        target = os.readlink(RC_S_START)
        assert target == "../init.d/metricsaggd", (
            f"{RC_S_START} should point to '../init.d/metricsaggd', got: {target!r}"
        )

    def test_k_stop_target(self):
        target = os.readlink(RC_K_STOP)
        assert target == "../init.d/metricsaggd", (
            f"{RC_K_STOP} should point to '../init.d/metricsaggd', got: {target!r}"
        )


# ---------------------------------------------------------------------------
# Configuration file tests
# ---------------------------------------------------------------------------
class TestConfigFiles:
    """Verify the configuration files."""

    def test_daemon_conf_exists(self):
        assert DAEMON_CONF.exists(), (
            f"Daemon config {DAEMON_CONF} does not exist"
        )

    def test_daemon_conf_has_required_keys(self):
        content = DAEMON_CONF.read_text()
        keys = {}
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                keys[k.strip()] = v.strip()
        for required in ("log_path", "pid_file", "tick_interval"):
            assert required in keys, (
                f"Daemon config missing required key: {required!r}"
            )
        assert keys["log_path"] == "/home/user/var/metricsaggd.log", (
            f"log_path should be /home/user/var/metricsaggd.log, "
            f"got: {keys.get('log_path')!r}"
        )
        assert keys["pid_file"] == "/home/user/var/metricsaggd.pid", (
            f"pid_file should be /home/user/var/metricsaggd.pid, "
            f"got: {keys.get('pid_file')!r}"
        )
        assert keys["tick_interval"] == "1", (
            f"tick_interval should be '1', got: {keys.get('tick_interval')!r}"
        )

    def test_services_conf_exists(self):
        assert SERVICES_CONF.exists(), (
            f"Services config {SERVICES_CONF} does not exist"
        )

    def test_services_conf_has_metricsaggd_section(self):
        config = configparser.ConfigParser()
        config.read(SERVICES_CONF)
        assert config.has_section("metricsaggd"), (
            f"Services config missing [metricsaggd] section"
        )
        for key in ("executable", "config", "pid_file"):
            assert config.has_option("metricsaggd", key), (
                f"Services config [metricsaggd] missing required option: {key!r}"
            )
