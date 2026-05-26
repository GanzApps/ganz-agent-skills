# Changelog

## v6.0.0 (2026-05-27) — Major: Realtime + Generic Handlers

### Breaking Changes
- **Realtime subscription** now primary — agents get INSERT/UPDATE/DELETE events instantly
- **Polling fallback** if Realtime fails (every 30s)
- **All event types** handled — not just INSERT
- **Generic task handlers** — standard `TASK_HANDLERS` map instead of per-agent custom code

### New Features
- `blocked_by` column support — agents check before claiming
- `UPDATE` event handler — responds when blocked_by is cleared
- `DELETE` event handler — stops processing cancelled tasks
- `graceful shutdown` — marks current task pending on SIGTERM
- `skill_version` reporting — agents report `v6.0.0` on startup

### New Task Types
- `setup` — prerequisite/infrastructure tasks
- `general` — fallback for unknown types

### Standardized
- All handlers follow `handler(instruction, payload) -> dict` signature
- All Discord posts go to `source_channel` (no more ad hoc channels)
- Heartbeat gate enforced before any claim
- Environment variables — no hardcoded secrets

### Migration from v5
1. Update `SKILL_VERSION = "v6.0.0"` in worker
2. Replace polling loop with Realtime subscription
3. Add `TASK_HANDLERS` map
4. Update heartbeat: add `skill_version` field

---

## v5.0.0 (2026-05-18)

### Changes
- Source channel tracking — all tasks tagged with `source_channel`
- Job status → Working Agent thread `1504502974632820787`
- Agent heartbeat formalized

---

## v4.0.0 (2026-05-15)

### Changes
- Unblock mechanism added
- `agent_heartbeats` table created
- Task claim worker (every 2 min cron)

---

## v3.0.0 (2026-05-10)

### Changes
- Multi-agent coordination via Supabase
- Mr. Kim Realtime bridge
- Zenoa image/video specialist

---

## v1-v2 (Earlier)

- Initial Zeanna setup
- Basic task queue
