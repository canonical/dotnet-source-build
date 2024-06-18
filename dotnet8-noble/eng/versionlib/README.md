# versionlib

This library has the goal to make complex version parsing scenarios easy.

## Getting started

```python
import os
import sys

sys.path.append("debian/eng")
from versionlib.dotnet import SourcePackageVersion, RuntimeIdentifier

version = SourcePackageVersion.ParseFromChangelog(
    os.path.join("debian", "changelog"))

runtimeIdentifier = RuntimeIdentifier.FromPlatformData()

print(version) 
# 6.0.128-0ubuntu1~23.10.1

print(version.SdkVersion)
# 6.0.128

print(version.SdkVersion.Major)
# 6

print(version.SdkVersion.Minor)
# 0

print(version.SdkVersion.FeatureBand)
# 100

print(version.SdkVersion.Patch)
# 28

print(version.SdkVersion.Revision)
# 128

print(version.RuntimeVersion)
# 6.0.28

print(version.RuntimeVersion.Major)
# 6

print(version.RuntimeVersion.Minor)
# 0

print(version.RuntimeVersion.Patch)
# 28

print(version.DebRevision)
# 0ubuntu1~23.10.1

print(version.DebRevision.DebianRevision)
# 0

print(version.DebRevision.UbuntuRevision)
# 1~23.10.1

print(version.IsFO127Compliant)
# False

print(runtimeIdentifier)
# ubuntu.23.10-x64

print(runtimeIdentifier.OperatingSystemIdentifier)
# ubuntu.23.10

print(runtimeIdentifier.OperatingSystemIdentifier.Name)
# ubuntu

print(runtimeIdentifier.OperatingSystemIdentifier.Version)
# 23.10

print(runtimeIdentifier.ArchitectureIdentifier)
# x64
```

Alternatively add `"debian/eng"` to the
[`PYTHONPATH`](https://docs.python.org/3/using/cmdline.html#envvar-PYTHONPATH)
environemnt variable if you do not want to use the `sys.path.append`
mechanism before importing this module.

```bash
PYTHONPATH="debian/eng:$PYTHONPATH"
```

## Quirks

If you used the module localy a `__pycache__` directory will be created (at
`debian/eng/versionlib/__pycache__`). Do not forget to delete this directory
before building the source-package or commiting changes to `git-ubuntu`.

## Author

Dominik Viererbe \<dominik.viererbe@canonical.com\>
