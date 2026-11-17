"""Tests for alarm rules.

Covers parse_time, parse_weekdays, the default weekday, next_occurrence,
the alarm record, and storing a new alarm id.
"""

import unittest
from datetime import datetime

from alarm import (
    default_weekdays,
    empty_alarm_store,
    make_alarm_record,
    next_occurrence,
    parse_time,
    parse_weekdays,
    store_new_alarm,
)


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


class ParseWeekdaysTests(unittest.TestCase):
    def test_accepts_full_names_in_any_case(self):
        cases = [
            ("Monday", {0}),
            ("friday", {4}),
            ("Sunday", {6}),
            ("monday, thursday", {0, 3}),
            (" Monday , Thursday ", {0, 3}),
            ("Monday, Monday", {0}),
            (
                "Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday",
                {0, 1, 2, 3, 4, 5, 6},
            ),
        ]
        for text, expected in cases:
            with self.subTest(text=text):
                self.assertEqual(parse_weekdays(text), expected)

    def test_chosen_friday_text_feeds_next_occurrence(self):
        monday_8am = datetime(2026, 11, 16, 8, 0)
        friday = parse_weekdays("Friday")
        self.assertEqual(
            next_occurrence(20, 0, friday, monday_8am),
            datetime(2026, 11, 20, 20, 0),
        )

    def test_rejects_empty_or_invalid_weekday_text(self):
        cases = [
            "",
            "   ",
            "Mon",
            "Monday Thursday",
            "Monday,",
            "Monday,,Thursday",
            ",Monday",
            "Funday",
            "8",
        ]
        for text in cases:
            with self.subTest(text=text):
                with self.assertRaises(ValueError) as caught:
                    parse_weekdays(text)
                self.assertIn("weekday", str(caught.exception).lower())


class AlarmRecordTests(unittest.TestCase):
    def test_section_examples_become_scheduled_records(self):
        monday_8am = datetime(2026, 11, 16, 8, 0)

        eight_am = default_weekdays(8, 0, monday_8am)
        once_morning = make_alarm_record(
            1,
            8,
            0,
            "once",
            eight_am,
            "scheduled",
            next_occurrence(8, 0, eight_am, monday_8am),
            None,
        )
        self.assertEqual(once_morning["mode"], "once")
        self.assertEqual(once_morning["weekdays"], {1})
        self.assertEqual(once_morning["next_due_at"], datetime(2026, 11, 17, 8, 0))

        eight_pm = default_weekdays(20, 0, monday_8am)
        once_evening = make_alarm_record(
            2,
            20,
            0,
            "once",
            eight_pm,
            "scheduled",
            next_occurrence(20, 0, eight_pm, monday_8am),
            None,
        )
        self.assertEqual(once_evening["weekdays"], {0})
        self.assertEqual(once_evening["next_due_at"], datetime(2026, 11, 16, 20, 0))

        friday = parse_weekdays("Friday")
        chosen_friday = make_alarm_record(
            3,
            20,
            0,
            "once",
            friday,
            "scheduled",
            next_occurrence(20, 0, friday, monday_8am),
            None,
        )
        self.assertEqual(chosen_friday["weekdays"], {4})
        self.assertEqual(chosen_friday["next_due_at"], datetime(2026, 11, 20, 20, 0))

        monday_and_thursday = parse_weekdays("Monday, Thursday")
        repeated = make_alarm_record(
            4,
            20,
            0,
            "repeat",
            monday_and_thursday,
            "scheduled",
            next_occurrence(20, 0, monday_and_thursday, monday_8am),
            None,
        )
        self.assertEqual(repeated["mode"], "repeat")
        self.assertEqual(repeated["weekdays"], {0, 3})
        self.assertEqual(repeated["next_due_at"], datetime(2026, 11, 16, 20, 0))
        self.assertIsNone(repeated["last_triggered_occurrence"])

        monday_and_thursday.add(4)
        self.assertEqual(repeated["weekdays"], {0, 3})

    def test_finished_alarm_keeps_no_next_occurrence(self):
        finished = make_alarm_record(
            5,
            8,
            0,
            "once",
            {0},
            "finished",
            None,
            datetime(2026, 11, 16, 8, 0),
        )
        self.assertEqual(finished["state"], "finished")
        self.assertIsNone(finished["next_due_at"])
        self.assertEqual(
            finished["last_triggered_occurrence"],
            datetime(2026, 11, 16, 8, 0),
        )

    def test_ringing_alarm_keeps_its_occurrence(self):
        ringing = make_alarm_record(
            6,
            8,
            0,
            "once",
            {0},
            "ringing",
            datetime(2026, 11, 16, 8, 0),
            datetime(2026, 11, 16, 8, 0),
        )
        self.assertEqual(ringing["state"], "ringing")
        self.assertEqual(ringing["next_due_at"], datetime(2026, 11, 16, 8, 0))

    def test_rejects_a_record_that_breaks_its_fields(self):
        due = datetime(2026, 11, 17, 8, 0)
        cases = [
            (0, 8, 0, "once", {1}, "scheduled", due, None),
            (1, 24, 0, "once", {1}, "scheduled", due, None),
            (1, 8, 60, "once", {1}, "scheduled", due, None),
            (1, 8, 0, "daily", {1}, "scheduled", due, None),
            (1, 8, 0, "once", {1}, "paused", due, None),
            (1, 8, 0, "once", set(), "scheduled", due, None),
            (1, 8, 0, "once", {7}, "scheduled", due, None),
            (1, 8, 0, "once", {1}, "scheduled", None, None),
            (1, 8, 0, "once", {1}, "finished", due, None),
            (1, 8, 0, "once", {4}, "scheduled", due, None),
            (1, 8, 0, "once", {1}, "scheduled", datetime(2026, 11, 17, 9, 0), None),
        ]
        for fields in cases:
            with self.subTest(fields=fields):
                with self.assertRaises(ValueError):
                    make_alarm_record(*fields)


