#!/usr/bin/python3

from glob import glob
from os import path
from typing import NoReturn
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile


DOTNET_VIRTUAL_MONOLITHIC_REPOSITORY_URL = "https://github.com/dotnet/dotnet"
FO127_SPEC_URL = "https://github.com/canonical/dotnet/blob/main/specs/FO127.md"


def DotnetSecurityPartnersRepositoryUrl(accessToken: str | None = None) -> str:
    userinfo = "dotnet-security-partners"

    if accessToken is not None:
        userinfo += ":" + accessToken

    return (f"https://{userinfo}@"
            "dev.azure.com/dotnet-security-partners/dotnet/_git/dotnet")


def LogErrorAndExit(message: str, exitCode=1) -> NoReturn:
    print("ERROR: " + message, file=sys.stderr, flush=True)
    sys.exit(exitCode)


def LogWarning(message: str) -> None:
    print("WARNING: " + message, file=sys.stderr, flush=True)


class ArgumentParser(argparse.ArgumentParser):
    def __init__(self):
        super().__init__(
            description="A tool for creating .NET orig tarballs used for "
                        "building Ubuntu .NET source packages.")

        self.__AddGeneralOptions()
        self.__AddManifestOptions()
        self.__AddBootstrappingOption()

    def __AddGeneralOptions(self) -> None:
        self.add_argument(
            "-v", "--verbose",
            dest="VerboseOutput",
            action="store_true",
            help="Increase the verbosity of the output.")

        self.__AddCloneGitRepositoryOptionGroup()

        self.add_argument(
            "--source-version",
            type=str,
            dest="SourceVersion",
            metavar="VERSION",
            required=True,
            help="The FO127 compliant version string of the .NET release "
                 "(e.g. '8.0.100-8.0.0~preview3', '9.0.106-9.0.5').\n"
                 "NOTE: Do NOT add a '~bootstrap' suffix when including "
                 "a bootstrap SDK.")

        self.add_argument(
            "--git-reference",
            type=str,
            dest="GitReference",
            metavar="COMMITISH",
            required=True,
            help="The git commit-ish in the cloned repository that points to "
                 "the release that should be packaged.")

        self.add_argument(
            "--security-partners-repository-access-token",
            dest="SecurityPartnersRepositoryAccessToken",
            metavar="ACCESS_TOKEN",
            help="Personal access token for cloning the "
                 ".NET security partners git repository. "
                 "Can also be supplied via the "
                 "DOTNET_SECURITY_PARTNERS_REPOSITORY_ACCESS_TOKEN "
                 "environment variable")

        distPath = ExecutionEnvironment.GetExpectedDistDirectoryPath()
        self.add_argument(
            "--output-directory",
            type=str,
            dest="OutputDirectory",
            default=distPath,
            metavar="PATH",
            help="The path of the directory where the resulting tarball will "
                 f"be created (default: '{path.relpath(distPath)}').")

        self.add_argument(
            "--tarball-name",
            type=str,
            dest="TarballName",
            metavar="NAME",
            help="The name of the resulting tarball (without the "
                 "'.orig.tar.xz' file extension) that should be used; "
                 "otherwise a name will be determined based on the release "
                 "info.")

        self.add_argument(
            "--git-reference-repository",
            type=str,
            dest="GitReferenceRepository",
            metavar="PATH",
            help="Borrow the objects from a reference repository only to "
                 "reduce network transfer.")

    def __AddCloneGitRepositoryOptionGroup(self) -> None:
        gitRepoGroup = self.add_mutually_exclusive_group(required=True)

        gitRepoGroup.add_argument(
            "--clone-git-repository",
            type=str,
            dest="GitRepository",
            metavar="URL",
            help="The git repository to clone and create an orig tarball from.")  # noqa: E501

        gitRepoGroup.add_argument(
            "--clone-vmr",
            dest="GitRepository",
            action="store_const",
            const=DOTNET_VIRTUAL_MONOLITHIC_REPOSITORY_URL,
            help="Use the .NET virtual monolithic (git) repository "
                 "(%(const)s) to clone from.")

        gitRepoGroup.add_argument(
            "--clone-security-partners-repository",
            dest="GitRepository",
            action="store_const",
            const=DotnetSecurityPartnersRepositoryUrl(),
            help="Use the .NET security partners git repository "
                 "(%(const)s) to clone from.")

    def __AddManifestOptions(self) -> None:
        manifestGroup = self.add_argument_group(
            "manifest options",
            "The following options influnces the release manifest that will "
            "be generated and embedded into the orig tarball.")

        manifestGroup.add_argument(
            "--build-id",
            type=str,
            dest="BuildId",
            metavar="ID",
            help=".NET 10+ requires a build-id to build from source. "
                 "See the release notes of the release for details.")

        manifestGroup.add_argument(
            "--source-link-repository",
            type=str,
            dest="SourceLinkRepository",
            default=DOTNET_VIRTUAL_MONOLITHIC_REPOSITORY_URL,
            metavar="URL",
            help="The git repository url where the source of the release can "
                 "be found (default: %(default)s)")

        manifestGroup.add_argument(
            "--vendor-name",
            type=str,
            dest="VendorName",
            metavar="VENDOR_NAME",
            help="Name of the organization/person that created the "
                 "orig tarball.")

        manifestFormatGroup = manifestGroup.add_mutually_exclusive_group()

        manifestFormatGroup.add_argument(
            "--force-no-manifest",
            dest="ForceNoManifest",
            action="store_true",
            help="Force that no release manifest file will be created.")

        manifestFormatGroup.add_argument(
            "--force-use-legacy-manifest-format",
            dest="ForceUseLegacyManifestFormat",
            action="store_true",
            help="Force the use of the legacy release manifest file format "
                 "(release.info).")

        manifestFormatGroup.add_argument(
            "--force-use-json-manifest-format",
            dest="ForceUseJsonManifestFormat",
            action="store_true",
            help="Force the use of the newer json based release manifest file "
                 "format (release.json).")

    def __AddBootstrappingOption(self) -> None:
        bootstrappinGroup = self.add_argument_group("bootstrapping options")

        bootstrappinGroup.add_argument(
            "--include-bootstrap-sdk",
            dest="IncludeBootstrapSdk",
            action="store_true",
            help="Include a .NET SDK in the orig tarball that is used for "
                 "initial bootstrapping "
                 "(see also: --bootstrap-sdk-architecture).\n"
                 "NOTE: A respective '~bootstrap' suffix will be added to "
                 "the resulting tarball name.")

        bootstrappinGroup.add_argument(
            "--bootstrap-sdk-architecture",
            type=str,
            dest="BootstrapSdkArchitecture",
            choices=[
                "amd64",
                "i386",
                "arm64",
                "armhf",
                "s390x",
                "ppc64el",
                "riscv64"
            ],
            help="The architecture of the bootstrap SDK that should be "
                 "included in the orig tarball (defaults to host "
                 "architecture). See: --include-bootstrap-sdk")


