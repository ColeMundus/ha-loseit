# Known limitations

Experimental, read-only website integration—not an official Lose It! API client
or a stable app replacement.

| Area | Current boundary |
| --- | --- |
| Authentication | Existing website cookies only. No email/password login or automatic renewal; replace expired sessions manually for the same account. Session lifetime is unverified; human verification stays in the browser. |
| Website compatibility | Unofficial GWT protocol pinned to reviewed schemas. Unknown schemas fail closed and may require a code update. |
| Account access | Only reviewed reads are implemented, but cookies can grant broader account privileges. |
| Calories | Current-day budget and food calories require a matching source date. A missing date fails the read; it is not zero. |
| Exercise | Empty exercise arrays establish zero credit. Nonempty arrays leave exercise, net and remaining unknown; tracker/bonus credit semantics are unresolved. |
| Nutrients | Consumed-food protein/carbohydrates/fat only where complete. Missing data stays unknown; pending foods are excluded. |
| Weight | Day-effective source weight, not proof of a new measurement or verified carry-forward provenance. Goal weight is the returned goal, not a reconstructed historical goal. |
| Timezone | IANA fallback for HA day selection; the protocol reports a whole-hour account offset. Full DST, historical and fractional-offset behavior is unverified. |
| History/statistics | HA entities are current-day only; no backfill, historical Recorder import or account export. Editable daily totals are not monotonically increasing meters. |
| Unsupported | No food/weight writes, goal edits, water, fasting, full food-detail UI or nutrition advice. |
| Reliability | Long-duration session, restore and upgrade behavior remain unverified. See [tested versions](installation.md). |
| Distribution | Private preview, not available through HACS. Public validation and default-catalog inclusion are separate steps. |

Daily values become unavailable at rollover until a successful new-day read;
yesterday's totals are not presented as today's. Access challenges and connection
failures do not automatically mean the session has expired.

## Data and privacy

Recorder, dashboards, API consumers and backups may retain or expose health states.
Review entity/Assist exposure, retention and backup encryption. Disabling a sensor
does not erase history. Cookies, browser exports, raw logs and backups are not safe
to share; use only sanitized diagnostics. See [security policy](../SECURITY.md).
