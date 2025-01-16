from strenum import StrEnum
import platform
import re

from . import dpkg


class PreReleaseType(StrEnum):
    Alpha = "alpha"
    Beta = "beta"
    Preview = "preview"
    ReleaseCandidate = "rc"


class PrereleaseVersion:
    def __init__(self,
                 type: PreReleaseType,
                 revision: int | None,
                 buildMetadata: list[str] | None) -> None:
        self.Type = type
        self.Revision = revision
        self.BuildMetadata = buildMetadata

    def __str__(self) -> str:
        prereleaseVersion = str(self.Type)

        if self.Revision is not None:
            prereleaseVersion += "." + str(self.Revision)

        if self.BuildMetadata is not None:
            for buildMetadataPart in self.BuildMetadata:
                prereleaseVersion += "." + buildMetadataPart

        return prereleaseVersion

    def DebRepresentation(self) -> str:
        prereleaseVersion = str(self.Type)

        if self.Revision is not None:
            prereleaseVersion += str(self.Revision)

        if self.BuildMetadata is not None:
            for buildMetadataPart in self.BuildMetadata:
                prereleaseVersion += "." + buildMetadataPart

        return prereleaseVersion

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, __value: object) -> bool:
        if __value is None:
            return False

        if self.Type != __value.Type:
            return False

        if self.Revision != __value.Revision:
            return False

        if (self.BuildMetadata is None) != (__value.BuildMetadata is None):
            return False
        elif self.BuildMetadata is None:
            return True
        elif len(self.BuildMetadata) != len(__value.BuildMetadata):
            return False

        for i in range(len(self.BuildMetadata)):
            if self.BuildMetadata[i] != __value.BuildMetadata[i]:
                return False

        return True


class SdkVersion:
    def __init__(self,
                 major: int,
                 minor: int,
                 featureBand: int,
                 patch: int,
                 preReleaseVersion: PrereleaseVersion) -> None:
        if major < 1:
            raise ValueError(".NET SDK major version number can't be "
                             f"non-positive (major = {major}).")
        if minor < 0:
            raise ValueError(".NET SDK minor version number can't be "
                             f"negative (minor = {minor}).")
        if featureBand < 100 or featureBand > 900 or (featureBand % 100) != 0:
            raise ValueError(".NET SDK feature band has to be a "
                             "multiple of 100 between (inclusive) 100 and 900 "
                             f"(featureBand = {featureBand}).")
        if patch < 0 or patch > 99:
            raise ValueError(".NET SDK patch number has to be "
                             "between (inclusive) 0 and 99 "
                             f"(patch = {patch}).")

        self.Major = major
        self.Minor = minor
        self.FeatureBand = featureBand
        self.Patch = patch
        self.Revision = featureBand + patch
        self.PreReleaseVersion = preReleaseVersion

    def __str__(self) -> str:
        sdkVersion = f"{self.Major}.{self.Minor}.{self.Revision}"

        if self.PreReleaseVersion is not None:
            sdkVersion += "-" + str(self.PreReleaseVersion)

        return sdkVersion

    def DebRepresentation(self) -> str:
        sdkVersion = f"{self.Major}.{self.Minor}.{self.Revision}"

        if self.PreReleaseVersion is not None:
            sdkVersion += "~" + self.PreReleaseVersion.DebRepresentation()

        return sdkVersion

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other: 'SdkVersion') -> bool:
        if not isinstance(other, SdkVersion):
            return False

        return (self.Major == other.Major
                and self.Minor == other.Minor
                and self.Minor == other.Minor
                and self.FeatureBand == other.FeatureBand
                and self.Patch == other.Patch
                and self.PreReleaseVersion == other.PreReleaseVersion)