class ExecutionEnvironment:
    @staticmethod
    def GetExpectedDistDirectoryPath() -> str:
        r"""
        Get the absolute path of the expected location of the dist directory.

        **Remarks:**
        This functions assumes that this script is located in the `eng`
        directory and that the `dist` directory (default output directory)
        should be located next to the `eng` directory. It uses the __file__
        variable to build the path. The `dist` directory may not exist yet.

        Returns:
        str: Absolute path of the expected location of the `dist` directory.

        """

        return path.abspath(path.join(path.dirname(__file__), "..", "dist"))

    @staticmethod
    def GetHostDpkgArchitecture() -> str:
        value = subprocess.check_output(
            ["dpkg", "--print-architecture"],
            text=True)

        return value.strip()


class InvocationContext:
    @staticmethod
    def GatherInformation():
        parser = ArgumentParser()
        args = parser.parse_args()
        hostDpkgArchitecture = ExecutionEnvironment.GetHostDpkgArchitecture()
        context = InvocationContext(args, hostDpkgArchitecture)

        return context

    def __init__(self, args: argparse.Namespace, hostDpkgArchitecture: str):
        self.VerboseOutput: bool = args.VerboseOutput

        self.SourceVersion: str = args.SourceVersion
        majorVersion, minorVersion = self.__ParseDotnetVersion()
        self.DotnetMajorVersion: int = majorVersion
        self.DotnetMinorVersion: int = minorVersion
        self.DotnetMajorMinorVersion: str = f"{majorVersion}.{minorVersion}"

        self.GitRepository: str = args.GitRepository
        self.GitReference: str = args.GitReference
        self.GitReferenceRepository: str | None = args.GitReferenceRepository

        if self.GitRepository == DotnetSecurityPartnersRepositoryUrl():
            if args.SecurityPartnersRepositoryAccessToken is not None:
                accessToken = args.SecurityPartnersRepositoryAccessToken
            else:
                accessToken = os.environ.get("DOTNET_SECURITY_PARTNERS_REPOSITORY_ACCESS_TOKEN")  # noqa: E501

                if self.VerboseOutput and accessToken is not None:
                    print("Used .NET security partners repository "
                          "access token from environment variable.",
                          flush=True)

            if accessToken is not None:
                self.GitRepository = DotnetSecurityPartnersRepositoryUrl(accessToken)  # noqa: E501
        elif args.SecurityPartnersRepositoryAccessToken:
            LogWarning("Specified .NET security partners repository "
                       "access token was not used")

        self.ReleaseManifestFormat: str | None = None

        if args.ForceNoManifest:
            self.ReleaseManifestFormat = None
        elif args.ForceUseJsonManifestFormat:
            self.ReleaseManifestFormat = "json"
        elif args.ForceUseLegacyManifestFormat:
            self.ReleaseManifestFormat = "legacy"
        elif self.DotnetMajorVersion >= 10:
            self.ReleaseManifestFormat = "json"
        elif self.DotnetMajorVersion >= 8:
            self.ReleaseManifestFormat = "legacy"

        self.VendorName: str | None = args.VendorName
        self.SourceLinkRepository: str | None = args.SourceLinkRepository

        self.BuildId: str | None = args.BuildId
        if self.BuildId is not None and self.BuildId.strip() == "":
            self.BuildId = None

        self.HostDpkgArchitecture: str = hostDpkgArchitecture
        self.BootstrapSdkArchitecture: str | None = None

        if args.IncludeBootstrapSdk:
            if args.BootstrapSdkArchitecture is None:
                LogWarning("No bootstrap architecture specified. "
                           "Using host architecture "
                           f"'{self.HostDpkgArchitecture}'.")
                self.BootstrapSdkArchitecture = self.HostDpkgArchitecture
            else:
                self.BootstrapSdkArchitecture = args.BootstrapSdkArchitecture
        elif args.BootstrapSdkArchitecture is not None:
            LogErrorAndExit("Option --bootstrap-sdk-architecture is "
                            "specified without option "
                            "--include-bootstrap-sdk")

        self.SourcePackageName: str = self.__GetSourcePackageName()
        self.OutputDirectory: str = path.abspath(args.OutputDirectory)
        self.TarballName: str = self.__GetTarballName(args.TarballName)
        self.OutputTarballFilePath: str = self.__GetOutputTarballFilePath()

        self.DotnetRoot: str | None = self.__FindMatchingDotnetSdk()
        self.SourceBuiltArtifactsTarball: str | None = self.__FindMatchingSourceBuiltArtifactsTarball()  # noqa: E501

        self.GitRepositoryClonePath: str = self.__GenerateTmpGitRepositoryClonePath()  # noqa: E501

    def __ParseDotnetVersion(self):
        match = re.search(
            r"^(?P<majorVersion>\d+)\.(?P<minorVersion>\d+)(?=\.)",
            self.SourceVersion)

        if match is None:
            LogErrorAndExit(f"Source version '{self.SourceVersion}' is not "
                            "a valid FO127 compliant version string.\n"
                            "See: " + FO127_SPEC_URL)

        majorVersion = int(match.group("majorVersion"))
        minorVersion = int(match.group("minorVersion"))

        return majorVersion, minorVersion

    def __GetSourcePackageName(self) -> str:
        name = f"dotnet{self.DotnetMajorVersion}"

        if self.DotnetMinorVersion > 0:
            name += "." + str(self.DotnetMinorVersion)

        return name

    def __GetTarballName(self, parsedTarballName: str | None) -> str:
        if parsedTarballName is not None:
            return parsedTarballName

        tarballName = f"{self.SourcePackageName}_{self.SourceVersion}"

        if self.BootstrapSdkArchitecture is not None:
            tarballName += f"~bootstrap+{self.BootstrapSdkArchitecture}"

        return tarballName

    def __GetOutputTarballFilePath(self) -> str:
        return path.join(
            self.OutputDirectory,
            f"{self.TarballName}.orig.tar.xz")

    def __GenerateTmpGitRepositoryClonePath(self) -> str:
        return tempfile.mkdtemp(
            prefix=f"{self.TarballName}_",
            dir=None)

    def __FindMatchingDotnetSdk(self) -> str | None:
        try:
            env = os.environ.copy()
            env["DOTNET_NOLOGO"] = "true"
            env["DOTNET_SKIP_FIRST_TIME_EXPERIENCE"] = "true"

            sdkList = subprocess.check_output(
                ["dotnet", "--list-sdks"],
                text=True,
                env=env)
        except:  # noqa: E722
            return None

        rePattern = (
            rf"^{self.DotnetMajorVersion}\.{self.DotnetMinorVersion}\..+"
            r"\[(?P<dotnetRoot>.+)/sdk\]$")

        matchingSdk = re.search(rePattern, sdkList, re.MULTILINE)

        if matchingSdk is None:
            return None

        return matchingSdk.group("dotnetRoot")

    def __FindMatchingSourceBuiltArtifactsTarball(self) -> str | None:
        tarballs = glob("/usr/lib/dotnet/source-built-artifacts/"
                        "Private.SourceBuilt.Artifacts."
                        f"{self.DotnetMajorMinorVersion}.1*.tar.gz",
                        root_dir="/")

        match len(tarballs):
            case 1:
                return tarballs[0]
            case 0:
                return None
            case _:
                message = ("multiple matching source built artifacts "
                           "tarballs found:")

                for tarball in tarballs:
                    message += f"\n- '{tarball}'"

                LogWarning(message)
                return None

    def PrintState(self) -> None:
        state = f"""
Source/Output options:
- SourceVersion={self.SourceVersion}
- DotnetMajorVersion={self.DotnetMajorVersion}
- DotnetMinorVersion={self.DotnetMinorVersion}
- SourcePackageName={self.SourcePackageName}
- GitRepository={self.GitRepository}
- GitReference={self.GitReference}
- GitReferenceRepository={self.GitReferenceRepository}
- GitRepositoryClonePath={self.GitRepositoryClonePath}
- OutputDirectory={self.OutputDirectory}
- TarballName={self.TarballName}

Manifest options:
- ReleaseManifestFormat={self.ReleaseManifestFormat}
- SourceLinkRepository={self.SourceLinkRepository}
- VendorName={self.VendorName}
- BuildId={self.BuildId}

Bootstrapping options:
- BootstrapSdkArchitecture={self.BootstrapSdkArchitecture}

Host information:
- HostArchitecture={self.HostDpkgArchitecture}

Dependency information:
- DotnetRoot={self.DotnetRoot}
- SourceBuiltArtifactsTarball={self.SourceBuiltArtifactsTarball}
"""
        print(state, flush=True)


