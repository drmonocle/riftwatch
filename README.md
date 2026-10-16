# RiftWatch is now RiftWise

RiftWatch was renamed **RiftWise** on 2026-10-16 (version 0.4.0). Same app, new name.

- Code, releases and issues: **https://github.com/drmonocle/riftwise**
- Web version: **https://lolworlds.com/riftwise/** (old lolworlds.com/riftwatch links forward there)

## Why this repository exists

Installed RiftWatch apps (0.3.40 and older) only trust downloads from `github.com/drmonocle/riftwatch`.
This repository holds one bridge release whose `RiftWatch.exe` is the RiftWise app, so those copies can update
themselves once more and move over to RiftWise. After that they update from `drmonocle/riftwise`.

The `h2h-data` branch is a copy of the RiftWise head-to-head data (refreshed every 6 hours by
`.github/workflows/mirror-h2h.yml`) for RiftWatch apps that have not updated yet.

Nothing else lives here; please open issues on https://github.com/drmonocle/riftwise.
