# Python alarm clock

A small command-line alarm clock. It keeps an application clock of its own and does not change the computer clock. Alarms are stored in memory only. When you Exit, they are gone. The app must stay open to ring. There is no sound, and it does not adjust itself for time-zone changes.

Tested with Python 3.13.1.

## Run

From this folder:

```text
python cli.py
```

Checks:

```text
python -m unittest discover -s tests -v
```

## Commands

Type these at the `>` prompt. Capital letters do not matter.

| Command | What it does |
| --- | --- |
| `Set alarm` | Asks for a time, then `once`, `repeat`, or `daily`, then the weekday or weekdays. |
| `Show all alarms` | Lists every alarm, including finished ones. |
| `Edit <id>` | Changes an alarm that is not ringing. |
| `Delete <id>` | Removes an alarm that is not ringing. The id is not reused. |
| `STOP <id>` | Stops one ringing alarm. `STOP` still works while you are answering a prompt. |
| `Set clock` | Shows the effect, then applies it only if you type `yes`. |
| `Cancel` | Drops the answer you are in the middle of. |
| `Help` | Shows the commands. |
| `Exit` | Leaves. Stored alarms are lost. |

Times look like `8:00 AM`. Dates look like `18-11-2026`. Press Enter at the weekday question to accept the suggested day.

## Limits

- At most 10 stored alarms, including finished ones.
- Overlapping future schedules are rejected. Monday 8:00 AM and Tuesday 8:00 AM can both exist. Daily 8:00 AM conflicts with Monday 8:00 AM.
- A new alarm is always placed in the future. Setting the clock exactly onto a pending alarm rings it.
- Moving the clock forward skips missed rings instead of playing them all.
- A finished alarm stays finished if the clock moves backward.
- No sound, no notifications from the operating system, and no saving to a file.

## Assistance

The behaviour record is `DECISIONS.md`. The code was written with AI assistance in Cursor, one reviewed piece at a time, and then completed in one pass so it could be demonstrated.
