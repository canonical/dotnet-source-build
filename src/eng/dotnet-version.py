#!/usr/bin/env python3

import os
import sys


sys.path.append("debian/eng")
from versionlib.dotnet import SourcePackageVersion


if __name__ == "__main__":
    version = SourcePackageVersion.ParseFromChangelog(
        os.path.join("debian", "changelog"))
    
    print(f"{version.SdkVersion.Major}.{version.SdkVersion.Minor}")