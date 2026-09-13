"""
test_final_state.py

Comprehensive pytest suite validating the FINAL state of the logshipperd
implementation after the student has completed the task.

Validates:
- File structure (existence, permissions, directories)
- Configuration files (daemon config, services config)
- systemd unit file (INI format, required sections/keys)
- Daemon runtime behavior (PID file, logging, shipping, signals)
- CLI behavior (start, stop, status, enable, disable, is-active, is-enabled, list)
"""
import configparser
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

# ============================================================================
# Absolute paths (as required)
# ============================================================================
HOME = Path("/home/user")
DAEMON = HOME / "logshipperd.py"
SVCCTL = HOME / "svcctl.py"
SYSTEMD_UNIT = HOME / "systemd" / "logshipper.service"
DAEMON_CONFIG = HOME / "etc" / "logshipper.conf"
SERVICES_CONFIG = HOME / "etc" / "services.conf"
PID_FILE = HOME / "var" / "logshipperd.pid"
LOG_FILE = HOME / "var" / "logshipperd.log"
ENABLED_FILE = HOME / "var" / "enabled.json"
SPOOL_INCOMING = HOME / "spool" / "incoming"
SPOOL_SHIPPED = HOME / "spool" / "shipped"
VAR_DIR = HOME / "var"
ETC_DIR = HOME / "etc"
SYSTEMD_DIR = HOME / "systemd"


# ============================================================================
# Helpers
# ============================================================================
def _kill_daemon():
    """Kill any running daemon and clean up state files."""
    if PID_FILE.exists():
        try:
            pid = int(PID_FILE.read_text().strip())
            os.kill(pid, signal.SIGTERM)
        except (ProcessLookupError, ValueError, PermissionError, OSError):
            pass
        time.sleep(0.3)
    for f in (PID_FILE, LOG_FILE, ENABLED_FILE):
        if f.exists() and f.is_file():
            try:
                f.unlink()
            except (IsADirectoryError, OSError):
                pass


