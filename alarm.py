"""Alarm data, clock calculations, validation, scheduling, and state changes.

No terminal input or output belongs in this module.
"""

import re
from datetime import datetime, timedelta

# Hour 1-12 with an optional leading zero, minutes 00-59, one space, then AM or PM.
TIME_INPUT_PATTERN = re.compile(
    r"(0?[1-9]|1[0-2]):([0-5][0-9]) ([AP]M)",
    re.IGNORECASE,
)

# Monday is 0 and Sunday is 6. The position of each name is its weekday number.
WEEKDAY_NAMES = (
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
)

VALID_MODES = ("once", "repeat")
VALID_STATES = ("scheduled", "ringing", "finished")
MAX_ALARMS = 10


def parse_time(text): #function to parse a 12-hour time string and convert it to a 24-hour time for interal operations.
    """Return (hour_24, minute) for an approved 12-hour time.

    Spaces at the two ends are removed first. Any other shape of text is rejected.
    """
    cleaned = text.strip(" ") #removes any leading or trailing whitespace from the input text.
    match = TIME_INPUT_PATTERN.fullmatch(cleaned)
    if match is None:
        raise ValueError(
            "Enter a time like 8:00 AM. "
            "Use an hour from 1 to 12, minutes from 00 to 59, one space, and AM or PM."
        )

    hour_text, minute_text, meridian_text = match.groups() #extracts three matched text values from a regular expression result and assigns them to three separate variables in a single step. It is commonly used to parse a timestamp string (like "09:30 AM") into individual pieces.
    hour_12 = int(hour_text) #converts the extracted hour text to an integer, allowing it to be used in arithmetic operations.
    minute = int(minute_text)
    meridian = meridian_text.upper() #converts the extracted meridian text to uppercase, ensuring consistent comparison.

    # 12 AM is 00:00. 12 PM stays 12:00. Every other PM hour is 12 hours later.
    if meridian == "AM":
        hour_24 = 0 if hour_12 == 12 else hour_12
    else:
        hour_24 = 12 if hour_12 == 12 else hour_12 + 12

    return (hour_24, minute)


def parse_weekdays(text):
    """Return weekday numbers for comma-separated full weekday names.

    Names may use any letter case. Spaces at the ends and around commas are
    removed. Monday is 0 and Sunday is 6. A repeated name is stored once.
    """
    cleaned = text.strip(" ")
    if cleaned == "":
        raise ValueError("Enter at least one weekday, for example Monday, Thursday.")

    numbers = set()
    for part in cleaned.split(","):
        name = part.strip(" ")
        if name == "":
            raise ValueError(
                "Enter weekdays like Monday, Thursday. "
                "Use full names separated by commas."
            )
        matched_number = None
        for number, weekday_name in enumerate(WEEKDAY_NAMES):
            if name.upper() == weekday_name.upper():
                matched_number = number
                break
        if matched_number is None:
            raise ValueError(
                "Enter weekdays like Monday, Thursday. "
                "Use full names separated by commas."
            )
        numbers.add(matched_number)
    return numbers


def default_weekdays(hour_24, minute, reference): #function to determine the default weekday for a new alarm based on the current time and the reference time.
    """Return the one weekday used when a new alarm accepts the default day.

    A later clock time stays on the reference date. An equal or earlier clock
    time uses the next date. Monday is 0 and Sunday is 6.
    """
    if (hour_24, minute) > (reference.hour, reference.minute): #checks if the current time is later than the reference time.
        chosen = reference
    else:
        chosen = reference + timedelta(days=1) #if the current time is earlier than or equal to the reference time, the next day is chosen.
    return {chosen.weekday()} #returns a set containing the weekday of the chosen date.


def next_occurrence(hour_24, minute, weekdays, reference):
    """Return the earliest matching date and time strictly after reference."""
    allowed = set(weekdays)
    if len(allowed) == 0:
        raise ValueError("Choose at least one weekday.")
    for weekday in allowed:
        if weekday not in range(7):
            raise ValueError(
                "Weekday numbers run from 0 for Monday through 6 for Sunday."
            )

    # Offset 0 is the reference date. Offset 7 is the same weekday one week later.
    for day_offset in range(8):
        candidate_date = reference.date() + timedelta(days=day_offset)
        if candidate_date.weekday() not in allowed:
            continue
        candidate = datetime(
            candidate_date.year,
            candidate_date.month,
            candidate_date.day,
            hour_24,
            minute,
        )
        if candidate > reference:
            return candidate

    raise ValueError("Choose at least one weekday.")