class RuntimeVersion:
    def __init__(self,
                 major: int,
                 minor: int,
                 patch: int,
                 preReleaseVersion: PrereleaseVersion) -> None:
        if major < 1:
            raise ValueError(".NET Runtime major version number can't be "
                             f"non-positive (major = {major}).")
        if minor < 0:
            raise ValueError(".NET Runtime minor version number can't be "
                             f"negative (minor = {minor}).")
        if patch < 0 or patch > 99:
            raise ValueError(".NET Runtime patch number has to be "
                             f"between 0 and 99 (patch = {patch}).")

        self.Major = major
        self.Minor = minor
        self.Patch = patch
        self.PreReleaseVersion = preReleaseVersion

    def __str__(self) -> str:
        runtimeVersion = f"{self.Major}.{self.Minor}.{self.Patch}"

        if self.PreReleaseVersion is not None:
            runtimeVersion += "-" + str(self.PreReleaseVersion)

        return runtimeVersion

    def DebRepresentation(self) -> str:
        runtimeVersion = f"{self.Major}.{self.Minor}.{self.Patch}"

        if self.PreReleaseVersion is not None:
            runtimeVersion += "~" + self.PreReleaseVersion.DebRepresentation()

        return runtimeVersion

    def __repr__(self) -> str:
        return str(self)

    def __eq__(self, other: 'RuntimeVersion') -> bool:
        if not isinstance(other, RuntimeVersion):
            return False

        return (self.Major == other.Major
                and self.Minor == other.Minor
                and self.Patch == other.Patch
                and self.PreReleaseVersion == other.PreReleaseVersion)


class SourcePackageVersion:
    Pattern = (r"\A(?:(?P<OverwrittenVersion>.+)\+really)?"
               r"(?P<Major>[1-9]\d*)\."
               r"(?P<Minor>\d+)\."
               r"(?P<SdkFeatureBand>[1-9])"
               r"(?P<SdkPatch>\d\d)"
               r"(?:-"
                    r"(?P=Major)\."  # noqa: E127
                    r"(?P=Minor)\."
                    r"(?P<RuntimePatch>0|[1-9]\d?)"
               r")?"
               r"(?:~"
                    r"(?P<PreReleaseType>rc|preview|beta|alpha)"
                    r"(?P<PreReleaseRevision>[1-9]\d*)"
                    r"(?P<BuildMetadata>(?:\.[0-9a-z]+)+)?"
               r")?"
               r"(?:~bootstrap\+"
                    r"(?P<BootstrapArch>amd64|arm64|s390x|ppc64el|riscv64)"
               r")?"
               r"(?:-"
                    r"(?P<DebianRevision>[A-Za-z0-9.+:~]+)"
                    r"(?:ubuntu(?P<UbuntuRevision>[A-Za-z0-9.+:~]+))"
               r")\Z")

    def __init__(self,
                 sdkVersion: str,
                 runtimeVersion: str,
                 debRevision: str,
                 raw: str,
                 isFO127Compliant: bool,
                 bootstrapArch: str | None = None,
                 overwrittenVersion: str | None = None) -> None:
        self.SdkVersion = sdkVersion
        self.RuntimeVersion = runtimeVersion
        self.DebRevision = debRevision
        self.Raw = raw
        self.IsFO127Compliant = isFO127Compliant
        self.BootstrapArchitecture = bootstrapArch
        self.OverwrittenVersion = overwrittenVersion

    def RuntimeOnlyDebVersion(self, buildSuffix: str = "") -> str:
        versionString = self.RuntimeVersion.DebRepresentation() + buildSuffix

        if (self.BootstrapArchitecture is not None):
            versionString += f"~bootstrap+{self.BootstrapArchitecture}"

        versionString += f"-{self.DebRevision}"
        return versionString

    def SdkOnlyDebVersion(self, buildSuffix: str = "") -> str:
        versionString = self.SdkVersion.DebRepresentation() + buildSuffix

        if (self.BootstrapArchitecture is not None):
            versionString += f"~bootstrap+{self.BootstrapArchitecture}"

        versionString += f"-{self.DebRevision}"
        return versionString

    @staticmethod
    def Parse(value: str) -> 'SourcePackageVersion':
        parsingResult = re.search(SourcePackageVersion.Pattern, value)

        if parsingResult is None:
            raise ValueError("The format of the provided .NET source package "
                             "version identifier could not be recognized "
                             f"(value=\"{value}\").")

        if parsingResult.group("PreReleaseType") is not None:
            preReleaseType = parsingResult.group("PreReleaseType")
            preReleaseRevision = parsingResult.group("PreReleaseRevision")
            buildMetadata = parsingResult.group("BuildMetadata")

            if preReleaseRevision is not None:
                preReleaseRevision = int(preReleaseRevision)

            if buildMetadata is not None:
                buildMetadata = buildMetadata.split('.')[1:]

            preReleaseVersion = PrereleaseVersion(
                preReleaseType, preReleaseRevision, buildMetadata)
        else:
            preReleaseVersion = None

        major = int(parsingResult.group("Major"))
        minor = int(parsingResult.group("Minor"))
        sdkFeatureBand = int(parsingResult.group("SdkFeatureBand")) * 100
        sdkPatch = int(parsingResult.group("SdkPatch"))
        sdkVersion = SdkVersion(
            major, minor, sdkFeatureBand, sdkPatch, preReleaseVersion)

        if parsingResult.group("RuntimePatch") is not None:
            isFO127Compliant = True
            runtimePatch = int(parsingResult.group("RuntimePatch"))
        else:
            isFO127Compliant = False
            runtimePatch = sdkPatch

        runtimeVersion = RuntimeVersion(
            major, minor, runtimePatch, preReleaseVersion)

        overwrittenVersion = parsingResult.group("OverwrittenVersion")
        bootstrapArch = parsingResult.group("BootstrapArch")
        debianRevision = parsingResult.group("DebianRevision")
        ubuntuRevision = parsingResult.group("UbuntuRevision")
        debRevision = dpkg.DebRevision(debianRevision, ubuntuRevision)

        return SourcePackageVersion(
            sdkVersion,
            runtimeVersion,
            debRevision,
            value,
            isFO127Compliant,
            bootstrapArch,
            overwrittenVersion)

    @staticmethod
    def ParseFromChangelog(path: str) -> 'SourcePackageVersion':
        version = dpkg.Changelog(path).ParseFieldOfLatestEntry(
            dpkg.ChangelogEntryField.VERSION)

        return SourcePackageVersion.Parse(version)

    def __str__(self) -> str:
        return self.Raw


