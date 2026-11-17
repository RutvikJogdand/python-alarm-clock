"""Commands and prompts for the alarm clock.

The input thread only places lines on a queue. The main loop is the only
code that changes alarms or the app clock.
"""

import queue
import threading
import time
from datetime import datetime

import alarm


HELP_TEXT = """Commands:
  Set alarm
  Show all alarms
  Edit <id>
  Delete <id>
  STOP <id>
  Set clock
  Cancel
  Help
  Exit

Times look like 8:00 AM. Dates look like 18-11-2026.
Alarms stay in memory only. Exit clears them. There is no sound.
"""


def new_session(now):
    """Return the in-memory session the main loop owns."""
    moment = now.replace(microsecond=0)
    return {
        "store": alarm.empty_alarm_store(),
        "now": moment,
        "base_datetime": moment,
        "reset_clock_anchor": False,
        "dialog": None,
        "clock_plan": None,
        "running": True,
    }


def _normalize(line):
    return " ".join(line.strip().split()).lower()


def _weekday_text(weekdays):
    return ", ".join(alarm.WEEKDAY_NAMES[day] for day in sorted(weekdays))


def _prompt_for(session):
    dialog = session["dialog"]
    if dialog is None:
        return ">"
    step = dialog["step"]
    if step == "time":
        return "Time, for example 8:00 AM:"
    if step == "mode":
        return "Type once, repeat, or daily:"
    if step == "days":
        default_name = _weekday_text(dialog["default_days"])
        if dialog["mode"] == "once":
            return f"Weekday [{default_name}]. Press Enter for that day, or type another:"
        return (
            f"Weekdays [{default_name}]. Press Enter for that day, "
            "or type days such as Monday, Thursday:"
        )
    if step == "confirm":
        return "Type yes to save, or Cancel:"
    if step == "clock_date":
        return "Date as DD-MM-YYYY, for example 18-11-2026:"
    if step == "clock_time":
        return "Time, for example 7:00 AM:"
    if step == "clock_confirm":
        return "Type yes to apply this clock change, or Cancel:"
    return ">"


def _show(session):
    return [alarm.format_alarm_list(session["store"], session["now"])]


def _start_set(session, edit_id):
    if edit_id is not None:
        current = session["store"]["alarms_by_id"].get(edit_id)
        if current is None:
            return [f"No alarm {edit_id}."]
        if current["state"] == "ringing":
            return [f"Alarm {edit_id} is ringing. Use STOP {edit_id} first."]
    session["dialog"] = {
        "kind": "alarm",
        "step": "time",
        "edit_id": edit_id,
        "hour_24": None,
        "minute": None,
        "mode": None,
        "weekdays": None,
        "default_days": None,
    }
    session["clock_plan"] = None
    return ["Setting an alarm.", _prompt_for(session)]


def _start_clock(session):
    session["dialog"] = {"kind": "clock", "step": "clock_date", "date_text": None}
    session["clock_plan"] = None
    return ["Setting the app clock. This does not change the computer clock.", _prompt_for(session)]


def _clear_dialog(session):
    session["dialog"] = None
    session["clock_plan"] = None


def _save_alarm_draft(session):
    dialog = session["dialog"]
    due = alarm.next_occurrence(
        dialog["hour_24"], dialog["minute"], dialog["weekdays"], session["now"]
    )
    if dialog["edit_id"] is None:
        record = alarm.make_alarm_record(
            session["store"]["next_alarm_id"],
            dialog["hour_24"],
            dialog["minute"],
            dialog["mode"],
            dialog["weekdays"],
            "scheduled",
            due,
            None,
        )
        alarm.store_new_alarm(session["store"], record)
    else:
        record = alarm.make_alarm_record(
            dialog["edit_id"],
            dialog["hour_24"],
            dialog["minute"],
            dialog["mode"],
            dialog["weekdays"],
            "scheduled",
            due,
            None,
        )
        alarm.replace_alarm(session["store"], record)
    _clear_dialog(session)
    return [
        f"Saved alarm {record['id']}. First ring: {alarm.format_when(due)}.",
        alarm.format_alarm_list(session["store"], session["now"]),
    ]


