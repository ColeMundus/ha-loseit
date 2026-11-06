# Installation and configuration

Read-only **custom integration**, not a Supervisor add-on.
Requires **Home Assistant Core 2026.10.0+**. Cookie setup/options were verified on
2026.10.0; offline tests target 2026.10.4. Other versions and long-duration session
behavior remain unverified.

## HACS custom repository

Version **0.1.0** is stable, but not in HACS's default catalog. With HACS already configured:

1. Open **HACS → ⋮ → Custom repositories**. Add
   `https://github.com/ColeMundus/ha-loseit`, select **Integration**, then **Add**.
2. Open **Lose It!** and choose **Download** to install the default stable release.
   For an installed copy use **⋮ → Redownload** first.
3. Restart HA and follow **Connect** below.

See HACS's [custom repository instructions](https://www.hacs.xyz/docs/faq/custom_repositories/).
HACS downloads the integration from repository source, not the manual ZIP.

## Manual installation

Download `loseit-0.1.0.zip` and `SHA256SUMS` from the
[0.1.0 release](https://github.com/ColeMundus/ha-loseit/releases/tag/v0.1.0).
Check the ZIP with `sha256sum --check SHA256SUMS` in the download directory.

1. Copy `custom_components/loseit/` into your HA configuration directory's
   `custom_components/` folder. Alternatively, extract the manual installation ZIP
   into the **configuration directory**.
2. Check that the result is `<config>/custom_components/loseit/manifest.json`, not
   a nested `custom_components/custom_components/` folder.
3. Restart HA, then connect below.

## Connect

1. Open **Settings → Devices & services → Add integration → Lose It!**.
2. Follow the [one-paste session guide](session-cookies.md): copy the **Cookie →
   Copy value** result from a signed-in website request into **Website session**.
   Keep the suggested timezone and submit. No JSON editing is needed.

Cookies grant account access. Paste them only into your own HA, never into issues,
chat or converters. HA stores them in configuration and potentially backups;
restrict access and encrypt backups. Health states may be retained in Recorder.
See [privacy and security](../SECURITY.md).

## Options and entities

Use **Configure** for the fallback timezone and polling interval (30–1440 minutes;
default 30). This interval is project policy, not a published vendor quota.
Timezone defaults to HA's setting; use an IANA name such as `America/Chicago`,
not `CST`. Only one entry per account is allowed.

Protein, carbohydrates, fat and logged food count are disabled by default; enable
them in the entity registry. Weight uses kg internally with HA unit conversion.
Entities describe the current diary day, not historical imports or new weigh-ins.

## Refresh and troubleshooting

- `homeassistant.update_entity` requests a shared refresh, subject to cooldowns.
- Sessions do not renew automatically. When HA requests reauthentication, repeat
  the [cookie-copy steps](session-cookies.md) for the **same account**; keep the entry
  and its entities. Reconfiguration also accepts a replacement session.
- For input, connection and account errors, see the [troubleshooting table](session-cookies.md#if-setup-fails).
- Unknown exercise/net/remaining values and day rollover are explained in
  [limitations](limitations.md).

For support, share the commit, HA version and sanitized error—not cookies, raw
logs, service responses, browser exports or health history.

## Removal

Delete the entry in **Settings → Devices & services**. To remove the code, remove
`<config>/custom_components/loseit` and restart. This does not revoke the website
session or erase Recorder history and backups.