def _wait_for(condition, timeout=5.0, interval=0.05):
    """Poll until condition() returns True or timeout expires."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if condition():
            return True
        time.sleep(interval)
    return condition()


@pytest.fixture(autouse=True)
def _isolate():
    """Ensure clean state before and after each test."""
    _kill_daemon()
    for d in (SPOOL_INCOMING, SPOOL_SHIPPED):
        if d.exists():
            for p in Path(d).iterdir():
                if p.is_file():
                    try:
                        p.unlink()
                    except OSError:
                        pass
    yield
    _kill_daemon()


# ============================================================================
# File Structure Tests
# ============================================================================
class TestFileStructure:
    """Verify all required files and directories exist with correct permissions."""

    def test_daemon_script_exists(self):
        assert DAEMON.exists(), f"Daemon script missing at {DAEMON}"
        assert DAEMON.is_file(), f"{DAEMON} is not a regular file"

    def test_daemon_script_executable(self):
        assert os.access(DAEMON, os.X_OK), (
            f"Daemon script at {DAEMON} is not executable "
            "(chmod +x required)"
        )

    def test_svcctl_script_exists(self):
        assert SVCCTL.exists(), f"svcctl script missing at {SVCCTL}"
        assert SVCCTL.is_file(), f"{SVCCTL} is not a regular file"

    def test_svcctl_script_executable(self):
        assert os.access(SVCCTL, os.X_OK), (
            f"svcctl script at {SVCCTL} is not executable "
            "(chmod +x required)"
        )

    def test_systemd_unit_exists(self):
        assert SYSTEMD_UNIT.exists(), (
            f"systemd unit missing at {SYSTEMD_UNIT}"
        )
        assert SYSTEMD_UNIT.is_file(), (
            f"{SYSTEMD_UNIT} is not a regular file"
        )

    def test_daemon_config_exists(self):
        assert DAEMON_CONFIG.exists(), (
            f"Daemon config missing at {DAEMON_CONFIG}"
        )

    def test_services_config_exists(self):
        assert SERVICES_CONFIG.exists(), (
            f"Services config missing at {SERVICES_CONFIG}"
        )

    def test_var_dir_exists(self):
        assert VAR_DIR.exists() and VAR_DIR.is_dir(), (
            f"Directory {VAR_DIR} does not exist"
        )

    def test_etc_dir_exists(self):
        assert ETC_DIR.exists() and ETC_DIR.is_dir(), (
            f"Directory {ETC_DIR} does not exist"
        )

    def test_spool_incoming_exists(self):
        assert SPOOL_INCOMING.exists() and SPOOL_INCOMING.is_dir(), (
            f"Directory {SPOOL_INCOMING} does not exist"
        )

    def test_spool_shipped_exists(self):
        assert SPOOL_SHIPPED.exists() and SPOOL_SHIPPED.is_dir(), (
            f"Directory {SPOOL_SHIPPED} does not exist"
        )

    def test_systemd_dir_exists(self):
        assert SYSTEMD_DIR.exists() and SYSTEMD_DIR.is_dir(), (
            f"Directory {SYSTEMD_DIR} does not exist"
        )


# ============================================================================
# Configuration File Tests
# ============================================================================
class TestDaemonConfig:
    """Verify the daemon configuration file has correct content."""

    def test_config_has_source_dir(self):
        content = DAEMON_CONFIG.read_text()
        assert "source_dir=/home/user/spool/incoming" in content, (
            f"source_dir not set correctly in {DAEMON_CONFIG}: {content!r}"
        )

    def test_config_has_dest_dir(self):
        content = DAEMON_CONFIG.read_text()
        assert "dest_dir=/home/user/spool/shipped" in content, (
            f"dest_dir not set correctly in {DAEMON_CONFIG}: {content!r}"
        )

    def test_config_has_poll_interval(self):
        content = DAEMON_CONFIG.read_text()
        assert "poll_interval=1" in content, (
            f"poll_interval not set correctly in {DAEMON_CONFIG}: {content!r}"
        )


class TestServicesConfig:
    """Verify the services configuration file has correct content."""

    def test_services_config_parses(self):
        parser = configparser.ConfigParser()
        parser.read(str(SERVICES_CONFIG))
        assert parser.has_section("logshipperd"), (
            f"Missing [logshipperd] section in {SERVICES_CONFIG}"
        )

    def test_services_config_has_required_keys(self):
        parser = configparser.ConfigParser()
        parser.read(str(SERVICES_CONFIG))
        for key in ("executable", "config", "pid_file"):
            assert parser.has_option("logshipperd", key), (
                f"Missing '{key}' in [logshipperd] section of "
                f"{SERVICES_CONFIG}"
            )


# ============================================================================
# systemd Unit Tests
# ============================================================================
class TestSystemdUnit:
    """Verify the systemd unit file is correctly formatted."""

    def _parser(self):
        p = configparser.ConfigParser()
        p.read(str(SYSTEMD_UNIT))
        return p

    def test_unit_parses_as_ini(self):
        # Should not raise
        self._parser()

    def test_unit_has_unit_section(self):
        assert self._parser().has_section("Unit"), (
            "Missing [Unit] section in systemd unit file"
        )

    def test_unit_has_service_section(self):
        assert self._parser().has_section("Service"), (
            "Missing [Service] section in systemd unit file"
        )

    def test_unit_has_install_section(self):
        assert self._parser().has_section("Install"), (
            "Missing [Install] section in systemd unit file"
        )

    def test_execstart_references_daemon(self):
        exec_start = self._parser().get("Service", "ExecStart")
        assert "/home/user/logshipperd.py" in exec_start, (
            f"ExecStart does not reference daemon: {exec_start!r}"
        )

    def test_execstart_references_config(self):
        exec_start = self._parser().get("Service", "ExecStart")
        assert "/home/user/etc/logshipper.conf" in exec_start, (
            f"ExecStart does not reference config: {exec_start!r}"
        )

    def test_pidfile_correct(self):
        pid_file = self._parser().get("Service", "PIDFile")
        assert pid_file == "/home/user/var/logshipperd.pid", (
            f"PIDFile is {pid_file!r}, "
            f"expected '/home/user/var/logshipperd.pid'"
        )

    def test_restart_set(self):
        restart = self._parser().get("Service", "Restart")
        assert restart == "on-failure", (
            f"Restart is {restart!r}, expected 'on-failure'"
        )

    def test_wantedby_set(self):
        wanted_by = self._parser().get("Install", "WantedBy")
        assert wanted_by == "multi-user.target", (
            f"WantedBy is {wanted_by!r}, expected 'multi-user.target'"
        )

    def test_description_non_empty(self):
        description = self._parser().get("Unit", "Description")
        assert description.strip() != "", (
            f"Unit.Description is empty: {description!r}"
        )


# ============================================================================
# Daemon Behavior Tests
# ============================================================================
class TestDaemon:
    """Verify the daemon's runtime behavior."""

    def _start_daemon(self):
        """Start the daemon process."""
        return subprocess.Popen(
            [sys.executable, str(DAEMON), "--config", str(DAEMON_CONFIG)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

    def test_start_writes_pid_file(self):
        """Daemon must write PID file on startup within 3 seconds."""
        proc = self._start_daemon()
        try:
            assert _wait_for(lambda: PID_FILE.exists(), timeout=3.0), (
                f"PID file not created at {PID_FILE} within 3 seconds"
            )
            pid_text = PID_FILE.read_text().strip()
            assert pid_text.lstrip("-").isdigit(), (
                f"PID file content {pid_text!r} is not an integer"
            )
            pid = int(pid_text)
            assert pid > 0, f"PID {pid} is not positive"
        finally:
            _kill_daemon()

    def test_start_logs_start_event(self):
        """Daemon must log START event with PID on startup."""
        proc = self._start_daemon()
        try:
            assert _wait_for(lambda: LOG_FILE.exists(), timeout=3.0), (
                f"Log file not created at {LOG_FILE} within 3 seconds"
            )
            assert _wait_for(lambda: PID_FILE.exists(), timeout=3.0), (
                "PID file not created within 3 seconds"
            )
            log_content = LOG_FILE.read_text()
            assert "START" in log_content, (
                f"START event not found in log: {log_content!r}"
            )
            pid_text = PID_FILE.read_text().strip()
            assert pid_text in log_content, (
                f"PID {pid_text!r} not found in log: {log_content!r}"
            )
        finally:
            _kill_daemon()

    def test_ships_new_file(self):
        """Daemon must copy .log files to shipped dir with .shipped suffix."""
        proc = self._start_daemon()
        try:
            assert _wait_for(lambda: PID_FILE.exists(), timeout=3.0), (
                "Daemon did not start within 3 seconds"
            )

            test_content = b"test log content for shipping verification"
            incoming_file = SPOOL_INCOMING / "test_ship.log"
            incoming_file.write_bytes(test_content)

            shipped_file = SPOOL_SHIPPED / "test_ship.log.shipped"
            assert _wait_for(lambda: shipped_file.exists(), timeout=5.0), (
                f"File not shipped to {shipped_file} within 5 seconds"
            )
            assert shipped_file.read_bytes() == test_content, (
                "Shipped file content does not match original"
            )
        finally:
            _kill_daemon()

    def test_does_not_reship(self):
        """Daemon must not re-ship files that already have .shipped counterparts."""
        proc = self._start_daemon()
        try:
            assert _wait_for(lambda: PID_FILE.exists(), timeout=3.0), (
                "Daemon did not start within 3 seconds"
            )

            sentinel = b"ORIGINAL_SHIPPED_SENTINEL_BYTES_DO_NOT_OVERWRITE"
            (SPOOL_SHIPPED / "already.log.shipped").write_bytes(sentinel)
            (SPOOL_INCOMING / "already.log").write_bytes(
                b"NEW_INCOMING_CONTENT_DIFFERENT_FROM_SHIPPED"
            )

            # Wait for daemon to poll at least twice
            time.sleep(3.0)

            shipped_content = (
                SPOOL_SHIPPED / "already.log.shipped"
            ).read_bytes()
            assert shipped_content == sentinel, (
                f"Shipped file was overwritten. "
                f"Expected {sentinel!r}, got {shipped_content!r}"
            )
        finally:
            _kill_daemon()

    def test_sigterm_graceful_shutdown(self):
        """SIGTERM must cause clean shutdown with PID file removal."""
        proc = self._start_daemon()
        try:
            assert _wait_for(lambda: PID_FILE.exists(), timeout=3.0), (
                "Daemon did not start within 3 seconds"
            )

            pid = int(PID_FILE.read_text().strip())
            os.kill(pid, signal.SIGTERM)

            assert _wait_for(lambda: not PID_FILE.exists(), timeout=5.0), (
                "PID file not removed within 5 seconds after SIGTERM"
            )

            proc.wait(timeout=5.0)
            assert proc.returncode == 0, (
                f"Process exited with code {proc.returncode}, expected 0"
            )

            log_content = LOG_FILE.read_text()
            assert "STOP SIGTERM" in log_content, (
                f"STOP SIGTERM not found in log: {log_content!r}"
            )
        finally:
            _kill_daemon()

    def test_sighup_reloads(self):
        """SIGHUP must trigger reload without killing the process."""
        proc = self._start_daemon()
        try:
            assert _wait_for(lambda: PID_FILE.exists(), timeout=3.0), (
                "Daemon did not start within 3 seconds"
            )

            pid_before = PID_FILE.read_text().strip()
            pid = int(pid_before)

            os.kill(pid, signal.SIGHUP)
            time.sleep(1.0)  # Give daemon time to handle signal

            assert PID_FILE.exists(), (
                "PID file was removed after SIGHUP (should remain)"
            )
            pid_after = PID_FILE.read_text().strip()
            assert pid_before == pid_after, (
                f"PID changed after SIGHUP: "
                f"{pid_before!r} -> {pid_after!r}"
            )

            assert proc.poll() is None, (
                f"Process died after SIGHUP with code {proc.returncode}"
            )

            log_content = LOG_FILE.read_text()
            assert "RELOAD" in log_content, (
                f"RELOAD not found in log: {log_content!r}"
            )
        finally:
            _kill_daemon()


# ============================================================================
# CLI Behavior Tests
# ============================================================================
class TestSvcctl:
    """Verify the service control CLI behavior and LSB exit codes."""

    def _run_cli(self, *args, timeout=10.0):
        """Run svcctl with given arguments."""
        return subprocess.run(
            [sys.executable, str(SVCCTL), *args],
            capture_output=True,
            text=True,
            timeout=timeout,
        )

    def test_start_exits_zero(self):
        """svcctl start must exit 0 and create PID file."""
        result = self._run_cli("start", "logshipperd")
        assert result.returncode == 0, (
            f"start exited with {result.returncode}. "
            f"stderr: {result.stderr!r}"
        )
        assert _wait_for(lambda: PID_FILE.exists(), timeout=3.0), (
            "PID file not created after start command"
        )
        assert "started" in result.stdout.lower(), (
            f"stdout does not contain 'started': {result.stdout!r}"
        )

    def test_stop_exits_zero(self):
        """svcctl stop must exit 0 and remove PID file."""
        # First start the service
        self._run_cli("start", "logshipperd")
        assert _wait_for(lambda: PID_FILE.exists(), timeout=3.0), (
            "Service did not start"
        )

        result = self._run_cli("stop", "logshipperd")
        assert result.returncode == 0, (
            f"stop exited with {result.returncode}. "
            f"stderr: {result.stderr!r}"
        )
        assert "stopped" in result.stdout.lower(), (
            f"stdout does not contain 'stopped': {result.stdout!r}"
        )
        assert _wait_for(lambda: not PID_FILE.exists(), timeout=5.0), (
            "PID file not removed after stop command"
        )

    def test_status_active(self):
        """svcctl status must return 0 and print 'active' when running."""
        self._run_cli("start", "logshipperd")
        assert _wait_for(lambda: PID_FILE.exists(), timeout=3.0), (
            "Service did not start"
        )

        result = self._run_cli("status", "logshipperd")
        assert result.returncode == 0, (
            f"status exited with {result.returncode} when active, "
            f"expected 0. stderr: {result.stderr!r}"
        )
        assert "active" in result.stdout.lower(), (
            f"stdout does not contain 'active': {result.stdout!r}"
        )

    def test_status_inactive(self):
        """svcctl status must return 3 and print 'inactive' when stopped."""
        _kill_daemon()
        assert not PID_FILE.exists(), (
            "PID file should not exist before status check"
        )

        result = self._run_cli("status", "logshipperd")
        assert result.returncode == 3, (
            f"status exited with {result.returncode} when inactive, "
            f"expected 3. stderr: {result.stderr!r}"
        )
        assert "inactive" in result.stdout.lower(), (
            f"stdout does not contain 'inactive': {result.stdout!r}"
        )

    def test_is_active_codes(self):
        """svcctl is-active must return 0 when active, 3 when inactive."""
        # When inactive
        _kill_daemon()
        result = self._run_cli("is-active", "logshipperd")
        assert result.returncode == 3, (
            f"is-active exited with {result.returncode} when inactive, "
            f"expected 3. stderr: {result.stderr!r}"
        )

        # When active
        self._run_cli("start", "logshipperd")
        assert _wait_for(lambda: PID_FILE.exists(), timeout=3.0), (
            "Service did not start"
        )

        result = self._run_cli("is-active", "logshipperd")
        assert result.returncode == 0, (
            f"is-active exited with {result.returncode} when active, "
            f"expected 0. stderr: {result.stderr!r}"
        )

    def test_enable_persists(self):
        """svcctl enable must add service to enabled.json."""
        # Clean up first
        if ENABLED_FILE.exists():
            ENABLED_FILE.unlink()

        result = self._run_cli("enable", "logshipperd")
        assert result.returncode == 0, (
            f"enable exited with {result.returncode}. "
            f"stderr: {result.stderr!r}"
        )
        assert "enabled" in result.stdout.lower(), (
            f"stdout does not contain 'enabled': {result.stdout!r}"
        )

        assert ENABLED_FILE.exists(), (
            "enabled.json was not created by enable command"
        )
        data = json.loads(ENABLED_FILE.read_text())
        assert "logshipperd" in data, (
            f"logshipperd not in enabled.json: {data}"
        )

    def test_disable_removes(self):
        """svcctl disable must remove service from enabled.json."""
        # First enable
        self._run_cli("enable", "logshipperd")
        assert ENABLED_FILE.exists(), (
            "enabled.json should exist after enable"
        )

        result = self._run_cli("disable", "logshipperd")
        assert result.returncode == 0, (
            f"disable exited with {result.returncode}. "
            f"stderr: {result.stderr!r}"
        )
        assert "disabled" in result.stdout.lower(), (
            f"stdout does not contain 'disabled': {result.stdout!r}"
        )

        if ENABLED_FILE.exists():
            data = json.loads(ENABLED_FILE.read_text())
            assert "logshipperd" not in data, (
                f"logshipperd still in enabled.json after disable: {data}"
            )

    def test_is_enabled_codes(self):
        """svcctl is-enabled must return 0 when enabled, 1 when disabled."""
        # Clean up first
        if ENABLED_FILE.exists():
            ENABLED_FILE.unlink()

        # When disabled
        result = self._run_cli("is-enabled", "logshipperd")
        assert result.returncode == 1, (
            f"is-enabled exited with {result.returncode} when disabled, "
            f"expected 1. stderr: {result.stderr!r}"
        )

        # When enabled
        self._run_cli("enable", "logshipperd")
        result = self._run_cli("is-enabled", "logshipperd")
        assert result.returncode == 0, (
            f"is-enabled exited with {result.returncode} when enabled, "
            f"expected 0. stderr: {result.stderr!r}"
        )

    def test_list_format(self):
        """svcctl list must print enabled services with tab-separated state."""
        # Enable the service
        self._run_cli("enable", "logshipperd")

        result = self._run_cli("list")
        assert result.returncode == 0, (
            f"list exited with {result.returncode}. "
            f"stderr: {result.stderr!r}"
        )

        lines = [l for l in result.stdout.strip().split("\n") if l.strip()]
        assert len(lines) > 0, (
            f"list produced no output. stdout: {result.stdout!r}"
        )

        # Check that logshipperd is listed with tab-separated state
        found = False
        for line in lines:
            parts = line.split("\t")
            if len(parts) >= 2 and parts[0] == "logshipperd":
                state = parts[1].strip()
                assert state in ("active", "inactive"), (
                    f"Invalid state {state!r} in list output line: "
                    f"{line!r}"
                )
                found = True
                break

        assert found, (
            f"logshipperd not found in tab-separated list output: "
            f"{result.stdout!r}"
        )

    def test_restart_propagates(self):
        """svcctl restart must stop then start the service."""
        # First start
        start_result = self._run_cli("start", "logshipperd")
        assert start_result.returncode == 0, (
            f"initial start failed: {start_result.stderr!r}"
        )
        assert _wait_for(lambda: PID_FILE.exists(), timeout=3.0), (
            "Service did not start initially"
        )

        result = self._run_cli("restart", "logshipperd")
        assert result.returncode == 0, (
            f"restart exited with {result.returncode}. "
            f"stderr: {result.stderr!r}"
        )
        assert _wait_for(lambda: PID_FILE.exists(), timeout=5.0), (
            "Service did not restart (PID file missing after restart)"
        )
