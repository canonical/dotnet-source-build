#!/usr/bin/env python3

import os
import sys
import glob
import argparse

sys.path.append("debian/eng")
from versionlib.dotnet import SourcePackageVersion, RuntimeIdentifier


def GetSourceBuiltArtifactsTarball(
        basePath: str, 
        sdkVersion: str, 
        type: str = "packages") -> str:
    
    globPattern = ""

    if type.lower() == "packages":
        # e.g. Private.SourceBuilt.Artifacts.9.0.100-preview.7.24407.1.ubuntu.24.10-x64.tar.gz
        globPattern =  (f"{basePath}/Private.SourceBuilt.Artifacts."
                        f"{sdkVersion}*.*.tar.gz")
    elif type.lower() == "sdk":
        sdkArtifactsPath = os.path.join(basePath, "Sdk")
        if os.path.exists(sdkArtifactsPath):
            basePath = sdkArtifactsPath

        # e.g. dotnet-sdk-9.0.100-preview.7.24407.1-ubuntu.24.10-x64.tar.gz
        globPattern =  (f"{basePath}/**/dotnet-sdk-{sdkVersion}*-*.tar.gz")
    else:
        raise ValueError(f"Unknown source built artifacts tarball type '{type}'.")
    
    files = glob.glob(globPattern, recursive=True)

    if len(files) == 0:
        raise ValueError(f"Source built artifacts tarball not found "
                         f"(glob pattern: '{globPattern}').")
    elif len(files) > 1:
        raise ValueError(f"Multiple source built artifacts artifacts tarballs "
                         f"found (glob pattern: '{globPattern}').")

    return files[0]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--type",
                        type=str,
                        dest="Type",
                        choices=["packages","sdk"],
                        required=True,
                        metavar="TYPE",
                        help = "artifact type")
    parser.add_argument("--base-path",
                        type=str,
                        dest="BasePath",
                        required=True,
                        metavar="PATH",
                        help="base path where the artifacts tarball is "
                             "located")
    args = parser.parse_args()

    version = SourcePackageVersion.ParseFromChangelog(
        os.path.join("debian", "changelog"))

    print(GetSourceBuiltArtifactsTarball(
        basePath=args.BasePath,
        sdkVersion=str(version.SdkVersion),
        type=args.Type))
