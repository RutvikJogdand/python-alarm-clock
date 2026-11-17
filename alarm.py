"""Alarm data, clock calculations, validation, scheduling, and state changes.

No terminal input or output belongs in this module.
"""

import re

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