def CheckBootstrappingPrerequisites(context: InvocationContext) -> None:
    match context.BootstrapSdkArchitecture:
        case None:
            return
        case "amd64" | "arm64":
            if context.HostDpkgArchitecture != context.BootstrapSdkArchitecture:  # noqa: E501
                LogErrorAndExit(
                    "You need to run this script on an "
                    f"'{context.BootstrapSdkArchitecture}' host to bootstrap "
                    f"for architecture '{context.BootstrapSdkArchitecture}'. "
                    "Current host architecture is "
                    f"'{context.HostDpkgArchitecture}'.")
        case _:
            LogErrorAndExit("Bootstrapping for architecture "
                            f"'{context.BootstrapSdkArchitecture}' "
                            "is not yet implemented.")


def CheckPrepareScriptPrerequisites(context: InvocationContext) -> None:
    if (context.BootstrapSdkArchitecture is not None
       or context.DotnetMajorVersion < 9):
        return

    if context.DotnetRoot is None:
        LogErrorAndExit("No matching .NET SDK found. Required version: "
                        + context.DotnetMajorMinorVersion)

    if context.SourceBuiltArtifactsTarball is None:
        LogErrorAndExit("No matching .NET source build artifacts tarball "
                        "found. Required version: "
                        + context.DotnetMajorMinorVersion)


