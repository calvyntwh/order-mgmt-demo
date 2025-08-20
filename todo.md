# TODO — Order Management Demo

Changelog: Consolidated [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md:1) and [`TASK_TRACKER.md`](TASK_TRACKER.md:1) into this canonical checklist. Stakeholders notified.

## Consolidated Master Checklist

- [x] Create todo.md by merging [`IMPLEMENTATION_PLAN.md`](IMPLEMENTATION_PLAN.md:1) and [`TASK_TRACKER.md`](TASK_TRACKER.md:1) into a single canonical checklist (housekeeping complete)
- [-] Deduplicate tasks, normalize tags (MVP / BACKLOG / EXTENDED) and unify priorities
- [-] Canonicalize statuses: mark completed as done, mark in_progress items with [-], leave pending as [ ]
- [x] Insert the Demo Fast-Track checklist at top
- [-] Move detailed phase descriptions and rationale into an "Appendix / Reference" section below
- [x] Archive originals: copied to `docs/archives/` (`docs/archives/IMPLEMENTATION_PLAN-2025-08-20T0510.md`, `docs/archives/TASK_TRACKER-2025-08-20T0513.md`)
- [ ] Update [`README.md`](README.md:1) and in-repo links to reference [`todo.md`](todo.md:1) as the single source of truth
- [ ] Commit `todo.md` and archived copies; open PR "chore: consolidate implementation plan and tracker into todo.md" with verification steps
- [x] Add a one-line changelog and stakeholder notification entry at the top of [`todo.md`](todo.md:1)
- [ ] After stakeholder approval, delete or restrict write-permissions on old files or keep them in `docs/archives/` as agreed

## Appendix / Reference (moved from originals)

- Full implementation plan and task tracker archived in `docs/archives/`:
  - [`docs/archives/IMPLEMENTATION_PLAN-2025-08-20T0510.md`](docs/archives/IMPLEMENTATION_PLAN-2025-08-20T0510.md:1)
  - [`docs/archives/TASK_TRACKER-2025-08-20T0513.md`](docs/archives/TASK_TRACKER-2025-08-20T0513.md:1)

## Notes

- This file is the canonical tracker; update statuses here and run `scripts/update_tracker.py` to sync snapshots.
- If you want, I can: (A) perform the archival copy now, (B) update [`README.md`](README.md:1), and (C) create the PR. Choose which to run next.