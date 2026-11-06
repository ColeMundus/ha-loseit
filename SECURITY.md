# Security policy

## Support and threat model

The `main` branch is an experimental preview, not a stable security-supported
release line. Best-effort fixes target current `main`; there is no guaranteed
response time or support for arbitrary older commits.

Website cookies are bearer credentials. They authorize access to personal health
information and may authorize more actions on the service than this integration
implements. Read-only code does not reduce the privileges of a stolen cookie.

Home Assistant stores the supplied session in its configuration storage. This
integration does not provide an additional encryption layer. Anyone with access
to HA storage or backups may obtain it. Health sensor states can also be stored
by Recorder, exposed through dashboards/APIs and included in backups. Restrict
access, review entity exposure and use encrypted backups.

## Reporting a vulnerability

Do **not** post credentials, exploit details that expose accounts, health data,
raw responses, HAR files or backups in a public issue.

Use GitHub's **Security → Advisories → Report a vulnerability** when private
vulnerability reporting is enabled. If that option is unavailable, contact
[@ColeMundus](https://github.com/ColeMundus) through an available private contact
method on the maintainer's profile. If no private channel is available, open an
issue saying only **“Private security contact requested”** and wait for a private
channel; do not disclose the vulnerability there.

Include the affected commit/version, a synthetic reproduction, potential impact
and suggested remediation. Do not test against another person's account. If a
session is exposed, remove it from shared material and revoke/sign out the session
through the service where supported; removing a GitHub comment alone does not
invalidate a copied credential.

## Release boundaries

The project's license does not imply authorization from the service provider.
No public service endorsement, unattended renewal or security certification is
claimed. See [known limitations](docs/limitations.md) before installation.
