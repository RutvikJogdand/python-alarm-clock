# Python Alarm CLI — DECISIONS.md

Planning document · 17 November 2026 · Prepared with AI assistance before writing the fresh Python application.

## 1. Instructions for Cursor

The goal is a small application whose behaviour and code I can explain. I am still learning Python.

- **Do not generate the whole application.** Work on one small, reviewable increment at a time.
- `R` rules below are confirmed user decisions. `P` defaults and the technical plan are proposals: explain and obtain my approval before implementing the affected part.
- Before each increment, name its purpose, affected functions/data, and the behaviour its tests will check.
- After the change, explain every added or changed line, including unfamiliar Python syntax. Show how to run it and what to expect.
- **Wait for my approval before the next increment.** Passing tests does not replace my review.
- Search for existing validation before adding a validator. Adding and editing must reuse the same rules.
- Keep each change focused. Do not add features, dependencies, abstractions or unrelated refactors without discussing them.
- Update the function/data inventory when a reviewed change introduces or renames something. Do not invent a complete list of future temporary variables.
- Derive test expectations from these decisions and examples, not merely from what the implementation currently does.
- Keep actual commits for reviewed changes. Report checks as passed only after running them.

First response after reading this file: summarise the confirmed rules, identify which proposals affect increment 1, and explain that increment. Do not write application code in that first response.

## 2. Scope and limits

- Fresh Python command-line application. No React, web server or database.
- Multiple alarms; one-time, daily and selected-weekday schedules.
- An editable application clock. Changing it must not change the computer's clock.
- The assignment describes a 30-minute build exercise and asks to see requirements/design thinking and a narrated build recording. This plan does not claim the work fits that timebox or that a recording already exists.
- Persistence is optional: the user requested it only if reasonably simple. See P8. Snooze, calendar-date scheduling, operating-system notifications and background operation after exit are not part of the current agreed scope.
- The app must be running for it to ring. Running while the computer is asleep, surviving a shutdown and guaranteed audible sound require additional mechanisms; do not promise them.

## 3. Confirmed behaviour

| ID | Decision | Reason / consequence |
| --- | --- | --- |
| R1 | Store at most 10 alarms, including finished alarms. | The limit counts stored records, not only upcoming alarms. |
| R2 | Enter alarm times in a 12-hour clock with AM/PM; reject invalid values such as `-11:40 PM`. | Invalid input must not create or change an alarm. |
| R3 | Offer ring once or repeat. Repeating can be daily or on selected weekdays. | Selected days mean weekdays, not arbitrary calendar dates. |
| R4 | A new alarm's default first occurrence must be strictly in the future. A later time means today; an equal or earlier time means tomorrow. | Creating an alarm at the current time must not ring it immediately. |
| R5 | A one-time alarm may use the default day or a different upcoming weekday. | It rings once, even when its weekday is chosen explicitly. |
| R6 | For repeat, present the default starting weekday and allow selection of additional weekdays. | Daily repetition covers all seven weekdays. Removing the default is still proposal P1. |
| R7 | Reject overlapping future ringing schedules. Monday 8 AM and Tuesday 8 AM may coexist; daily 8 AM conflicts with Monday 8 AM. Finished alarms do not block schedules. | Compare complete schedules, not only the next occurrence. |
| R8 | Users may edit/delete alarms before ringing or after they finish, but not while they are ringing. | Recheck the state when an edit is saved, since it may have started ringing during input. |
| R9 | STOP ends the ringing state. | The exact command and repeat-after-STOP behaviour are specified as proposal P2. |
| R10 | Show all alarms so the user can select one to edit/delete. | Stable IDs are proposal P3. |
| R11 | When there are no stored alarms, show the message below. | A collection containing only finished alarms is not empty. |
| R12 | The app does not automatically adjust for timezone changes. The user corrects its clock and can inspect the effect on alarms. | Show each next occurrence and how far away it is. A weekday schedule needs a current date as well as a time. |
| R13 | If a manual forward clock change passes a pending one-time alarm, move it to its next matching weekday/time. It remains a one-time alarm. | Preserve the chosen weekday/time without ringing the skipped occurrence. |
| R14 | After a forward clock jump passes a repeating occurrence, use the next future selected weekday/time. | Do not ring skipped occurrences as a batch. |
| R15 | If a manual clock change lands exactly on an existing pending alarm, ring immediately. | This differs deliberately from creating a new alarm at the current time, covered by R4. |
| R16 | Finished alarms remain finished when the clock moves backward. Explicitly editing their schedule can reactivate them. | A clock correction alone must not revive completed alarms. |

Empty-state message:

> No alarms set. If you want to set a alarm type: Set alarm

### Examples to keep in the tests

