# Architecture

The runtime is self-contained under `custom_components/loseit`.

| Module | Responsibility |
| --- | --- |
| `__init__.py` | Config-entry setup, runtime data and unload |
| `config_flow.py` | Shared session form, same-account replacement and options |
| `coordinator.py` | Shared refresh and current-day freshness |
| `request_gate.py` | HA-lifetime account/session cooldown across flows and runtime |
| `sensor.py` | Entity metadata and presentation; no I/O in properties |
| `diagnostics.py` | Allowlisted diagnostic output |
| `client.py` | Read-only website transport/public API; caller-owned aiohttp session |
| `models.py` | Frozen models and safe typed errors |
| `schemas.py` | Pinned signatures and read layouts |
| `gwt.py` | Bounded JSON-only GWT decoding |
| `protocol.py` | Identity parsing and reviewed daily-read request encoding |
| `snapshot.py` | Source-date validation and metric projection |

One coordinator fetches the current diary day and shares an immutable snapshot.
The client is independent of HA and creates no session or background task.
Public imports, configuration keys and entity IDs are compatibility boundaries.
Source dates must match before projection; missing values remain unknown, pending
foods are excluded and exercise credit is not guessed. See [limitations](limitations.md).

## Authentication and lifecycle

Setup, reauthentication and reconfiguration share one manually supplied cookie
form and [guide](session-cookies.md). No password login, sign-in requests or automatic
renewal exist. Bootstrap reads `https://www.loseit.com/` to validate account identity.
Cookie names/values are preserved; whole-header import stores only supported
session cookies, not raw input or unrelated cookies. Timezone settings are stored
with the entry/options.

Legacy cookies work without migration or forced sign-in; historical `username`
and `auth_method` metadata are inert. Failed/cancelled replacement preserves exact
entry data, options and entity identities. Successful replacement requires the
same account, updates effective timezone and preserves polling/account/entity IDs.

The request gate checks session/known-account cooldown before identity validation,
including reopening flows, refresh and reload. Replacement cooldown lives in
HA-lifetime private state without changing the existing entry; older persisted
runtime cooldowns are honored. Fingerprints are never persisted or diagnosed.
Only verified expiry triggers reauthentication; access/schema/connection failures
do not discard credentials. Requests/parsing are bounded, redirects are disabled,
and credentials or raw responses must never be logged.

Tests exercise the pure client and real HA lifecycle with synthetic provider I/O.
Archive tests verify importability without development files. Adapted schemas
retain the [upstream MIT notice](../THIRD_PARTY_NOTICES.md).
