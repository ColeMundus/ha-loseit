# Changelog

## 0.1.0b1 — public beta

First beta preview, not a stable release. HACS custom-repository and manual ZIP
installation; not included in the default HACS catalog.

### Added

- Native read-only Lose It! config flow, reauthentication and configuration.
- Shared polling coordinator, request cooldowns and allowlisted diagnostics.
- Source-date-verified calorie, nutrient and diary-day weight sensors.
- Synthetic pure-client tests, real Home Assistant harness tests and CI validation.
- Installation archive tooling, project licensing, contributor/security policies,
  and distribution preparation.

### Fixed

- Setup, reauthentication, reconfiguration and options form serialization for the HA frontend.
- Invalid timezone input now returns a readable form error.

### Known limitations

Manual website-session cookies, no unattended renewal, unverified nonempty
exercise-credit semantics, no writes or historical Recorder import. See
[limitations](docs/limitations.md).