| Situation | Expected result |
| --- | --- |
| Monday 8 AM; create 8 AM, once, accept default day | Tuesday 8 AM, once. |
| Monday 8 AM; create 8 PM, once, accept default day | Monday 8 PM, once. |
| Monday 8 AM; create 8 PM, once, choose Friday | Upcoming Friday 8 PM, once. |
| Monday 8 AM; repeat 8 PM on Monday and Thursday | Monday and Thursday at 8 PM each week. |
| Monday 7 AM; pending once alarm Monday 8 AM; set clock to Monday 9 AM | Next Monday 8 AM, still scheduled and still once. |
| Monday 7 AM; pending once alarm Monday 8 AM; set clock to Monday 8 AM | Start ringing immediately. |
| Completed once alarm Monday 8 AM; move clock back to Monday 7 AM | Remains finished. |

## 4. Proposed defaults — review before the affected increment

These are recommendations, not additional decisions already made by the user.

| ID | Proposal | Why it is needed |
| --- | --- | --- |
| P1 | The default repeat weekday is preselected but removable. Require at least one weekday. | A user should be able to choose a schedule that excludes today/tomorrow. |
| P2 | Use `STOP <id>` to stop a particular alarm. A once alarm becomes finished. A repeating alarm schedules its next selected occurrence strictly after the stop time; skip occurrences that passed while it was ringing. | Different alarms can remain ringing simultaneously, even when their scheduled start times differ. |
| P3 | Use increasing positive integer IDs. Never renumber remaining alarms after deletion. | An existing command or selection must not start referring to another alarm. |
| P4 | Initialise the app clock from the computer's local date/time once at startup. Advance it using elapsed time; later computer timezone changes do not adjust it automatically. Accept a date and time for manual correction. | Keeps weekday calculations meaningful and isolates the editable app clock. |
| P5 | On a backward clock change, retain a pending once alarm's scheduled date. For repeating alarms, never replay an occurrence already triggered; search after both the corrected time and the last triggered occurrence. | Prevents duplicate ringing after a clock correction. R16 already covers finished alarms. |
| P6 | Preview a clock change before applying it. Reject it if rescheduling creates a conflict, showing affected IDs. Require ringing alarms to be stopped first. Revalidate at confirmation if state changed during review. | Clock changes can create collisions or otherwise bypass the edit restriction. |
| P7 | **Approved 18 Nov 2026**, with one replacement: clock dates are `DD-MM-YYYY`. Otherwise unchanged: accept `8:00 AM` and `08:00 AM`, trim outer spaces, and accept lowercase AM/PM. Require minutes and AM/PM; reject extra text. | Defines exactly what the parser accepts. Midnight is 12 AM; noon is 12 PM. Date text is for `parse_clock_datetime` later; increment 1 parses time only. |
| P8 | Build and review the in-memory core first. Add JSON persistence only in a separately approved increment if time permits. | Loading overdue/ringing alarms, bad files and failed saves need explicit behaviour. Until then, exit loses stored alarms. |
| P9 | Print a notification once when an alarm enters ringing, and keep it in that state until STOP. Do not spam the terminal every second. | State and notification frequency are separate. Audible output is not required for this proposed version. |
| P10 | Commands are case-insensitive. Invalid input leaves stored alarms unchanged; a form can be cancelled. STOP remains available while entering an alarm. | Input handling must remain usable while time advances. |

Do not silently turn these proposals into confirmed rules. Record approval or the chosen replacement alongside the affected item.

## 5. Proposed files and execution approach

| File | Responsibility |
| --- | --- |
| `alarm.py` | Alarm data, clock calculations, validation, scheduling and state changes. No terminal input/output. |
| `cli.py` | Commands, prompts and display; calls the rules in `alarm.py`. |
| `tests/test_alarm.py` | Rules and scheduling tested with controlled times. |
| `tests/test_cli.py` | Command routing, invalid input, STOP while entering data, and exit behaviour. Add with the CLI increment. |
| `README.md` | Setup, commands, limitations, actual checks and AI assistance. |
| `DECISIONS.md` | This decision record and the evolving implementation inventory. |

Use Python's standard library first. Record the Python version actually tested. Proposed run commands are `python cli.py` and `python -m unittest discover -s tests -v`.

Python version tested: 3.13.1. `python -m unittest discover -s tests -v` passed on 18 Nov 2026 for `parse_time`, `default_weekdays`, and `next_occurrence`.

**Input must not freeze alarms.** Proposed approach: one background reader puts terminal input into a queue; the main loop alone owns and changes alarm/clock state. It checks alarms while waiting for input. A queue is a thread-safe inbox. Explain this approach before implementing it; do not add threads that independently mutate alarms.

A partly entered alarm is only a draft. Creating, editing or correcting the clock applies a complete validated change. An error must not leave half the change saved.

## 6. Planned function inventory

