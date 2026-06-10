# 🕐 CLI Alarm Clock

A highly robust, concurrency-safe Python CLI alarm clock designed for terminal-centric workflows. 

This project demonstrates core software engineering principles including dual-thread concurrency, thread-safe state management, producer-consumer event queueing, and local persistence.

> For a deep dive into the architectural choices and threading model, please read [DESIGN.md](DESIGN.md).

---

## ✨ Features

- **Concurrent Execution**: A background daemon reliably tracks time while the main thread handles terminal UI, avoiding blocking I/O collisions.
- **State Persistence**: Alarms are serialized to a local JSON datastore (`~/.alarm_clock_data.json`) ensuring survival across system reboots.
- **Graceful Degradation**: Built with cross-platform ANSI color support that degrades gracefully in non-TTY environments.
- **Snooze & Recurrence**: Smart state mutations allow for daily repeating alarms and 5-minute snoozes without complex state machines.
- **Zero Heavy Dependencies**: Relies primarily on the Python standard library, utilizing `schedule` for clean, readable background cron tasks.

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/alarm-clock.git
cd alarm-clock

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch the application
python alarm_clock.py
```

---

## 💻 Usage

Upon launching, the TUI (Terminal User Interface) will present a menu:

```text
╔══════════════════════════════════════╗
║        🕐  CLI Alarm Clock            ║
╚══════════════════════════════════════╝

  Alarms stored at: /Users/username/.alarm_clock_data.json
  Checking every 10s

  [1] Set alarm
  [2] List alarms
  [3] Delete alarm
  [4] Current time
  [q] Quit
```

- **Set an Alarm**: Input time in `HH:MM` (24h format). You can optionally assign a label and mark it as recurring.
- **Snooze/Dismiss**: When an alarm fires, the terminal will ring and prompt you to either dismiss it or snooze for 5 minutes.

---

## 🧪 Testing

This project includes a comprehensive test suite utilizing `pytest` to verify state mutations, parsing logic, and storage interactions.

```bash
# Run the test suite
pytest test_alarm_clock.py -v
```

---

## 📂 Project Structure

```text
cli-alarm-clock/
├── alarm_clock.py        # Main application and threading logic
├── test_alarm_clock.py   # Pytest suite for unit verification
├── requirements.txt      # Project dependencies
├── DESIGN.md             # Systems design and architecture documentation
└── README.md             # Project overview
```
