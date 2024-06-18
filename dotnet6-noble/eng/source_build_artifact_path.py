#!/usr/bin/env python3

import os
import sys
from glob import glob

sys.path.append("debian/eng")
from versionlib.dotnet import SourcePackageVersion, RuntimeIdentifier, SdkVersion


def GetSourceBuiltArtifactsTarball(
        basePath: str, 
        sdkVersion: str, 
        runtimeIdentifier: str) -> str:
    globPattern =  (f"{basePath}/Private.SourceBuilt.Artifacts."
                    f"{sdkVersion}*.{runtimeIdentifier}.tar.gz")

    files = glob(globPattern)

    if len(files) == 0:
        raise ValueError(f"Source built artifacts tarball not found "
                         f"(glob pattern: '{globPattern}').")
    elif len(files) > 1:
        raise ValueError(f"Multiple source built artifacts artifacts tarballs "
                         f"found (glob pattern: '{globPattern}').")

    return files[0]


if __name__ == "__main__":
    version = SourcePackageVersion.ParseFromChangelog(
        os.path.join("debian", "changelog"))

    runtimeIdentifier = RuntimeIdentifier.FromPlatformData()

    print(GetSourceBuiltArtifactsTarball(
        basePath="/usr/lib/dotnet/source-built-artifacts",
        sdkVersion=str(version.SdkVersion), 
        runtimeIdentifier=str(runtimeIdentifier)))
