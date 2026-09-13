You are a senior infrastructure engineer at CloudMetrics Inc. The platform team has approved deployment of an internal log shipping service called `logshipperd`. Your responsibility is to build the daemon itself, a Python service-control CLI to manage its lifecycle, and integrate the service with systemd. After you finish, an automated test suite will verify every aspect of your implementation.

## Context

`logshipperd` is a Python daemon that monitors a "spool" directory for newly-arrived `.log` files. When a file appears, the daemon copies it to a "shipped" directory with `.shipped` appended to the filename — a deterministic simulation of real log shipping. The service must follow proper Linux daemon conventions:

- PID file management under `/home/user/var/`
- Clean signal handling (`SIGTERM` for graceful shutdown, `SIGHUP` for config reload)
- Structured lifecycle event logging
- LSB-compliant exit codes from the control CLI (0 = success/active/enabled, 3 = inactive, 1 = not-enabled)

All deliverables live under `/home/user/`. The project is pure Python 3 standard library — no third-party packages are required.

## Component 1: The Daemon — `/home/user/logshipperd.py`

**Invocation**: `python3 /home/user/logshipperd.py [--config PATH]` (default config path: `/home/user/etc/logshipper.conf`).

**Configuration file** (`/home/user/etc/logshipper.conf`) — key=value lines, one per line, `#` for comments:
```
source_dir=/home/user/spool/incoming
dest_dir=/home/user/spool/shipped
poll_interval=1
```

**On startup**, the daemon must:
1. Parse `--config` and read `source_dir`, `dest_dir`, `poll_interval`.
2. Ensure `source_dir` and `dest_dir` exist (`os.makedirs(..., exist_ok=True)`).
3. Write its current PID as an integer string to `/home/user/var/logshipperd.pid`.
4. Append one line to `/home/user/var/logshipperd.log` in this exact format: `START <pid> <iso8601_timestamp>` (e.g., `START 12345 2024-01-15T10:30:00`).

**Main loop**:
- Poll `source_dir` every `poll_interval` seconds (use `time.sleep`).
- For each file ending in `.log` whose basename does NOT already have a `<filename>.shipped` counterpart in `dest_dir`, copy it to `dest_dir` with `.shipped` appended, then append `SHIP <filename> <iso8601_timestamp>` to the daemon log.
- Track shipped basenames in memory so a file is never re-shipped within a single run.

**Signal handling**:
- `SIGTERM` → append `STOP SIGTERM <iso8601_timestamp>`, remove the PID file, `sys.exit(0)`.
- `SIGHUP` → append `RELOAD <iso8601_timestamp>`, re-read the config file in place (without exiting), continue polling.

**Timestamps**: use `datetime.now().isoformat(timespec='seconds')` (no timezone, e.g., `2024-01-15T10:30:00`).

## Component 2: The Control CLI — `/home/user/svcctl.py`

**Invocation**: `python3 /home/user/svcctl.py <subcommand> <service_name>`.

The CLI reads service definitions from `/home/user/etc/services.conf` (INI format; see Component 4). Each section must at minimum define `executable`, `config`, and `pid_file`. The default service is `logshipperd`.

**Subcommands and exact exit codes**:

| Subcommand | Output on stdout | Exit code |
|---|---|---|
| `start <svc>` | `<service> started (pid <pid>)` | 0 success, 1 failure |
| `stop <svc>` | `<service> stopped` | 0 success, 1 failure |
| `restart <svc>` | equivalent to `stop` then `start` | propagates |
| `status <svc>` | `active (pid <pid>)` or `inactive (dead)` | 0 if active, 3 if inactive |
| `enable <svc>` | `<service> enabled` | 0 |
| `disable <svc>` | `<service> disabled` | 0 |
| `is-active <svc>` | (no output) | 0 if active, 3 if inactive |
| `is-enabled <svc>` | (no output) | 0 if enabled, 1 if disabled |
| `list` | one line per enabled service: `<service>\t<active\|inactive>` | 0 |

**Implementation hints**:
- `start` must use `subprocess.Popen([...], start_new_session=True, stdout=DEVNULL, stderr=DEVNULL)` and wait up to 3 seconds for the PID file to materialize before returning.
- `stop` must read the PID file, send SIGTERM, and wait up to 5 seconds for the process to exit and the PID file to disappear.
- A service is **active** iff its `pid_file` exists and the PID inside corresponds to a live process (use `os.kill(pid, 0)` inside a try/except `ProcessLookupError`).
- `enable` adds the service name to `/home/user/var/enabled.json` (a JSON array of strings); create the file if missing.
- `disable` removes the service name from that JSON array (write back the modified array).

## Component 3: The systemd Unit — `/home/user/systemd/logshipper.service`

A standard INI-format unit file containing:

```
[Unit]
Description=CloudMetrics Log Shipper
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/user/logshipperd.py --config /home/user/etc/logshipper.conf
PIDFile=/home/user/var/logshipperd.pid
Restart=on-failure
ExecReload=/bin/kill -HUP $MAINPID

[Install]
WantedBy=multi-user.target
```

## Component 4: Configuration Files

Create both with the contents shown below.

`/home/user/etc/logshipper.conf`:
```
source_dir=/home/user/spool/incoming
dest_dir=/home/user/spool/shipped
poll_interval=1
```

`/home/user/etc/services.conf`:
```ini
[logshipperd]
executable=/home/user/logshipperd.py
config=/home/user/etc/logshipper.conf
pid_file=/home/user/var/logshipperd.pid
```

## Component 5: Runtime Directories

Create these if missing: `/home/user/var/`, `/home/user/etc/`, `/home/user/spool/incoming/`, `/home/user/spool/shipped/`, `/home/user/systemd/`.

## Verification

The grading harness runs:
```
cd /home/user && python -m compileall . && python -m pytest -v
```

The pytest suite under `/home/user/tests/` covers:

1. **Daemon** (`test_daemon.py`): PID file written on start, `START <pid>` logged, dropped `.log` files appear as `.log.shipped` in the shipped dir, shipped files are not re-shipped, `SIGTERM` produces clean shutdown with PID file removed and `STOP SIGTERM` logged, `SIGHUP` produces `RELOAD` log entry without killing the process.

2. **CLI** (`test_svcctl.py`): `start`/`stop` exit 0, `status`/`is-active` return exit 0 active and exit 3 inactive, `enable`/`disable` persist correctly into `enabled.json`, `is-enabled` returns exit 0 enabled and exit 1 disabled, `list` prints enabled services.

3. **systemd unit** (`test_systemd.py`): file exists at the expected path, parses as INI, contains `[Unit]`/`[Service]`/`[Install]` sections, `ExecStart` references the daemon and the correct config path, `PIDFile`, `Restart`, `WantedBy` are all present.

## Constraints

- Standard library only — no `pip install` required.
- All Python scripts must be executable (`chmod +x`).
- Do not modify anything under `/home/user/tests/`.
- The PID file must contain only the PID as an integer string (trailing newline is fine).
- Timestamps: `datetime.now().isoformat(timespec='seconds')`.
- Exit codes: 0 success/active/enabled, 3 inactive, 1 not-enabled/generic-failure.
- Do not background daemons manually (no `nohup`, no `&`); tests spawn processes via `subprocess.Popen`.