def CheckPrerequisites(context: InvocationContext) -> None:
    print("Checking prerequisites...", flush=True)

    CheckBootstrappingPrerequisites(context)
    CheckPrepareScriptPrerequisites(context)

    if context.DotnetMajorVersion >= 10 and context.BuildId is None:
        LogErrorAndExit("No build id provided.")

    if path.exists(context.OutputTarballFilePath):
        LogErrorAndExit("Output tarball file already exists "
                        f"('{context.OutputTarballFilePath}').")

    if (path.exists(context.OutputDirectory)
       and not path.isdir(context.OutputDirectory)):
        LogErrorAndExit("Output directory can not be created, because "
                        "another resource with the same name already "
                        f"exists ('{context.OutputDirectory}').")


def CloneGitRespository(context: InvocationContext) -> None:
    print("Cloning git repository...", flush=True)

    gitCommand = [
        "git",
        "-c", "advice.detachedHead=false",
        "clone",
        "--depth", "1",
        "--branch", context.GitReference
        ]

    if not context.VerboseOutput:
        gitCommand.append("--quiet")

    if context.GitReferenceRepository is not None:
        gitCommand.append("--reference")
        gitCommand.append(context.GitReferenceRepository)
        gitCommand.append("--dissociate")

    gitCommand.append(context.GitRepository)
    gitCommand.append(context.GitRepositoryClonePath)

    subprocess.check_call(gitCommand)


