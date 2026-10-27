---
type: Decision
title: GUI Cancel and Quit stop the whole pipeline process tree
description:
  The desktop launcher runs the pipeline as its own process group and stops the
  group, any detached descendants and any late-born members, escalating to
  SIGKILL after 5 s; a cancelled run is reported as incomplete, not deleted.
tags: [gui, cancellation, p0, milestone-4]
generated: { by: agent/richard-claude-code, at: "2026-10-27T16:10:00Z" }
status: draft
---

## Scope and status

This note records decisions for the desktop launcher (`tools/roap_app.py`,
`tools/roap_app_core.py`) made under P0 issue
[#12](https://github.com/uw-ssec/roap/issues/12) and implemented in
[#70](https://github.com/uw-ssec/roap/pull/70). It stays `draft` until #70
merges. It was agreed during Richard/Dinesh cross-review on 2026-10-26, with
end-to-end testing by Gilfoyle.

## The problem it fixes

Cancel sent SIGTERM only to `bash`. The papermill child was reparented to PID 1
and ran its stage to completion, so a "cancelled" run left stage output that
looked complete (`oa_stage2_outputs/data/enhanced.csv` was written after the
cancel). Quit and closing the window had no handler, so the whole pipeline kept
running with no window.

## Decisions

1. **Launch as a process group.** POSIX uses `start_new_session=True`; Windows
   uses `CREATE_NEW_PROCESS_GROUP`. Cancel, Quit and window-close all stop the
   run through one function, `stop_process_tree`.
2. **Stop the group and its detached descendants.** POSIX sends `killpg(SIGTERM)`
   and also SIGTERM to every descendant in a `ps` snapshot taken first. The
   snapshot is required because jupyter_client starts each kernel in its own
   session, outside the group, so `killpg` alone leaves the kernel running.
   Windows uses `taskkill /T /F`.
3. **Escalate to SIGKILL after `STOP_GRACE_SECONDS` (5 s).** The wait runs on a
   non-daemon thread, which keeps Tk responsive and still completes after Quit
   destroys the window. It ends early only when bash is reaped, the original
   process group is empty and no snapshotted descendant is alive. The group
   check catches members born after the snapshot, for example one started by a
   SIGTERM handler; the snapshot catches the kernels that left the group.
4. **Warn instead of deleting.** After a cancel, the status line and log say
   *"Cancelled. Outputs in <out_dir> are incomplete and must not be used."*
   Deleting the in-flight stage folder would mean the app guessing an `rm -rf`
   target inside a path the user chose, so it is not done.
5. **Confirm before quitting a running pipeline.**

## Verification

- Mutation checks: reverting to `proc.terminate()`, dropping the descendant
  sweep, dropping SIGKILL, making the thread a daemon, joining it on the main
  thread, or dropping the group check each fail the tests meant to catch them.
- A real pipeline cancelled about 10 s into a run stopped mid-notebook with exit
  -15 and no surviving papermill, ipykernel or `run_pipeline.sh` process, and
  wrote nothing after the cancel (macOS 15, verified independently by Richard,
  Dinesh and Gilfoyle).

## Known limits

- The survivor tests are POSIX-only. On Windows only the dry-run click runs in
  CI, so the `taskkill` path has no survivor evidence.
- A dry run still leaves an empty output folder, created by
  `run_pipeline.sh`'s `abs_dir_create`. That is outside the launcher.
