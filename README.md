![Official Lose It! app icon](custom_components/loseit/brand/icon.png)

# Lose It! for Home Assistant

[![CI: workflows](https://img.shields.io/badge/CI-workflows-blue.svg)](https://github.com/ColeMundus/ha-loseit/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Tested HA: 2026.10.0](https://img.shields.io/badge/Tested_HA-2026.10.0-blue.svg)](docs/installation.md)
[![Status: experimental preview](https://img.shields.io/badge/Status-experimental_preview-orange.svg)](docs/limitations.md)

Native, **read-only** Lose It! diary sensors for Home Assistant. This is a custom
integration, not a Supervisor add-on; no extra container is needed.

## Sensors

- Current-day calorie budget and food calories.
- Exercise, net and remaining calories when exercise credit is established.
- Protein, carbohydrates, fat and consumed-food count (optional, disabled by default).
- Diary-day weight, goal weight, source diary date and last successful refresh.

One shared refresh runs every 30 minutes by default. No food/weight logging,
goal changes, water, fasting or historical import is included.

## Install and connect

Requires **Home Assistant Core 2026.10.0+**. This preview is private: you need
repository access or a maintainer-provided manual installation ZIP. It is not
available through HACS or approved for its default catalog.

1. Copy `custom_components/loseit/` into your HA configuration's
   `custom_components/` directory, or extract the manual ZIP into the configuration directory.
2. Restart HA → **Settings → Devices & services → Add integration → Lose It!**.
3. In your signed-in Lose It! desktop browser, open **Developer tools → Network**,
   refresh, select a website request, then **Headers → Request Headers → Cookie →
   Copy value**. Paste into HA's **Website session**, keep the timezone and submit.

[One-paste guide with screenshots](docs/session-cookies.md) · [Installation and options](docs/installation.md)

## Know before connecting

- Cookies are sign-in credentials. Paste only into your own HA; renewal is manual.
- HA configuration/backups can contain credentials; Recorder can retain health data.
- Nonempty exercise entries currently leave exercise/net/remaining calories unknown.
  Diary-day weight is not proof of a new weigh-in. Missing data is not zero.
- The unofficial website protocol can change. See [limitations](docs/limitations.md)
  and [privacy and security](SECURITY.md).

[Support](https://github.com/ColeMundus/ha-loseit/issues/new/choose) · [Contributing](CONTRIBUTING.md) · [Changelog](CHANGELOG.md)

Code is [MIT licensed](LICENSE), with [upstream notices](THIRD_PARTY_NOTICES.md).
Official artwork and trademarks remain their owners' property; see the [branding notice](custom_components/loseit/brand/NOTICE.md). No affiliation or endorsement by Lose It!, FitNow, Inc. or Home Assistant.