These describe responsibilities. Introduce a function only when its increment needs it. Explain any split, merge or rename before changing this inventory.

Existing after review: `parse_time` and `TIME_INPUT_PATTERN` (increment 1). This scheduling patch adds `default_weekdays` and `next_occurrence`. `parse_weekdays` is still planned; the weekday text format is not approved yet.

| Function | Inputs → result / effect |
| --- | --- |
| `parse_time` | Text → `(hour_24, minute)` or an understandable input error. Shared by create, edit and clock input. Exists in `alarm.py`. |
| `default_weekdays` | Hour, minute and a reference date/time → a set containing one weekday number. A later clock time uses the reference date. An equal or earlier clock time uses the next date. This is the R4 default day, kept separate from `next_occurrence` so a chosen weekday can be passed in on its own. |
| `parse_weekdays` | Text → a non-empty set of weekday numbers, or an input error. Not written yet. |
| `parse_alarm_id` | Text → positive integer ID. Reject partial numbers such as `2junk`, negatives and fractions. |
| `parse_clock_datetime` | Date text + time text → app date/time; reuse `parse_time`. Reject impossible dates. |
| `next_occurrence` | Time, allowed weekdays and a reference date/time → earliest matching occurrence strictly after the reference. Exists in `alarm.py`. |
| `find_conflict` | Candidate schedule, stored alarms, optional ID to exclude → conflicting ID or no conflict. Ignore finished alarms; inspect recurrence overlap. |
| `read_app_time` | Clock reference + current elapsed-time reading → current app date/time. Does not mutate alarms. |
| `save_alarm` | Draft + optional edited ID + current app time → validated alarm. Enforce capacity, schedule conflicts and edit restrictions together. |
| `delete_alarm` | ID → remove an existing non-ringing alarm or return an error. |
| `stop_alarm` | Ringing ID + current app time → finished once alarm or next repeating occurrence, subject to P2 approval. |
| `process_due_alarms` | Current app time → move scheduled due alarms into ringing; return IDs to notify. Never trigger a ringing alarm repeatedly. |
| `plan_clock_change` | New app date/time + current state → preview, rescheduled candidates, due-now IDs and any conflicts. No committed changes. |
| `apply_clock_change` | Reviewed clock plan + latest state → apply all valid changes together, or reject and explain. |
| `format_alarm_list` | Alarms + current app time → display text, including IDs, states, weekdays, next times and time remaining. |
| `handle_input` | Input line + dialog state → command/answer handling. Call shared rules; do not reimplement scheduling here. |
| `read_input` | Input queue → enqueue lines/end-of-input. Never change alarms or the app clock. |
| `main` | Start reader and main loop, check due alarms, handle queued input, and exit cleanly. |

Rule placement: parsing handles input syntax; scheduling chooses occurrences; conflict checking detects overlap; save/delete/stop enforce state rules; the CLI only gathers input and presents results.

## 7. Planned data, variables and constants

Start with a simple alarm record. Whether to use a dictionary or a small Python data class is an implementation proposal to explain before coding.

| Alarm field | Purpose |
| --- | --- |
| `id` | Stable positive identifier, subject to P3. |
| `hour_24`, `minute` | Internal time; display remains 12-hour. For example, 8 PM becomes hour 20 internally. |
| `mode` | `once` or `repeat`; daily repetition uses all seven weekdays. |
| `weekdays` | Selected weekday numbers. A once alarm has its chosen weekday so a forward jump can move it to the next matching day. |
| `state` | `scheduled`, `ringing` or `finished`. |
| `next_due_at` | Concrete date/time of the next occurrence. Retain the occurrence while ringing; use no next occurrence when finished. |
| `last_triggered_occurrence` | Scheduled occurrence most recently triggered, not the time STOP was pressed. Used for proposed backward-clock protection. Reset only for an explicit new schedule, never merely because the clock changed. |

| Shared / loop data | Purpose and owner |
| --- | --- |
| `alarms_by_id` | Dictionary of all stored alarms, including finished ones. Main loop owns changes. |
| `next_alarm_id` | Next unused ID; main loop advances it after a successful creation. |
| `base_app_datetime` | App date/time at startup or the latest accepted clock correction. |
| `base_monotonic_seconds` | Matching elapsed-time reference. Together with the previous field, produces advancing app time. |
| `command_queue` | Inbox written by the input reader and consumed by the main loop. |
| `input_thread`, `running` | Reader handle and main-loop running flag. No other shared mutation thread. |
| `dialog` | Which prompt is active and the answers gathered so far. |
| `draft`, `pending_clock_plan` | Uncommitted alarm input or clock-change preview; discard on cancellation/error. |
| `now`, `candidate`, `conflict_id` | Local values for one operation: a time snapshot, a proposed record and a conflicting ID. They are not extra sources of stored state. |