def ExtractSourceBuiltArtifactsTarball(context: InvocationContext) -> str:
    print("Extracting source built artifacts tarball...", flush=True)

    path = tempfile.mkdtemp(prefix=f"{context.SourcePackageName}-artifacts_")
    subprocess.check_call(
        ["tar", "--extract", "--file", context.SourceBuiltArtifactsTarball],
        cwd=path)

    return path


def RunBinaryToolkit(context: InvocationContext) -> None:
    packagesDirectoryPath = ExtractSourceBuiltArtifactsTarball(context)

    print("Running binary toolkit...", flush=True)

    command = [
            "./prep-source-build.sh",
            "--no-artifacts",
            "--no-bootstrap",
            "--no-prebuilts",
            "--no-sdk",
            "--with-sdk", context.DotnetRoot,
            "--with-packages", packagesDirectoryPath
        ]

    env = os.environ.copy()
    env["DOTNET_NOLOGO"] = "true"
    env["DOTNET_SKIP_FIRST_TIME_EXPERIENCE"] = "true"

    subprocess.check_call(command, cwd=context.GitRepositoryClonePath, env=env)

    print("Deleting temporary files...", flush=True)

    dirPath = path.join(context.GitRepositoryClonePath, "artifacts")
    if path.exists(dirPath):
        shutil.rmtree(dirPath, ignore_errors=False)

    dirPath = path.join(context.GitRepositoryClonePath, ".packages")
    if path.exists(dirPath):
        shutil.rmtree(dirPath, ignore_errors=False)

    shutil.rmtree(packagesDirectoryPath, ignore_errors=True)


