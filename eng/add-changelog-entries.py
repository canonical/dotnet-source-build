#!/usr/bin/python3

import argparse
# if missing, run: sudo apt install python3-distro-info
import distro_info
from glob import glob
from os import path
import re
import subprocess
import sys
from typing import NoReturn


DEVEL_DISTRIBUTION = distro_info.UbuntuDistroInfo().devel()
SRC_DIRECTORY_PATH: str = path.abspath(path.join(
        path.dirname(path.abspath(__file__)),
        "..", "src"))


def LogErrorAndExit(message: str, exitCode=1) -> NoReturn:
    print("ERROR: " + message, file=sys.stderr, flush=True)
    sys.exit(exitCode)


class ArgumentParser(argparse.ArgumentParser):
    def __init__(self):
        super().__init__(
            description="A tool to create new changelog entries of a "
                        "new upstream release for all distributions of a "
                        "source package.")

        self.add_argument(
            "-p", "--package",
            type=str,
            dest="SourcePackageName",
            choices=[
                "dotnet8",
                "dotnet9"
            ],
            required=True,
            help="Name of the source package to create changelog entries for.")

        self.add_argument(
            "-v", "--version",
            type=str,
            dest="UpstreamVersion",
            required=True,
            help="Version of the new upstream release.")

        self.add_argument(
            "--lp", "--lp-bug-number",
            type=str,
            dest="LaunchpadBugNumber",
            help="Corresponding Launchpad bug report number.")


def AppendChangelogEntry(
        changelogFile: str,
        distribution: str,
        version: str,
        entry: str) -> None:
    args = [
        "dch",
        "--changelog", changelogFile,
        "--distribution", distribution,
        "--newversion", version,
        entry
    ]

    subprocess.check_call(args)


def Main() -> None:
    parser = ArgumentParser()
    args = parser.parse_args()

    sourcePackageName: str = args.SourcePackageName
    upstreamVersion: str = args.UpstreamVersion
    lpBug: str | None = args.LaunchpadBugNumber

    changelogEntry: str = "New upstream release"

    if lpBug is not None:
        changelogEntry = f"{changelogEntry} (LP: #{lpBug})"

    match = re.search(r"dotnet(?P<majorVersion>\d+)$", sourcePackageName)

    if match is None:
        LogErrorAndExit()

    sourceMajorVersion = int(match.group("majorVersion"))
    sourceIsLts = sourceMajorVersion % 2 == 0

    changelogs = glob(path.join(
        SRC_DIRECTORY_PATH,
        f"changelog.{sourcePackageName}.*"))

    for changelog in changelogs:
        match = re.search(r".(?P<distribution>[a-z]+)$", changelog)
        distribution = match.group("distribution")

        distributionVersion = (distro_info
                               .UbuntuDistroInfo()
                               .version(distribution))
        distributionIsLts = distributionVersion.endswith(" LTS")

        if distributionIsLts:
            distributionVersion = distributionVersion[:-4]

        packageVersion = f"{upstreamVersion}-0ubuntu1"

        if distribution != DEVEL_DISTRIBUTION:
            packageVersion = f"{packageVersion}~{distributionVersion}.1"

            if not sourceIsLts and distributionIsLts:
                packageVersion = f"{packageVersion}~ppa1"

        print("Adding changelog entry to "
              f"{path.relpath(changelog)}: {packageVersion}")
        AppendChangelogEntry(
            changelog,
            distribution,
            packageVersion,
            changelogEntry)


Main()
