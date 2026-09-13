You are a system administrator at CloudMetrics Inc. The platform team has approved the deployment of a new internal service called `metricsaggd` — a metrics aggregator daemon. Your job is to deploy it as a properly managed Linux service. The deployment includes a Python daemon, a service control CLI, a SysVinit-style init script with runlevel symlinks, a systemd unit file, and configuration files. After you finish, the automated test suite already present under `/home/user/tests/` will verify every aspect of your implementation.

## Context

`metricsaggd` is a Python daemon that periodically writes a synthetic "metrics tick" entry to its log file. The service must follow proper Linux daemon conventions:

- PID file management under `/home/user/var/`
- Clean signal handling (`SIGTERM` → graceful shutdown, `SIGHUP` → config reload)
- Structured lifecycle event logging
- LSB-compliant exit codes from the control CLI (0 = success/active/enabled, 3 = inactive, 1 = not-enabled/failure)
- A standard SysVinit init script with LSB header
- Runlevel symlinks for SysVinit boot integration
- A standard systemd unit file

All deliverables live under `/home/user/`. Standard Python 3 library only — no third-party packages needed.

## Component 1: The Daemon — `/home/user/metricsaggd.py`

**Invocation**: `python3 /home/user/metricsaggd.py [--config PATH]` (default config path: `/home/user/etc/metricsaggd.conf`).

**Configuration** (`/home/user/etc/metricsaggd.conf`) — key=value lines, `#` for comments:
```
log_path=/home/user/var/metricsaggd.log
pid_file=/home/user/var/metricsaggd.pid
tick_interval=1
```

**On startup**, the daemon must:
1. Parse `--config` (use `argparse`) and read `log_path`, `pid_file`, `tick_interval` from the file.
2. Ensure the parent directory of `log_path` exists (`os.makedirs(..., exist_ok=True)`).
3. Write its current PID as an integer string to `pid_file`.
4. Append one line to `log_path` in the format `START <pid> <iso8601_timestamp>` (e.g., `START 12345 2024-01-15T10:30:00`).

**Main loop**: every `tick_interval` seconds, append one line `TICK <iso8601_timestamp>` to `log_path`. Use `time.sleep(tick_interval)` between ticks.

**Signal handling**:
- `SIGTERM` → append `STOP SIGTERM <iso8601_timestamp>` to `log_path`, remove `pid_file`, `sys.exit(0)`.
- `SIGHUP` → append `RELOAD <iso8601_timestamp>` to `log_path`, re-read the config file, continue looping.

**Timestamps**: use `datetime.now().isoformat(timespec='seconds')` (no timezone, e.g., `2024-01-15T10:30:00`).

## Component 2: Service Control CLI — `/home/user/svc.py`

**Invocation**: `python3 /home/user/svc.py <subcommand> [service_name]`. Default service name: `metricsaggd`.

Reads service definitions from `/home/user/etc/services.conf` (INI format). Each section must define `executable`, `config`, and `pid_file`.

**Subcommands and exact exit codes** (LSB-compliant):

| Subcommand | stdout | Exit |
|---|---|---|
| `start <svc>` | `<service> started (pid <pid>)` | 0 success, 1 failure |
| `stop <svc>` | `<service> stopped` | 0 success, 1 failure |
| `restart <svc>` | (stop then start) | propagates |
| `status <svc>` | `active (pid <pid>)` or `inactive (dead)` | 0 active / 3 inactive |
| `is-active <svc>` | (silent) | 0 active / 3 inactive |
| `is-enabled <svc>` | (silent) | 0 enabled / 1 disabled |
| `enable <svc>` | `<service> enabled` | 0 |
| `disable <svc>` | `<service> disabled` | 0 |
| `list` | `<service>\t<active\|inactive>` per enabled service | 0 |

**Implementation hints**:
- `start`: `subprocess.Popen([...], start_new_session=True, stdout=DEVNULL, stderr=DEVNULL)`; wait up to 3 seconds for the PID file to materialize.
- `stop`: read the PID file, `os.kill(pid, SIGTERM)`, wait up to 5 seconds for the PID file to disappear.
- A service is **active** iff its `pid_file` exists AND the PID is alive (use `os.kill(pid, 0)` inside try/except `ProcessLookupError`).
- `enable` adds the service name to `/home/user/var/enabled.json` (a JSON array of strings); create as `[]` if missing.
- `disable` removes the service name from that JSON array (idempotent — succeed even if not previously enabled).

