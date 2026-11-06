# Contributing

Experimental, read-only custom integration. Open an issue for substantial changes.
Bug fixes, synthetic tests and documentation are welcome. Do not add account writes
or automated credential acquisition as incidental cleanup: authentication is manual
website-session import, without password login or automatic renewal.

## Development

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then:

```sh
git clone https://github.com/ColeMundus/ha-loseit.git
cd ha-loseit
uv sync --locked
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy custom_components/loseit
uv run --locked pytest --cov=custom_components/loseit --cov-branch --cov-report=term-missing
uv run --locked python scripts/package.py --check
git diff --check
```

Python/HA harness versions are pinned in `pyproject.toml` and `uv.lock`;
resolve Python, HA and aiohttp compatibility together.
See [releasing](docs/releasing.md) for artifact and publication commands.

## Compatibility and tests

Read the [glossary](GLOSSARY.md) and [architecture](docs/architecture.md).
Keep protocol logic independent of HA, entity properties free of I/O and refreshes
shared through the coordinator/request gate. Preserve stored keys, entry versions
and account/entity IDs unless an explicitly tested migration is required. Keep
`strings.json` and `translations/en.json` synchronized.

- Add a failing synthetic regression, fix it, then run relevant tests and full checks.
- `tests/client` covers decoding/projections; `tests/ha` exercises real HA interfaces
  with mocked provider I/O. Routine tests block external networking; do not weaken
  this restriction. Local loopback fixtures are intentionally allowlisted.
- Preserve missing/zero distinctions, source dates, conservative polling, bounded
  parsing and verified-expiry versus generic access-error handling.
- Test shared cookie forms through translated frontend-schema serialization;
  same-account replacement must preserve exact entries on failure/cancellation.
  Legacy username/method metadata stays inert; cooldown applies before validation.

## Privacy and review

Real-account checks require separate authorization and stay outside the repository.
Never commit cookies, health values, emails, account IDs, browser exports, HARs,
backups or authenticated responses, or paste them into PRs/Actions. Do not log raw
responses or chain sensitive transport exceptions; test redaction with invented
canaries. Offline tests are not live provider or installed acceptance.

Keep PRs focused and report actual tests, behavior changes and limitations. Preserve
upstream notices; new code is contributed under the [MIT license](LICENSE).
Dependency updates require the same checks and review; they are not auto-merged.
Report vulnerabilities via [SECURITY.md](SECURITY.md), not public issues.