class AlarmStoreTests(unittest.TestCase):
    def test_new_alarms_receive_increasing_ids(self):
        monday_8am = datetime(2026, 11, 16, 8, 0)
        store = empty_alarm_store()
        self.assertEqual(store["next_alarm_id"], 1)
        self.assertEqual(store["alarms_by_id"], {})

        morning_days = default_weekdays(8, 0, monday_8am)
        morning = make_alarm_record(
            1,
            8,
            0,
            "once",
            morning_days,
            "scheduled",
            next_occurrence(8, 0, morning_days, monday_8am),
            None,
        )
        stored_morning = store_new_alarm(store, morning)
        self.assertIs(store["alarms_by_id"][1], stored_morning)
        self.assertEqual(stored_morning["next_due_at"], datetime(2026, 11, 17, 8, 0))
        self.assertEqual(store["next_alarm_id"], 2)

        morning["state"] = "finished"
        morning["weekdays"].add(4)
        self.assertEqual(stored_morning["state"], "scheduled")
        self.assertEqual(stored_morning["weekdays"], {1})

        evening_days = default_weekdays(20, 0, monday_8am)
        evening = make_alarm_record(
            2,
            20,
            0,
            "once",
            evening_days,
            "scheduled",
            next_occurrence(20, 0, evening_days, monday_8am),
            None,
        )
        store_new_alarm(store, evening)
        self.assertEqual(set(store["alarms_by_id"]), {1, 2})
        self.assertEqual(
            store["alarms_by_id"][2]["next_due_at"],
            datetime(2026, 11, 16, 20, 0),
        )
        self.assertEqual(store["next_alarm_id"], 3)

    def test_wrong_id_leaves_the_store_unchanged(self):
        store = empty_alarm_store()
        wrong = make_alarm_record(
            2,
            8,
            0,
            "once",
            {1},
            "scheduled",
            datetime(2026, 11, 17, 8, 0),
            None,
        )
        with self.assertRaises(ValueError) as caught:
            store_new_alarm(store, wrong)
        self.assertIn("1", str(caught.exception))
        self.assertEqual(store["next_alarm_id"], 1)
        self.assertEqual(store["alarms_by_id"], {})


if __name__ == "__main__":
    unittest.main()
