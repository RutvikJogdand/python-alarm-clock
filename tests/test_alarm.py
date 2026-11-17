"""Tests for alarm rules. This file currently covers parse_time only."""

import unittest

from alarm import parse_time


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


if __name__ == "__main__":
    unittest.main()
