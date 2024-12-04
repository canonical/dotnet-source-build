#!/usr/bin/env python3

import os
import sys


sys.path.append("debian/eng")
from versionlib.dotnet import SourcePackageVersion


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
        versionString = str(version.RuntimeVersion)        

        if (version.BootstrapArchitecture != None):
            versionString += f"~bootstrap+{version.BootstrapArchitecture}"

        versionString += f"-rtm-{version.DebRevision}"

        print(versionString)
    elif (sys.argv[1] == "--sdk-only-deb-version"):
        versionString = str(version.SdkVersion)        

        if (version.BootstrapArchitecture != None):
            versionString += f"~bootstrap+{version.BootstrapArchitecture}"

        versionString += f"-{version.DebRevision}"

        print(versionString)
    else:
        print("invalid arguments")
        sys.exit(1)