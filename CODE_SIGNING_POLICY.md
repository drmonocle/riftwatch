# Code signing policy

This is the code signing policy for **RiftWatch** (`RiftWatch.exe`), the Windows app built from this repository.

## Status

RiftWatch has applied to the [SignPath Foundation](https://signpath.org/) free code signing program for open source projects. **Until the application is accepted and the first signed release is published, `RiftWatch.exe` is not code-signed**, and Windows may warn about an unknown publisher. Every release still publishes the SHA-256 of `RiftWatch.exe` (`RiftWatch.exe.sha256`).

## Signing service (once accepted)

Free code signing provided by [SignPath.io](https://signpath.io/), certificate by [SignPath Foundation](https://signpath.org/).

## What is signed

- Only `RiftWatch.exe`, built from the source code in this public repository ([drmonocle/riftwatch](https://github.com/drmonocle/riftwatch)), which is MIT licensed and contains no proprietary components.
- Nothing else is signed: no third-party binaries and no files from other projects.
- Product name (`RiftWatch`) and product version are set in the executable and must match the release tag.

## How releases are built and signed

- Releases are built by the [`Release` GitHub Actions workflow](.github/workflows/release.yml) on **GitHub-hosted runners**, from an exact tagged commit. Nothing is built or signed on a developer machine.
- The workflow runs the full test suite, builds `RiftWatch.exe`, and submits that single artifact for signing.
- **Every signing request is approved manually** by the maintainer before the file is signed.
- The signed file is attached to a **draft** GitHub release together with its SHA-256 checksum. The release only becomes public (and visible to the in-app updater) when the maintainer publishes it.
- The in-app updater only downloads from `github.com/drmonocle/riftwatch/releases` and refuses to install a file that doesn't match its published SHA-256.

## Project roles

| Role | Who |
|---|---|
| Author / committer | Monocle Productions LLC ([@drmonocle](https://github.com/drmonocle)) |
| Reviewer | Monocle Productions LLC ([@drmonocle](https://github.com/drmonocle)) |
| Approver (signing requests) | Monocle Productions LLC ([@drmonocle](https://github.com/drmonocle)) |

Everyone with access to the repository or to signing uses multi-factor authentication.

## Privacy

RiftWatch has no accounts, analytics or tracking, and sends no personal data anywhere. See the [Privacy section of the README](README.md#-privacy) for the exact list of services it contacts (Riot's public esports API, lolworlds.com for the 24/7 stream schedule, and GitHub for updates and head-to-head data).

## System changes

- RiftWatch is a single portable file: there is no installer, and nothing is installed system-wide. To remove it, delete the file.
- **Start with Windows** is off by default. If you turn it on in Settings, RiftWatch adds one value to your own user's startup list (`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`); turning it off removes it.
- When you press **Update**, RiftWatch replaces its own file with the verified download. A copy of the previous version (`RiftWatch.exe.old`) is kept beside it briefly and then deleted.

## Reporting a problem

If you think a signed file is wrong or malicious, please [open an issue](https://github.com/drmonocle/riftwatch/issues) or use **Security → Report a vulnerability** on the repository.

---

RiftWatch is an unofficial fan project by Monocle Productions LLC. It isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games, and all associated properties are trademarks or registered trademarks of Riot Games, Inc.