def RunPrepScript(context: InvocationContext) -> None:
    if context.DotnetMajorVersion < 9:
        scriptFile = "./prep.sh"
    else:
        scriptFile = "./prep-source-build.sh"

    env = os.environ.copy()
    env["DOTNET_NOLOGO"] = "true"
    env["DOTNET_SKIP_FIRST_TIME_EXPERIENCE"] = "true"

    print("Running prep script...", flush=True)
    subprocess.check_call(
        [scriptFile],
        cwd=context.GitRepositoryClonePath,
        env=env)


def RemoveResource(context: InvocationContext,
                   resourcePath: str,
                   absolute: bool = False,
                   isDirectory=False,
                   isFile=False) -> None:
    if absolute:
        relativePath = path.relpath(
            resourcePath,
            context.GitRepositoryClonePath)
    else:
        relativePath = resourcePath
        resourcePath = path.join(
            context.GitRepositoryClonePath,
            relativePath)

    if not path.exists(resourcePath):
        LogWarning("Resource marked for deletion not found "
                   f"('{relativePath}')")
        return

    if isDirectory and not path.isdir(resourcePath):
        LogErrorAndExit(f"Directory marked for deletion is not a directory "
                        f"('{relativePath}')")
    if isFile and not path.isfile(resourcePath):
        LogErrorAndExit(f"File marked for deletion is not a file "
                        f"('{relativePath}')")

    if not isFile and not isDirectory:
        isFile = path.isfile(resourcePath)
        isDirectory = path.isdir(resourcePath)

    try:
        if isFile:
            os.remove(resourcePath)
            if context.VerboseOutput:
                print(f"- removed file '{relativePath}'", flush=True)
        elif isDirectory:
            shutil.rmtree(resourcePath, ignore_errors=False)
            if context.VerboseOutput:
                print(f"- removed directory '{relativePath}'", flush=True)
        else:
            LogErrorAndExit("Resource marked for deletion is neither "
                            f"a file nor a directory ('{relativePath}').")
    except Exception as exception:
        LogErrorAndExit(f"Failed to remove {path}: {exception}")


def RemoveFile(context: InvocationContext,
               filePath: str,
               absolute: bool = False) -> None:
    RemoveResource(context, filePath, absolute, isFile=True)


def RemoveDirectory(context: InvocationContext,
                    dirPath: str,
                    absolute: bool = False) -> None:
    RemoveResource(context, dirPath, absolute, isDirectory=True)


