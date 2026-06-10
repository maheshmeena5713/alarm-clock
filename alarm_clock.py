import json
import os
import sys
import time
import threading
import uuid
from datetime import datetime, timedelta
from pathlib import Path

import schedule

# ── Config ──────────────────────────────────────────────────────────────────

ALARMS_FILE = Path.home() / ".alarm_clock_data.json"
CHECK_INTERVAL = 10  # seconds between schedule checks

# ── ANSI Colors (graceful fallback on Windows) ───────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
DIM    = "\033[2m"


def c(color: str, text: str) -> str:
    """Wrap text in ANSI color — degrades gracefully if not a TTY."""
    if sys.stdout.isatty():
        return f"{color}{text}{RESET}"
    return text


# ── Storage ───────────────────────────────────────────────────────────────────

def load_alarms() -> list[dict]:
    if ALARMS_FILE.exists():
        try:
            return json.loads(ALARMS_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return []
    return []


def save_alarms(alarms: list[dict]) -> None:
    ALARMS_FILE.write_text(json.dumps(alarms, indent=2))


# ── Alarm Logic ───────────────────────────────────────────────────────────────

def ring(alarm: dict) -> None:
    """Called when an alarm fires."""
    os.system("cls" if os.name == "nt" else "clear")
    print("\n" + c(RED + BOLD, "╔══════════════════════════════════════╗"))
    print(c(RED + BOLD,         "║  🔔  ALARM RINGING!                  ║"))
    print(c(RED + BOLD,         f"║  ⏰  {alarm['time']}  —  {alarm['label']:<26}║"))
    print(c(RED + BOLD,         "╚══════════════════════════════════════╝\n"))
    # Terminal bell (works everywhere, no dependencies)
    for _ in range(5):
        sys.stdout.write("\a")
        sys.stdout.flush()
        time.sleep(0.4)

    choice = input(c(YELLOW, "  [s]nooze 5 min  |  [d]ismiss  → ")).strip().lower()
    if choice == "s":
        snooze_until = (datetime.now() + timedelta(minutes=5)).strftime("%H:%M")
        alarms = load_alarms()
        for a in alarms:
            if a["id"] == alarm["id"]:
                a["time"] = snooze_until
                a["label"] = f"Snoozed: {alarm['label']}"
        save_alarms(alarms)
        print(c(GREEN, f"\n  ✅  Snoozed until {snooze_until}"))
    else:
        # Dismiss: remove non-recurring alarms
        alarms = load_alarms()
        if alarm.get("recurring"):
            print(c(GREEN, "\n  ✅  Dismissed — repeats tomorrow."))
        else:
            alarms = [a for a in alarms if a["id"] != alarm["id"]]
            save_alarms(alarms)
            print(c(GREEN, "\n  ✅  Alarm dismissed."))
    time.sleep(1)


# ── Background Watcher ────────────────────────────────────────────────────────

_ringing_lock = threading.Lock()
_ringing_ids: set[str] = set()  # prevent double-firing within the same minute


def _check_alarms() -> None:
    now = datetime.now().strftime("%H:%M")
    alarms = load_alarms()
    for alarm in alarms:
        if alarm["time"] == now and alarm["id"] not in _ringing_ids:
            with _ringing_lock:
                _ringing_ids.add(alarm["id"])
            # Fire in main thread via a flag so input() works properly
            _pending_rings.append(alarm)


_pending_rings: list[dict] = []


def start_background_watcher() -> threading.Thread:
    schedule.every(CHECK_INTERVAL).seconds.do(_check_alarms)

    def _run():
        while True:
            schedule.run_pending()
            time.sleep(1)

    t = threading.Thread(target=_run, daemon=True)
    t.start()
    return t


# ── CLI Helpers ───────────────────────────────────────────────────────────────

BANNER = f"""
{c(CYAN + BOLD, '╔══════════════════════════════════════╗')}
{c(CYAN + BOLD, '║        🕐  CLI Alarm Clock            ║')}
{c(CYAN + BOLD, '╚══════════════════════════════════════╝')}
"""

MENU = f"""
  {c(BOLD, '[1]')} Set alarm
  {c(BOLD, '[2]')} List alarms
  {c(BOLD, '[3]')} Delete alarm
  {c(BOLD, '[4]')} Current time
  {c(BOLD, '[q]')} Quit
"""


def print_banner() -> None:
    os.system("cls" if os.name == "nt" else "clear")
    print(BANNER)
    print(c(DIM, f"  Alarms stored at: {ALARMS_FILE}"))
    print(c(DIM, f"  Checking every {CHECK_INTERVAL}s\n"))


def prompt_time() -> str | None:
    raw = input(c(YELLOW, "  Enter time (HH:MM, 24h): ")).strip()
    try:
        datetime.strptime(raw, "%H:%M")
        return raw
    except ValueError:
        print(c(RED, "  ✗ Invalid format. Use HH:MM (e.g. 09:30 or 14:45)."))
        return None


def cmd_set_alarm() -> None:
    print(c(BOLD, "\n  ── Set New Alarm ──"))
    alarm_time = prompt_time()
    if not alarm_time:
        return

    label = input(c(YELLOW, "  Label (default: 'Alarm'): ")).strip() or "Alarm"
    recurring = input(c(YELLOW, "  Repeat daily? [y/N]: ")).strip().lower() == "y"

    # Warn if alarm time has already passed today
    now = datetime.now()
    alarm_dt = datetime.strptime(alarm_time, "%H:%M").replace(
        year=now.year, month=now.month, day=now.day
    )
    already_passed = alarm_dt <= now
    if already_passed and not recurring:
        print(c(YELLOW, f"\n  ⚠  {alarm_time} has already passed today."))
        print(c(YELLOW,  "     This alarm will fire tomorrow."))

    alarms = load_alarms()
    alarm = {
        "id": str(uuid.uuid4())[:8],
        "time": alarm_time,
        "label": label,
        "recurring": recurring,
        "created_at": now.isoformat(),
    }
    alarms.append(alarm)
    save_alarms(alarms)
    _ringing_ids.discard(alarm_time)  # allow it to fire today if not yet passed

    tag = c(GREEN, "✅ ") + c(BOLD, f"{alarm_time}") + f"  —  {label}"
    tag += c(DIM, "  (daily)" if recurring else "")
    alarm_id = alarm["id"]
    print(f"\n  {tag}\n  {c(DIM, f'ID: {alarm_id}')}\n")


def cmd_list_alarms() -> None:
    alarms = load_alarms()
    print(c(BOLD, "\n  ── Active Alarms ──"))
    if not alarms:
        print(c(DIM, "  No alarms set.\n"))
        return
    now = datetime.now().strftime("%H:%M")
    for a in sorted(alarms, key=lambda x: x["time"]):
        status = c(GREEN, "▶ ") if a["time"] > now else c(DIM, "● ")
        recur  = c(DIM, " ↻ daily") if a.get("recurring") else ""
        print(f"  {status}{c(BOLD, a['time'])}  {a['label']}{recur}  {c(DIM, a['id'])}")
    print()


def cmd_delete_alarm() -> None:
    alarms = load_alarms()
    if not alarms:
        print(c(DIM, "\n  No alarms to delete.\n"))
        return

    cmd_list_alarms()
    alarm_id = input(c(YELLOW, "  Enter alarm ID to delete (or [a] for all): ")).strip().lower()

    if alarm_id == "a":
        save_alarms([])
        print(c(GREEN, "  ✅  All alarms cleared.\n"))
    else:
        before = len(alarms)
        alarms = [a for a in alarms if a["id"] != alarm_id]
        if len(alarms) < before:
            save_alarms(alarms)
            print(c(GREEN, f"  ✅  Alarm {alarm_id} deleted.\n"))
        else:
            print(c(RED, f"  ✗  ID '{alarm_id}' not found.\n"))


def cmd_current_time() -> None:
    now = datetime.now()
    print(c(BOLD, f"\n  🕐  {now.strftime('%A, %d %B %Y  —  %H:%M:%S')}\n"))


# ── Main Loop ─────────────────────────────────────────────────────────────────

def main() -> None:
    start_background_watcher()
    print_banner()

    while True:
        # Fire any pending alarms (input-safe — runs in main thread)
        if _pending_rings:
            alarm = _pending_rings.pop(0)
            ring(alarm)
            print_banner()

        print(MENU)
        try:
            choice = input(c(CYAN, "  → ")).strip().lower()
        except (KeyboardInterrupt, EOFError):
            print(c(DIM, "\n\n  Goodbye! 👋\n"))
            sys.exit(0)

        if choice == "1":
            cmd_set_alarm()
        elif choice == "2":
            cmd_list_alarms()
        elif choice == "3":
            cmd_delete_alarm()
        elif choice == "4":
            cmd_current_time()
        elif choice in ("q", "quit", "exit"):
            print(c(DIM, "\n  Goodbye! 👋\n"))
            sys.exit(0)
        else:
            print(c(RED, "  ✗  Invalid option.\n"))

        input(c(DIM, "  Press Enter to continue..."))
        print_banner()


if __name__ == "__main__":
    main()