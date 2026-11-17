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
