"""Tests for alarm rules.

Covers parse_time, the default weekday, and next_occurrence.
"""

import unittest
from datetime import datetime

from alarm import default_weekdays, next_occurrence, parse_time


class ParseTimeTests(unittest.TestCase):
    def test_accepts_approved_times(self):
        cases = [
            ("8:00 AM", (8, 0)),
            ("08:00 AM", (8, 0)),
            ("8:00 PM", (20, 0)),
            ("08:00 pm", (20, 0)),
            ("12:00 AM", (0, 0)),
            ("12:00 PM", (12, 0)),
            ("12:30 AM", (0, 30)),
            ("12:30 PM", (12, 30)),
            ("1:00 AM", (1, 0)),
            ("1:15 PM", (13, 15)),
            ("10:00 AM", (10, 0)),
            ("11:59 PM", (23, 59)),
            ("  9:05 Am  ", (9, 5)),
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(parse_time(text), expected)

    def test_rejects_invalid_times(self):
        cases = [
            "-11:40 PM",
            "0:00 AM",
            "00:00 AM",
            "13:00 AM",
            "8:60 AM",
            "8:00",
            "8 AM",
            "8:00 AM extra",
            "8:00AM",
            "8:00  AM",
            "8:5 AM",
            "",
            "   ",
            "8:00:00 AM",
            "8:00 XM",
            "24:00 AM",
            "8:00 am.",
        ]
        for text in cases:
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as caught:
                    parse_time(text)
                self.assertIn("8:00 AM", str(caught.exception))


class NextOccurrenceTests(unittest.TestCase):
    def test_section_examples_for_one_alarm_time(self):
        monday_8am = datetime(2026, 11, 16, 8, 0)
        self.assertEqual(monday_8am.weekday(), 0)

        tuesday_8am = next_occurrence(
            8, 0, default_weekdays(8, 0, monday_8am), monday_8am
        )
        self.assertEqual(tuesday_8am, datetime(2026, 11, 17, 8, 0))

        monday_8pm = next_occurrence(
            20, 0, default_weekdays(20, 0, monday_8am), monday_8am
        )
        self.assertEqual(monday_8pm, datetime(2026, 11, 16, 20, 0))

        friday_8pm = next_occurrence(20, 0, {4}, monday_8am)
        self.assertEqual(friday_8pm, datetime(2026, 11, 20, 20, 0))

    def test_repeat_monday_and_thursday_wraps_the_week(self):
        monday_8am = datetime(2026, 11, 16, 8, 0)
        days = {0, 3}

        monday_8pm = next_occurrence(20, 0, days, monday_8am)
        thursday_8pm = next_occurrence(20, 0, days, monday_8pm)
        following_monday_8pm = next_occurrence(20, 0, days, thursday_8pm)

        self.assertEqual(monday_8pm, datetime(2026, 11, 16, 20, 0))
        self.assertEqual(thursday_8pm, datetime(2026, 11, 19, 20, 0))
        self.assertEqual(following_monday_8pm, datetime(2026, 11, 23, 20, 0))

        thursday_9pm = datetime(2026, 11, 19, 21, 0)
        self.assertEqual(
            next_occurrence(20, 0, days, thursday_9pm),
            datetime(2026, 11, 23, 20, 0),
        )

    def test_all_seven_weekdays_use_the_next_future_time(self):
        monday_8am = datetime(2026, 11, 16, 8, 0)
        every_day = set(range(7))

        self.assertEqual(
            next_occurrence(8, 0, every_day, monday_8am),
            datetime(2026, 11, 17, 8, 0),
        )
        self.assertEqual(
            next_occurrence(20, 0, every_day, monday_8am),
            datetime(2026, 11, 16, 20, 0),
        )

    def test_midnight_boundaries_and_time_equal_to_now(self):
        sunday_1159pm = datetime(2026, 11, 22, 23, 59)
        self.assertEqual(sunday_1159pm.weekday(), 6)
        self.assertEqual(default_weekdays(0, 0, sunday_1159pm), {0})
        self.assertEqual(
            next_occurrence(0, 0, {0}, sunday_1159pm),
            datetime(2026, 11, 23, 0, 0),
        )

        monday_1201am = datetime(2026, 11, 23, 0, 1)
        self.assertEqual(default_weekdays(0, 0, monday_1201am), {1})
        self.assertEqual(
            next_occurrence(0, 0, default_weekdays(0, 0, monday_1201am), monday_1201am),
            datetime(2026, 11, 24, 0, 0),
        )

        monday_8am = datetime(2026, 11, 16, 8, 0)
        self.assertEqual(default_weekdays(8, 0, monday_8am), {1})
        self.assertEqual(
            next_occurrence(8, 0, {0}, monday_8am),
            datetime(2026, 11, 23, 8, 0),
        )

    def test_week_can_cross_into_the_next_year(self):
        thursday_8am = datetime(2026, 12, 31, 8, 0)
        self.assertEqual(thursday_8am.weekday(), 3)
        self.assertEqual(
            next_occurrence(8, 0, {0}, thursday_8am),
            datetime(2027, 1, 4, 8, 0),
        )

    def test_rejects_empty_or_unknown_weekdays(self):
        reference = datetime(2026, 11, 16, 8, 0)
        for weekdays in ([], set(), {7}, {-1}):
            with self.subTest(weekdays=weekdays):
                with self.assertRaises(ValueError) as caught:
                    next_occurrence(8, 0, weekdays, reference)
                self.assertIn("weekday", str(caught.exception).lower())


if __name__ == "__main__":
    unittest.main()