| Constant / collection | Proposed value or purpose |
| --- | --- |
| `MAX_ALARMS` | `10`, confirmed in R1. |
| `CHECK_INTERVAL_SECONDS` | `1`; approximate checking interval, not a guarantee of precise real-time delivery. |
| `WEEKDAY_NAMES` | Monday through Sunday, mapped to 0 through 6. |
| `VALID_MODES`, `VALID_STATES` | The mode and state values listed above. |
| `TIME_INPUT_PATTERN` | One shared definition of the accepted time syntax from approved P7. |
| `EMPTY_ALARMS_MESSAGE` | The exact empty-state message in section 3. |

Do not store duplicate counts, display strings or countdowns that can be derived from this data. No file path/save flags are needed until persistence is approved. Introduce other temporary variables only when needed and explain each in the increment review.

## 8. Proposed command interface

| Command | Behaviour |
| --- | --- |
| `Set alarm` | Ask time, once/repeat, and day(s); explain the default first occurrence before saving. |
| `Show all alarms` | Show the stored alarms and their IDs, including finished alarms. |
| `Edit <id>` / `Delete <id>` | Operate on the selected non-ringing alarm. |
| `STOP <id>` | Stop that ringing alarm, subject to P2. |
| `Set clock` | Ask app date/time and show proposed alarm changes, subject to P6. |
| `Cancel` | Discard the current input draft; do not stop alarms. |
| `Help` / `Exit` | Show commands / leave cleanly, explaining the in-memory limitation. |

Display the app's current date/time with the alarm list. During an input dialog, STOP must still work and clock checking must continue. On an edit, validate the latest alarm state when saving, not only when the dialog opens.

## 9. Verification checklist

These are planned checks, not passing-test claims. Test proposal-dependent expectations only after that proposal is approved.

| Area | Cases to verify |
| --- | --- |
| Time input | Valid 1–12 hours and 00–59 minutes; midnight/noon; reject negative hours, 0/13, minute 60, missing AM/PM and trailing junk. Check approved spacing/case rules. |
| Defaults | Every example in section 3; include times just before/after midnight and exactly equal to now. |
| Weekdays | Once on an upcoming chosen day; weekly wraparound; all seven days; empty/invalid weekday selection. |
| Conflicts | Same date/time rejected; different days allowed; daily-versus-weekly overlap detected even when next occurrences differ; finished alarms ignored; an edit excludes its own ID. |
| Capacity | Ten stored alarms allowed; eleventh rejected even if all ten are finished; editing does not consume a slot; deletion frees one. |
| IDs | Unknown, negative, fractional and partly numeric IDs rejected; deleting one does not renumber others under P3. |
| States | Cannot edit/delete ringing alarms; rejected edit leaves original intact; STOP affects the chosen alarm; completed once alarms can be explicitly rescheduled. |
| Clock forward | Exactly due rings; strictly passed once alarm moves to next matching weekday; repeats skip past occurrences; multiple-week jumps work. |
| Clock backward | Finished alarms stay finished; verify approved P5 behaviour for pending/repeating alarms. |
| Clock conflicts | A once alarm rolling to next Monday may collide with another alarm already there. Verify approved P6 policy with no partial clock/alarm changes. |
| Responsiveness | Alarm becomes due while user is entering/editing; checks and STOP still work; final save rechecks ringing state. |
| Notifications / exit | No duplicate trigger notification per occurrence; empty-state wording; Cancel, end-of-input and Ctrl+C do not produce an unhandled traceback. |

Pass explicit test times or substitute the clock-reading function. Tests must not wait until a real alarm minute arrives. Verify the actual CLI path as well as isolated functions.

## 10. Reviewable implementation order

Each row is a milestone to divide into small patches, not permission to implement the entire row at once.

1. Input-format proposal approved 18 Nov 2026; clock dates are `DD-MM-YYYY`. Implement only `parse_time` and its focused tests. Explain every line and wait.
2. Scheduling patch: `default_weekdays` and `next_occurrence`, with default-day and weekly-boundary tests. `parse_weekdays` waits for an approved weekday text format. Wait.
3. Add the alarm record, IDs, capacity, conflict checking and save/delete operations in separate reviewed patches. Wait.
4. Add the app clock, due transitions, STOP and manual clock-change planning/applying, approving P2/P4/P5/P6 as needed. Wait after each patch.
5. Add CLI commands and non-blocking input handling. Test an alarm firing while a dialog is open. Wait.
6. Run the complete agreed checks, update README limitations and actual results, then prepare the walkthrough using the real commits.
7. Consider persistence only after the core is understood and reviewed. First decide restart/catch-up behaviour, clock restoration, invalid-file handling and failed-save recovery; then update this document before adding code.

Do not race through these milestones to claim completion within 30 minutes. Keep the actual work and recording honest, and document unfinished scope.