def RemoveUnwantedFiles(context: InvocationContext) -> None:
    print("Removing unwanted files...", flush=True)

    RemoveDirectory(context, "src/runtime/src/tests/JIT/Performance/CodeQuality/Bytemark")  # noqa: E501

    searchPath = path.join(
        context.GitRepositoryClonePath,
        "src/aspnetcore/src/SignalR/clients/java/signalr")
    for resourceName in os.listdir(searchPath):
        if resourceName.startswith("gradle"):
            resourcePath = path.join(searchPath, resourceName)
            RemoveResource(context, resourcePath, absolute=True)

    if context.DotnetMajorVersion > 8:
        return

    RemoveDirectory(context, "src/nuget-client/test/EndToEnd")

    searchPath = path.join(
        context.GitRepositoryClonePath,
        "src/aspnetcore/src")
    for dirPath, dirNames, filNnames in os.walk(searchPath):
        for dirName in dirNames:
            if dirName == "samples":
                sampleDirPath = path.join(dirPath, dirName)
                RemoveDirectory(context, sampleDirPath, absolute=True)

    searchPath = path.join(
        context.GitRepositoryClonePath,
        "src/roslyn/src/Compilers/Test/Resources")
    for dirPath, dirNames, fileNames in os.walk(searchPath):
        for fileName in fileNames:
            if fileName.endswith(".dll"):
                filePath = path.join(dirPath, fileName)
                RemoveFile(context, filePath, absolute=True)

    # unused prebuilts (see: CPC-1578)
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/DiagnosticTests/ErrTestMod01.netmodule")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/DiagnosticTests/ErrTestMod02.netmodule")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/ExpressionCompiler/LibraryA.winmd")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/ExpressionCompiler/LibraryB.winmd")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/ExpressionCompiler/Windows.Data.winmd")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/ExpressionCompiler/Windows.Storage.winmd")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/ExpressionCompiler/Windows.winmd")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/MetadataTests/Invalid/EmptyModuleTable.netmodule")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/MetadataTests/NetModule01/ModuleCS00.mod")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/MetadataTests/NetModule01/ModuleCS01.mod")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/MetadataTests/NetModule01/ModuleVB01.mod")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/CustomModifiers/Modifiers.netmodule")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/MultiModule/mod2.netmodule")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/MultiModule/mod3.netmodule")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/MultiTargeting/Source1Module.netmodule")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/MultiTargeting/Source3Module.netmodule")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/MultiTargeting/Source4Module.netmodule")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/MultiTargeting/Source5Module.netmodule")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/MultiTargeting/Source7Module.netmodule")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/RetargetingCycle/V1/ClassB.netmodule")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/TypeForwarders/Forwarded.netmodule")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/V1/MTTestModule1.netmodule")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/V1/MTTestModule2.netmodule")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/V2/MTTestModule1.netmodule")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/V2/MTTestModule3.netmodule")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/V3/MTTestModule1.netmodule")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/V3/MTTestModule4.netmodule")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/With Spaces.netmodule")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/netModule/CrossRefModule1.netmodule")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/netModule/CrossRefModule2.netmodule")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/netModule/hash_module.netmodule")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/netModule/netModule1.netmodule")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/netModule/netModule2.netmodule")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/WinRt/W1.winmd")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/WinRt/W2.winmd")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/WinRt/WB.winmd")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/WinRt/WB_Version1.winmd")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/WinRt/WImpl.winmd")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/WinRt/WinMDPrefixing.winmd")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/WinRt/Windows.Languages.WinRTTest.winmd")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/Compilers/Test/Resources/Core/WinRt/Windows.winmd")  # noqa: E501
    RemoveFile(context, "src/roslyn/src/ExpressionEvaluator/Core/Source/ExpressionCompiler/Resources/WindowsProxy.winmd")  # noqa: E501
    RemoveFile(context, "src/runtime/src/libraries/System.Reflection.Metadata/tests/Resources/NetModule/ModuleCS00.mod")  # noqa: E501
    RemoveFile(context, "src/runtime/src/libraries/System.Reflection.Metadata/tests/Resources/NetModule/ModuleCS01.mod")  # noqa: E501
    RemoveFile(context, "src/runtime/src/libraries/System.Reflection.Metadata/tests/Resources/NetModule/ModuleVB01.mod")  # noqa: E501
    RemoveFile(context, "src/runtime/src/libraries/System.Reflection.Metadata/tests/Resources/WinRT/Lib.winmd")  # noqa: E501
    RemoveFile(context, "src/cecil/Test/Resources/assemblies/ManagedWinmd.winmd")  # noqa: E501
    RemoveFile(context, "src/cecil/Test/Resources/assemblies/NativeWinmd.winmd")  # noqa: E501
    RemoveFile(context, "src/cecil/Test/Resources/assemblies/moda.netmodule")
    RemoveFile(context, "src/cecil/Test/Resources/assemblies/modb.netmodule")
    RemoveFile(context, "src/cecil/Test/Resources/assemblies/winrtcomp.winmd")


def GetHeadCommitSha1Hash(context: InvocationContext) -> str:
    output = subprocess.check_output(
        ["git", "rev-parse", "--verify", "HEAD"],
        cwd=context.GitRepositoryClonePath,
        text=True)
    return output.strip()


