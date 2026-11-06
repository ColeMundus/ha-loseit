# Third-party notices and provenance

## phitoduck/lose-it — adapted schema catalog

The exact domain-signature/read-layout catalog and known array signatures are
adapted from `_schemas.json` in
[phitoduck/lose-it at fabf4fd](https://github.com/phitoduck/lose-it/tree/fabf4fd211b80e149015ef62a71d68c38a151264).
The adapted module retains the full notice below. Preserve this notice when
redistributing source or installation archives.

```text
MIT License

Copyright (c) 2026 phitoduck

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Other research sources

[cluffa/loseit-cli at 62bbfbe](https://github.com/cluffa/loseit-cli/tree/62bbfbeed83f315f39a7cbd6ce26bec5066d43d1)
was consulted for protocol facts only. No implementation code or fixtures were
copied; no license was discoverable at that revision.

The Lose It! website's public JavaScript serializers were inspected to verify
wire formats and units. The original application bundle is not redistributed.
The public serializers are identified by the pinned build in `schemas.py`.

## Lose It! artwork

The official Lose It! app icon in `custom_components/loseit/brand/` is sourced from
FitNow, Inc.'s verified Apple App Store listing. It remains proprietary artwork of
its respective rights holders, not original project art or MIT-licensed material.
See the [bundled artwork notice](custom_components/loseit/brand/NOTICE.md) for the
source URL, source SHA-256 and transformations. No endorsement or artwork license
is implied.

## Service access and trademarks

The MIT license covers this project's code; it does **not** grant permission to
access or redistribute the Lose It! service, its proprietary code, or user data.
This is an independent, unofficial integration, not affiliated with or endorsed
by Lose It! or Home Assistant. Product names identify the services they refer to;
no ownership of those trademarks is claimed.