class OperatingSystemIdentifier:
    def __init__(self, name, version):
        self.Name = name
        self.Version = version

    @staticmethod
    def Current() -> 'OperatingSystemIdentifier':
        osReleaseData = platform.freedesktop_os_release()

        osId = OperatingSystemIdentifier(
            osReleaseData["ID"],
            osReleaseData["VERSION_ID"])

        return osId

    def __str__(self) -> str:
        return f"{self.Name}.{self.Version}"


class ArchitectureIdentifier(StrEnum):
    X64 = "x64"
    ARM64 = "arm64"
    S390X = "s390x"
    PPC64LE = "ppc64le"

    @staticmethod
    def ParseMachineIdentifier(machineIdentifier: str) -> 'ArchitectureIdentifier':  # noqa: E501
        match machineIdentifier:
            case "x86_64":
                return ArchitectureIdentifier.X64
            case "aarch64":
                return ArchitectureIdentifier.ARM64
            case "s390x":
                return ArchitectureIdentifier.S390X
            case "ppc64le":
                return ArchitectureIdentifier.PPC64LE
            case _:
                raise RuntimeError(f"{machineIdentifier} is an "
                                   "unknown/unsupported system architecture.")

    @staticmethod
    def Current() -> 'ArchitectureIdentifier':
        machineIdentifier = platform.machine()
        return ArchitectureIdentifier.ParseMachineIdentifier(machineIdentifier)


class RuntimeIdentifier:
    def __init__(self,
                 osIdentifier: OperatingSystemIdentifier,
                 architecture: ArchitectureIdentifier | None) -> None:
        self.OperatingSystemIdentifier = osIdentifier
        self.ArchitectureIdentifier = architecture

    @staticmethod
    def FromPlatformData() -> 'RuntimeIdentifier':
        return RuntimeIdentifier(
            OperatingSystemIdentifier.Current(),
            ArchitectureIdentifier.Current())

    def __str__(self) -> str:
        rid = str(self.OperatingSystemIdentifier)

        if self.ArchitectureIdentifier is not None:
            rid += '-' + str(self.ArchitectureIdentifier)

        return rid
