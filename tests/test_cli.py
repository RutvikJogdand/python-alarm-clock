"""Command behaviour for the alarm clock."""

import unittest
from datetime import datetime

from cli import handle_line, new_session


def run(session, lines):
    output = []
    for line in lines:
        output.extend(handle_line(session, line))
    return "\n".join(output)


class CliTests(unittest.TestCase):
    def test_demo_path_rings_and_stop_finishes_the_alarm(self):
        session = new_session(datetime(2026, 11, 18, 3, 20))
        empty = run(session, ["show all alarms"])
        self.assertIn("No alarms set. If you want to set a alarm type: Set alarm", empty)

        created = run(
            session,
            [
                "set clock",
                "18-11-2026",
                "7:00 AM",
                "yes",
                "set alarm",
                "8:00 AM",
                "once",
                "",
                "yes",
                "set alarm",
                "8:00 PM",
                "once",
                "Friday",
                "yes",
                "set alarm",
                "8:00 PM",
                "repeat",
                "Monday, Thursday",
                "yes",
            ],
        )
        self.assertIn("First ring: 18-11-2026 8:00 AM", created)
        self.assertIn("20-11-2026 8:00 PM", created)
        self.assertIn("Monday, Thursday", created)

        before = len(session["store"]["alarms_by_id"])
        rejected = run(session, ["set alarm", "-11:40 PM", "once"])
        self.assertIn("8:00 AM", rejected)
        self.assertEqual(len(session["store"]["alarms_by_id"]), before)
        run(session, ["cancel"])

        ringing = run(session, ["set clock", "18-11-2026", "8:00 AM", "yes"])
        self.assertIn("RING alarm 1", ringing)
        self.assertEqual(session["store"]["alarms_by_id"][1]["state"], "ringing")
        blocked = run(session, ["delete 1"])
        self.assertIn("ringing", blocked)
        self.assertIn(1, session["store"]["alarms_by_id"])

        stopped = run(session, ["stop 1"])
        self.assertIn("finished", stopped)
        self.assertEqual(session["store"]["alarms_by_id"][1]["state"], "finished")

        listed = run(session, ["show all alarms"])
        self.assertIn("finished", listed)
        self.assertNotIn("No alarms set", listed)

    def test_stop_works_while_a_dialog_is_open(self):
        session = new_session(datetime(2026, 11, 18, 7, 0))
        run(
            session,
            ["set alarm", "8:00 AM", "once", "", "yes", "set clock", "18-11-2026", "8:00 AM", "yes"],
        )
        self.assertEqual(session["store"]["alarms_by_id"][1]["state"], "ringing")
        run(session, ["set alarm", "9:00 AM", "STOP 1"])
        self.assertEqual(session["store"]["alarms_by_id"][1]["state"], "finished")
        self.assertEqual(session["dialog"]["step"], "mode")
        run(session, ["cancel"])
        self.assertIsNone(session["dialog"])

    def test_exit_stops_the_session(self):
        session = new_session(datetime(2026, 11, 18, 7, 0))
        message = run(session, ["exit"])
        self.assertFalse(session["running"])
        self.assertIn("memory", message)


if __name__ == "__main__":
    unittest.main()
