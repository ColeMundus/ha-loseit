<img src="custom_components/loseit/brand/icon.png" alt="Official Lose It! app icon" width="64" height="64">

# Lose It! for Home Assistant

[![CI: workflow](docs/badges/ci.svg)](https://github.com/ColeMundus/ha-loseit/actions/workflows/ci.yml)
[![HA tested: 2026.10.4](docs/badges/compatibility.svg)](docs/installation.md)
[![License: MIT](docs/badges/license.svg)](LICENSE)
[![Distribution: HACS custom](docs/badges/distribution.svg)](docs/installation.md#hacs-custom-repository)

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

Requires **Home Assistant Core 2026.10.0+**. Version **0.1.1** is a stable release
for HACS custom-repository installation, not in the default catalog.

1. In **HACS → ⋮ → Custom repositories**, add
   `https://github.com/ColeMundus/ha-loseit` as **Integration**, then download Lose It!.
   Use the default stable release.
   Or extract the release's manual ZIP into your HA configuration directory.
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
