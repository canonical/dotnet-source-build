#!/usr/bin/env python3

import os
import sys


sys.path.append("debian/eng")
from versionlib.dotnet import RuntimeVersion, SdkVersion, SourcePackageVersion  # noqa: E402, E501


if __name__ == "__main__":
    version = SourcePackageVersion.ParseFromChangelog(
        os.path.join("debian", "changelog"))

    if (len(sys.argv) <= 1):
        print(f"{version.SdkVersion.Major}.{version.SdkVersion.Minor}")
    elif (sys.argv[1] == "--major"):
        print(f"{version.SdkVersion.Major}")
    elif (sys.argv[1] == "--minor"):
        print(f"{version.SdkVersion.Minor}")
    elif (sys.argv[1] == "--sdk"):
        print(str(version.SdkVersion))
    elif (sys.argv[1] == "--runtime"):
        print(str(version.RuntimeVersion))
    elif (sys.argv[1] == "--runtime-only-deb-version"):
        buildSuffix = ""

        # this fixes the version ordering issue for released .NET 9 preview
        # binary packages with incorrect version identifiers
        if (version.RuntimeVersion == RuntimeVersion(9, 0, 0, None)):
            buildSuffix = "-rtm"

            # see FO127 specification for SDK only release
            if (version.SdkVersion == SdkVersion(9, 0, 100, 1, None)):
                buildSuffix += "+build1"

        print(version.RuntimeOnlyDebVersion(buildSuffix))
    elif (sys.argv[1] == "--sdk-only-deb-version"):
        buildSuffix = ""

        # this fixes the version ordering issue for released .NET 9 preview
        # binary packages with incorrect version identifiers
        if (version.SdkVersion == SdkVersion(9, 0, 100, 0, None)):
            buildSuffix = "-rtm"

        print(version.SdkOnlyDebVersion(buildSuffix))
    else:
        print("invalid arguments")
        sys.exit(1)