## Component 3: SysVinit Init Script — `/home/user/init.d/metricsaggd`

Bash script with:
- LSB header delimited by `### BEGIN INIT INFO` and `### END INIT INFO` containing:
  - `# Provides: metricsaggd`
  - `# Required-Start: $local_fs`
  - `# Default-Start: 3 5`
  - `# Default-Stop: 0 1 6`
  - `# Short-Description: Metrics Aggregator`
  - `# Description: Aggregates internal metrics.`
- Functions: `start`, `stop`, `status`, `restart`; dispatch by `$1`.
- `start`: invokes `python3 /home/user/svc.py start metricsaggd`.
- `stop`: invokes `python3 /home/user/svc.py stop metricsaggd`.
- `status`: reads the PID file, checks liveness with `kill -0`, prints `active (pid <pid>)` and exits 0 if running; prints `inactive (dead)` and exits 3 if not.
- `restart`: calls `stop` then `start`.

## Component 4: Runlevel Symlinks — `/home/user/rc.d/`

Create two symlinks:
- `/home/user/rc.d/S99metricsaggd` → `../init.d/metricsaggd`
- `/home/user/rc.d/K01metricsaggd` → `../init.d/metricsaggd`

## Component 5: systemd Unit — `/home/user/systemd/metricsaggd.service`

Standard INI-format unit file:
```
[Unit]
Description=CloudMetrics Metrics Aggregator
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/user/metricsaggd.py --config /home/user/etc/metricsaggd.conf
PIDFile=/home/user/var/metricsaggd.pid
Restart=on-failure
ExecReload=/bin/kill -HUP $MAINPID

[Install]
WantedBy=multi-user.target
```

## Component 6: Configuration Files

`/home/user/etc/metricsaggd.conf`:
```
log_path=/home/user/var/metricsaggd.log
pid_file=/home/user/var/metricsaggd.pid
tick_interval=1
```

`/home/user/etc/services.conf`:
```ini
[metricsaggd]
executable=/home/user/metricsaggd.py
config=/home/user/etc/metricsaggd.conf
pid_file=/home/user/var/metricsaggd.pid
```

## Component 7: Runtime Directories

Ensure these exist: `/home/user/var/`, `/home/user/etc/`, `/home/user/init.d/`, `/home/user/rc.d/`, `/home/user/systemd/`, `/home/user/spool/`.

## Verification

The automated harness runs:
```
cd /home/user && python -m compileall . && python -m pytest -v
```

Tests under `/home/user/tests/` cover:
1. **Daemon**: PID file written on start; `START <pid>` logged; periodic `TICK` entries; `SIGTERM` clean shutdown with PID file removed and `STOP SIGTERM` logged; `SIGHUP` produces `RELOAD` log without killing the process.
2. **CLI**: `start`/`stop` exit 0; `status`/`is-active` return 0 active / 3 inactive; `enable`/`disable` persist into `enabled.json`; `is-enabled` returns 0 enabled / 1 disabled; `list` prints enabled services with tab-separated state.
3. **Init script**: `/home/user/init.d/metricsaggd status` returns 0 when active, 3 when inactive; LSB header has all required fields; file is executable.
4. **systemd unit**: file exists; parses as INI; `[Unit]`/`[Service]`/`[Install]` sections; `ExecStart` references daemon and config; `PIDFile`, `Restart`, `ExecReload`, `WantedBy` all present.
5. **Runlevel symlinks**: `/home/user/rc.d/S99metricsaggd` and `/home/user/rc.d/K01metricsaggd` both symlink to `../init.d/metricsaggd`.

## Constraints

- Standard library only — no `pip install` required.
- All Python scripts and the init script must be executable (`chmod +x`).
- Do not modify anything under `/home/user/tests/`.
- PID file must contain only the PID as an integer string (trailing newline allowed).
- Timestamps: `datetime.now().isoformat(timespec='seconds')`.
- Exit codes: 0 = success/active/enabled; 3 = inactive; 1 = not-enabled/generic-failure.
- Do not background daemons manually (no `nohup`, no `&`); tests spawn processes via `subprocess.Popen`.