def _require_occurrence(occurrence, hour_24, minute, weekdays):
    """Reject an occurrence that is not this alarm's weekday and time."""
    if type(occurrence) is not datetime:
        raise ValueError("An occurrence must be a date and time.")
    if occurrence.weekday() not in weekdays:
        raise ValueError("An occurrence must fall on a selected weekday.")
    if (occurrence.hour, occurrence.minute) != (hour_24, minute):
        raise ValueError("An occurrence must use the alarm's hour and minute.")


def make_alarm_record(
    alarm_id,
    hour_24,
    minute,
    mode,
    weekdays,
    state,
    next_due_at,
    last_triggered_occurrence,
):
    """Return one alarm dictionary.

    The caller supplies every field. This does not store the alarm, choose
    the next id, check the 10-alarm limit, or look for schedule conflicts.
    """
    if type(alarm_id) is not int or alarm_id < 1:
        raise ValueError("Alarm id must be a positive whole number.")
    if type(hour_24) is not int or hour_24 not in range(24):
        raise ValueError("Hour must be a whole number from 0 through 23.")
    if type(minute) is not int or minute not in range(60):
        raise ValueError("Minute must be a whole number from 0 through 59.")
    if mode not in VALID_MODES:
        raise ValueError("Alarm mode must be once or repeat.")
    if state not in VALID_STATES:
        raise ValueError("Alarm state must be scheduled, ringing, or finished.")

    stored_weekdays = set(weekdays)
    if len(stored_weekdays) == 0:
        raise ValueError("Choose at least one weekday.")
    for weekday in stored_weekdays:
        if type(weekday) is not int or weekday not in range(7):
            raise ValueError(
                "Weekday numbers run from 0 for Monday through 6 for Sunday."
            )

    if state == "finished":
        if next_due_at is not None:
            raise ValueError("A finished alarm has no next occurrence.")
    else:
        _require_occurrence(next_due_at, hour_24, minute, stored_weekdays)

    if last_triggered_occurrence is not None:
        _require_occurrence(
            last_triggered_occurrence, hour_24, minute, stored_weekdays
        )

    return {
        "id": alarm_id,
        "hour_24": hour_24,
        "minute": minute,
        "mode": mode,
        "weekdays": stored_weekdays,
        "state": state,
        "next_due_at": next_due_at,
        "last_triggered_occurrence": last_triggered_occurrence,
    }


def empty_alarm_store():
    """Return a store with no alarms and a next id of 1."""
    return {
        "alarms_by_id": {},
        "next_alarm_id": 1,
    }


def find_conflict(candidate, stored_alarms, exclude_id=None):
    """Return the id of a stored alarm that overlaps this schedule.

    Finished alarms are ignored. exclude_id skips one stored alarm so a later
    edit can ignore itself. The result is None when nothing overlaps.
    Two once alarms overlap only when their next occurrences are the same
    date and time. A repeat overlaps another alarm when they share a weekday
    and use the same hour and minute.
    """
    if candidate["state"] == "finished":
        return None

    candidate_time = (candidate["hour_24"], candidate["minute"])
    candidate_days = set(candidate["weekdays"])
    for alarm_id in sorted(stored_alarms):
        if alarm_id == exclude_id:
            continue
        alarm = stored_alarms[alarm_id]
        if alarm["state"] == "finished":
            continue
        if (alarm["hour_24"], alarm["minute"]) != candidate_time:
            continue
        if candidate["mode"] == "once" and alarm["mode"] == "once":
            if candidate["next_due_at"] == alarm["next_due_at"]:
                return alarm_id
            continue
        shared_days = candidate_days.intersection(alarm["weekdays"])
        if len(shared_days) > 0:
            return alarm_id
    return None


def store_new_alarm(store, alarm):
    """Store a new alarm whose id is the store's next id.

    At most 10 stored alarms are allowed, including finished alarms. A new
    alarm that overlaps a stored future schedule is rejected. The next id
    increases by one after a successful store. A rejected alarm leaves the
    store unchanged.
    """
    expected_id = store["next_alarm_id"]
    if alarm["id"] != expected_id:
        raise ValueError(f"The next alarm id is {expected_id}.")
    if len(store["alarms_by_id"]) >= MAX_ALARMS:
        raise ValueError(f"At most {MAX_ALARMS} alarms can be stored.")
    conflict_id = find_conflict(alarm, store["alarms_by_id"])
    if conflict_id is not None:
        raise ValueError(f"This alarm overlaps alarm {conflict_id}.")

    stored = dict(alarm)
    stored["weekdays"] = set(alarm["weekdays"])
    store["alarms_by_id"][expected_id] = stored
    store["next_alarm_id"] = expected_id + 1
    return stored
