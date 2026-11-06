# Releasing

Publication and deployment require explicit approval; local ZIPs and CI artifacts
are not releases. Keep manifest/`pyproject.toml` versions identical, update
[CHANGELOG](../CHANGELOG.md) and compatibility notes. Tags use `vMAJOR.MINOR.PATCH`
with optional `aN`, `bN` or `rcN`; use a prerelease version for a preview.

## Checks and artifacts

Run the [contributor checks](../CONTRIBUTING.md#development), then:

```sh
uv run --locked python scripts/package.py --check
uv run --locked python scripts/release_metadata.py v0.1.0
uv run --locked python scripts/package.py artifacts/loseit-0.1.0.zip
(cd artifacts && sha256sum --check SHA256SUMS)
```

`0.1.0` matches current metadata; it is not a claim of publication. The allowlisted
ZIP extracts to `custom_components/loseit/` with branding and license notices.
HACS downloads repository source; do not enable `zip_release` for this nested ZIP
without separately verifying extraction compatibility.

## Before publication

- Audit the full source/history, including author/committer metadata, for private
  data. Keep credentials, health values and authenticated captures outside the
  repository and artifacts; CI fixtures must be synthetic.
- Verify the documented installation, restart, same-account reauthentication,
  upgrade and restore under separate deployment authorization. Preserve cookies,
  options and account/entity IDs; legacy metadata must not trigger sign-in.
  Offline tests alone do not establish installed/provider behavior.
- Do not log out, rotate, force expiry or intentionally invalidate working access
  for testing. Sessions are manually imported; renewal is not automatic.
- HACS requires a public repository and validation without ignores before claiming
  acceptance. Default-catalog inclusion is separate; do not change visibility
  merely to pass validation.
- Preserve MIT/upstream and proprietary-brand notices. Artwork/service-rights
  review was skipped, not completed; no permission claim is implied.
- Configure actual required reviewers on the `release` environment and protect
  tags against updates. Naming an environment in YAML is not approval enforcement.

## GitHub workflows

`Validate` runs lint, typing, offline tests/90% coverage, packaging and hassfest.
HACS skips while private; that is not acceptance. Reports/artifacts last 14 days.
Tag pushes validate/build only. With an approved tag at the tested commit:

```sh
# Validate/build only:
gh workflow run release.yml --ref v0.1.0 -f publish=false
# Publish only after explicit release approval:
gh workflow run release.yml --ref v0.1.0 -f publish=true
```

Only the manual publishing job has write permission. It checks versions and the
remote tag's resolved commit before/after creation, refuses existing releases and
verifies downloaded asset bytes/checksums. Prerelease status follows the version;
releases are not automatically marked latest.

Tag checks and creation are not atomic: immutable tags remain necessary. A
postpublication mismatch fails without deleting the release. Independently verify
installation from the published route. Release-note categories are in
`scripts/release-notes.yml`; current [limitations](limitations.md) still apply.