def _answer_alarm_dialog(session, text):
    dialog = session["dialog"]
    if dialog["step"] == "time":
        hour_24, minute = alarm.parse_time(text)
        dialog["hour_24"] = hour_24
        dialog["minute"] = minute
        dialog["step"] = "mode"
        return [_prompt_for(session)]
    if dialog["step"] == "mode":
        choice = text.strip(" ").lower()
        if choice == "daily":
            dialog["mode"] = "repeat"
            dialog["weekdays"] = set(range(7))
            dialog["step"] = "confirm"
            return _preview_alarm(session) + [_prompt_for(session)]
        if choice not in alarm.VALID_MODES:
            return ["Type once, repeat, or daily.", _prompt_for(session)]
        dialog["mode"] = choice
        dialog["default_days"] = alarm.default_weekdays(dialog["hour_24"], dialog["minute"], session["now"])
        dialog["step"] = "days"
        return [_prompt_for(session)]
    if dialog["step"] == "days":
        if text.strip(" ") == "":
            dialog["weekdays"] = set(dialog["default_days"])
        else:
            dialog["weekdays"] = alarm.parse_weekdays(text)
        dialog["step"] = "confirm"
        return _preview_alarm(session) + [_prompt_for(session)]
    if text.strip(" ").lower() in ("yes", "y"):
        messages = _save_alarm_draft(session)
        messages.append(_prompt_for(session))
        return messages
    return ["Type yes to save, or Cancel.", _prompt_for(session)]


def _preview_alarm(session):
    dialog = session["dialog"]
    due = alarm.next_occurrence(
        dialog["hour_24"], dialog["minute"], dialog["weekdays"], session["now"]
    )
    return [
        "First ring: "
        f"{alarm.format_when(due)} ({dialog['mode']}, {_weekday_text(dialog['weekdays'])})."
    ]


def _answer_clock_dialog(session, text):
    dialog = session["dialog"]
    if dialog["step"] == "clock_date":
        alarm.parse_clock_datetime(text, "12:00 AM")
        dialog["date_text"] = text.strip(" ")
        dialog["step"] = "clock_time"
        return [_prompt_for(session)]
    if dialog["step"] == "clock_time":
        new_time = alarm.parse_clock_datetime(dialog["date_text"], text)
        plan = alarm.plan_clock_change(session["store"], new_time)
        session["clock_plan"] = plan
        dialog["step"] = "clock_confirm"
        preview = plan["lines"] or ["No stored alarms to move."]
        return ["Proposed clock change:"] + preview + [_prompt_for(session)]
    if text.strip(" ").lower() in ("yes", "y"):
        fresh = alarm.apply_clock_change(session["store"], session["clock_plan"])
        session["now"] = fresh["new_time"]
        session["base_datetime"] = fresh["new_time"]
        session["reset_clock_anchor"] = True
        due_ids = alarm.process_due_alarms(session["store"], session["now"])
        _clear_dialog(session)
        messages = ["Clock updated."]
        messages.extend(_ring_lines(session, due_ids))
        messages.append(alarm.format_alarm_list(session["store"], session["now"]))
        messages.append(_prompt_for(session))
        return messages
    return ["Type yes to apply this clock change, or Cancel.", _prompt_for(session)]


def _ring_lines(session, due_ids):
    lines = []
    for alarm_id in due_ids:
        current = session["store"]["alarms_by_id"][alarm_id]
        lines.append(
            f"RING alarm {alarm_id} at "
            f"{alarm.format_time_12(current['hour_24'], current['minute'])}. "
            f"Type STOP {alarm_id}"
        )
    return lines