def CreateReleaseManifest(context: InvocationContext) -> None:
    if context.ReleaseManifestFormat is None:
        return

    sourceRepository = context.SourceLinkRepository
    sourceVersion = GetHeadCommitSha1Hash(context)
    buildIdUnused = False

    if context.ReleaseManifestFormat == "legacy":
        releaseManifestFileName = "release.info"
        releaseManifestFileContent = (
            f"RM_GIT_REPO={sourceRepository}\n"
            f"RM_GIT_COMMIT={sourceVersion}")

        buildIdUnused = context.BuildId is not None
    elif context.ReleaseManifestFormat == "json":
        releaseManifestFileName = "release.json"
        releaseManifestData = {
            "sourceRepository": sourceRepository,
            "sourceVersion": sourceVersion,
            "vendor": context.VendorName
        }

        if context.DotnetMajorVersion >= 10:
            if context.BuildId is None:
                LogErrorAndExit("No build id provided. .NET 10+ requires "
                                "an official build id.")
            else:
                releaseManifestData["officialBuildId"] = context.BuildId
        else:
            buildIdUnused = context.BuildId is not None

        releaseManifestFileContent = json.dumps(releaseManifestData, indent=4)
    else:
        LogErrorAndExit("Unsupported release manifest format "
                        f"'{context.ReleaseManifestFormat}'.")

    if buildIdUnused:
        LogWarning(f"Build id '{context.BuildId}' is unused")

    releaseManifestFilePath = path.join(
        context.GitRepositoryClonePath,
        releaseManifestFileName)

    print("Creating release manifest...", flush=True)

    if context.VerboseOutput:
        print(releaseManifestFileContent, flush=True)

    with open(releaseManifestFilePath, "w") as releaseManifestFile:
        releaseManifestFile.write(releaseManifestFileContent)


def RemoveDotGitDirectory(context: InvocationContext) -> None:
    gitDirectory = path.join(context.GitRepositoryClonePath, ".git")
    shutil.rmtree(gitDirectory, ignore_errors=False)


def PrepareForSourceBuild(context: InvocationContext) -> None:
    match context.BootstrapSdkArchitecture:
        case None:
            if context.DotnetMajorVersion >= 9:
                # NOTE: The BinaryToolkit was introduced with .NET 9
                RunBinaryToolkit(context)
        case "amd64" | "arm64":
            # NOTE: The prep scrip will run the BinaryToolkit for .NET 9+
            RunPrepScript(context)
        case _:
            # NOTE: When implementing this make sure that you run the
            #       BinaryToolkit! See eng/detect-binaries.sh in a
            #       .NET 9+ source tree for moore details.
            LogErrorAndExit("Bootstrapping for architecture "
                            f"'{context.BootstrapSdkArchitecture}' "
                            "is not yet implemented.")

    RemoveUnwantedFiles(context)
    CreateReleaseManifest(context)
    RemoveDotGitDirectory(context)


def CreateOrigTarball(context: InvocationContext) -> None:
    print("Creating orig tarball (this may take a while)...", flush=True)

    if not path.exists(context.OutputDirectory):
        os.mkdir(context.OutputDirectory)

    command = [
            "tar",
            "--create",
            "--xz",
            "--file", context.OutputTarballFilePath,
            "."
        ]

    subprocess.check_call(args=command, cwd=context.GitRepositoryClonePath)

    print(f"Orig tarball created at: '{context.OutputTarballFilePath}'",
          flush=True)


def DeleteTmpFiles(context: InvocationContext) -> None:
    print("Cleaning temporary files... ", flush=True)
    shutil.rmtree(context.GitRepositoryClonePath, ignore_errors=True)


def Main():
    context = InvocationContext.GatherInformation()

    if context.VerboseOutput:
        context.PrintState()

    CheckPrerequisites(context)
    CloneGitRespository(context)
    PrepareForSourceBuild(context)
    CreateOrigTarball(context)

    DeleteTmpFiles(context)


Main()
