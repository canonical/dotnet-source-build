from strenum import StrEnum
import errno
import os
import subprocess


class DebRevision:
    def __init__(
            self,
            debianRevision: str,
            ubuntuRevision: str | None = None) -> None:
        self.DebianRevision = debianRevision
        self.UbuntuRevision = ubuntuRevision

    def __str__(self) -> str:
        if self.UbuntuRevision is None:
            return f"{self.DebianRevision}"
        else:
            return f"{self.DebianRevision}ubuntu{self.UbuntuRevision}"


class ChangelogEntryField(StrEnum):
    VERSION = "Version"
    DISTRIBUTION = "Distribution"
    URGENCY = "Urgency"
    MAINTAINER = "Maintainer"
    CHANGES = "Changes"


class Changelog:
    def __init__(self, path: str) -> None:
        if not os.path.exists(path):
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), path)

        self.Path = path

    def ParseFieldOfLatestEntry(self, field: ChangelogEntryField) -> str:
        field = subprocess.check_output(
            "dpkg-parsechangelog "
            f"--show-field {str(field.value)} "
            f"--file {self.Path}",
            text=True, shell=True)

        return field[:-1]  # remove trailing \n