def _handle_stop(session, text):
    parts = text.strip().split()
    if len(parts) != 2:
        return ["Type STOP and an id, for example STOP 1."]
    alarm_id = alarm.parse_alarm_id(parts[1])
    alarm.stop_alarm(session["store"], alarm_id, session["now"])
    current = session["store"]["alarms_by_id"][alarm_id]
    if current["state"] == "finished":
        return [f"Alarm {alarm_id} is finished."]
    return [f"Alarm {alarm_id} will ring next at {alarm.format_when(current['next_due_at'])}."]


def handle_line(session, line):
    """Handle one input line. Return the lines to print."""
    try:
        return _handle_line(session, line)
    except ValueError as error:
        return [str(error), _prompt_for(session)]


def _handle_line(session, line):
    normalized = _normalize(line)
    if normalized in ("exit",):
        session["running"] = False
        return ["Exit. Stored alarms are lost because they are kept in memory only."]
    if normalized == "help":
        return [HELP_TEXT.rstrip(), _prompt_for(session)]
    if normalized == "cancel":
        if session["dialog"] is None:
            return ["Nothing to cancel.", _prompt_for(session)]
        _clear_dialog(session)
        return ["Cancelled.", _prompt_for(session)]
    if normalized.startswith("stop"):
        messages = _handle_stop(session, line)
        if session["dialog"] is not None:
            messages.append(_prompt_for(session))
        else:
            messages.append(_prompt_for(session))
        return messages

    if session["dialog"] is not None:
        if session["dialog"]["kind"] == "alarm":
            return _answer_alarm_dialog(session, line)
        return _answer_clock_dialog(session, line)

    if normalized == "set alarm":
        return _start_set(session, None)
    if normalized == "show all alarms":
        return _show(session) + [_prompt_for(session)]
    if normalized == "set clock":
        return _start_clock(session)
    if normalized.startswith("edit "):
        return _start_set(session, alarm.parse_alarm_id(normalized.split()[1]))
    if normalized.startswith("delete "):
        alarm_id = alarm.parse_alarm_id(normalized.split()[1])
        alarm.delete_alarm(session["store"], alarm_id)
        return [f"Deleted alarm {alarm_id}.", alarm.format_alarm_list(session["store"], session["now"]), _prompt_for(session)]
    return ["Unknown command. Type Help.", _prompt_for(session)]


def read_input(command_queue):
    """Read terminal lines onto the queue. This function does not touch alarms."""
    while True:
        try:
            line = input()
        except EOFError:
            command_queue.put(None)
            return
        except KeyboardInterrupt:
            command_queue.put(None)
            return
        command_queue.put(line)


def _print_messages(messages):
    for message in messages:
        print(message)


def main():
    """Run the clock and the command loop until Exit or Ctrl+C."""
    now = datetime.now().replace(microsecond=0)
    session = new_session(now)
    base_monotonic = time.monotonic()
    command_queue = queue.Queue()
    reader = threading.Thread(target=read_input, args=(command_queue,), daemon=True)
    reader.start()
    print("Alarm clock. The computer clock is left unchanged.")
    print(alarm.format_alarm_list(session["store"], session["now"]))
    print("Type Help for commands.")
    print(">")
    try:
        while session["running"]:
            session["now"] = alarm.read_app_time(
                session["base_datetime"], base_monotonic, time.monotonic()
            )
            due_ids = alarm.process_due_alarms(session["store"], session["now"])
            if due_ids:
                print()
                _print_messages(_ring_lines(session, due_ids))
                print(_prompt_for(session))
            try:
                line = command_queue.get(timeout=alarm.CHECK_INTERVAL_SECONDS)
            except queue.Empty:
                continue
            if line is None:
                print("Exit. Stored alarms are lost because they are kept in memory only.")
                break
            messages = handle_line(session, line)
            _print_messages(messages)
            if session["reset_clock_anchor"]:
                base_monotonic = time.monotonic()
                session["reset_clock_anchor"] = False
    except KeyboardInterrupt:
        print()
        print("Exit. Stored alarms are lost because they are kept in memory only.")


if __name__ == "__main__":
    main()
