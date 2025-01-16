![Ubuntu and .NET Logos combined with a heart in-between](images/Ubunru+DotNet.svg)

# Building .NET from source for Ubuntu
[![License badge for GNU General Public License v3.0](https://img.shields.io/badge/License-GPL--3.0-informational)](https://github.com/canonical/dotnet-source-build/blob/main/LICENSE)

Home of the .NET source build effort for Ubuntu platforms. This Repository includes all the code needed to build .NET Debian source packages that target Ubuntu 22.04+

## Releases

| Package Name | Launchpad Link | Autopkgtest Link |
|--------------|----------------|------------------|
| `dotnet9` | [![dotnet9 source package on Launchpad](https://img.shields.io/badge/Launchpad-dotnet9-F8C300?logo=launchpad)](https://launchpad.net/ubuntu/+source/dotnet9) | [![dotnet9 Ubuntu autopkgtest cloud](https://img.shields.io/badge/Ubuntu%20autopkgtest%20cloud-dotnet9-E95420?logo=ubuntu)](https://autopkgtest.ubuntu.com/packages/dotnet9) |
| `dotnet8` | [![dotnet8 source package on Launchpad](https://img.shields.io/badge/Launchpad-dotnet8-F8C300?logo=launchpad)](https://launchpad.net/ubuntu/+source/dotnet8) | [![dotnet8 Ubuntu autopkgtest cloud](https://img.shields.io/badge/Ubuntu%20autopkgtest%20cloud-dotnet8-E95420?logo=ubuntu)](https://autopkgtest.ubuntu.com/packages/dotnet8) |
| `dotnet7` | [![dotnet7 source package on Launchpad](https://img.shields.io/badge/Launchpad-dotnet7-F8C300?logo=launchpad)](https://launchpad.net/ubuntu/+source/dotnet7) | [![dotnet7 Ubuntu autopkgtest cloud](https://img.shields.io/badge/Ubuntu%20autopkgtest%20cloud-dotnet7-E95420?logo=ubuntu)](https://autopkgtest.ubuntu.com/packages/dotnet7) |
| `dotnet6` | [![dotnet6 source package on Launchpad](https://img.shields.io/badge/Launchpad-dotnet6-F8C300?logo=launchpad)](https://launchpad.net/ubuntu/+source/dotnet6) | [![dotnet6 Ubuntu autopkgtest cloud](https://img.shields.io/badge/Ubuntu%20autopkgtest%20cloud-dotnet6-E95420?logo=ubuntu)](https://autopkgtest.ubuntu.com/packages/dotnet6) |

> [!NOTE]
> This repository only builds .NET 8+ source packages. Support for `dotnet6` and `dotnet7` was dropped with commit [94faf62](https://github.com/canonical/dotnet-source-build/commit/94faf62fe11b9a7ef021384198e02bf6974af02c).

### See also

- [.NET Maintainer Team on Launchpad](https://launchpad.net/~dotnet)
- [.NET Backports PPA](https://launchpad.net/~dotnet/+archive/ubuntu/backports)

## License
  
Copyright (C) 2025 Canonical Ltd.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

This project is licensed under the GPLv3 license. See the respective license information for third party libraries.

### Third party libraries 

This project uses third-party libraries. See the respective licensing information for more details.

#### .NET Test Runner 

| Project | .NET Test Runner |
|---------|---------|
| License | LGPL-2.1 |
| Copyright | 2019 Red Hat, Inc<br>2024 Canonical Ltd. |
| Location in project | [`src/eng/test-runner`](src/eng/test-runner) |
| Upstream repository | https://github.com/canonical/dotnet-test-runner |

See the [README.md](src/eng/test-runner/README.md) and [LICENSE.txt](src/eng/test-runner/LICENSE.txt) file in the corresponding directory for more details.

#### .NET Regular Tests

| Project |.NET Regular Tests |
|---------|---------|
| License | MIT |
| Copyright | 2018 Radka Janeková<br>2019 Red Hat, Inc<br>2024 Canonical Ltd. |
| Location in project | [`src/tests/regular-tests`](src/tests/regular-tests) |
| Upstream repository | https://github.com/canonical/dotnet-regular-tests |

See the [README.md](src/tests/regular-tests/README.md) and [LICENSE.md](src/tests/regular-tests/LICENSE.md) file in the corresponding directory for more details.

#### strenum

| Project |.NET Regular Tests |
|---------|---------|
| License | MIT |
| Copyright | 2019 James C Sinclair |
| Location in project | [`src/eng/strenum`](src/eng/strenum) |
| Upstream repository | https://github.com/irgeek/StrEnum |

See the [README.md](src/eng/strenum/README.md) and [LICENSE](src/eng/strenum/LICENSE) file in the corresponding directory for more details.