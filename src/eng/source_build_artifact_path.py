#!/usr/bin/env python3

import os
import sys
from glob import glob

sys.path.append("debian/eng")
from versionlib.dotnet import SourcePackageVersion, RuntimeIdentifier


def GetSourceBuiltArtifactsTarball(
        basePath: str, 
        sdkVersion: str, 
        type: str = "Packages") -> str:
    
    globPattern = ""

    if type == "Packages":
        # e.g. Private.SourceBuilt.Artifacts.9.0.100-preview.7.24407.1.ubuntu.24.10-x64.tar.gz
        globPattern =  (f"{basePath}/Private.SourceBuilt.Artifacts."
                        f"{sdkVersion}*.*.tar.gz")
    elif type == "SDK":
        # e.g. dotnet-sdk-9.0.100-preview.7.24407.1-ubuntu.24.10-x64.tar.gz
        globPattern =  (f"{basePath}/dotnet-sdk-{sdkVersion}*-*.tar.gz")
    else:
        raise ValueError(f"Unknown source built artifacts tarball type '{type}'.")
    
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

    print(GetSourceBuiltArtifactsTarball(
        basePath="/usr/lib/dotnet/source-built-artifacts",
        sdkVersion=str(version.SdkVersion)))
