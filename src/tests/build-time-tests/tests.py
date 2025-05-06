#!/usr/bin/env python3

import argparse
import os
import sys
import subprocess
import tempfile
import re
import shutil

sys.path.append("debian/eng")

from versionlib.dotnet import SourcePackageVersion, RuntimeIdentifier  # noqa: E402, E501
from source_build_artifact_path import GetSourceBuiltArtifactsTarball  # noqa: E402, E501


def ParseArguments():
    class MultiStoreTrue(argparse.Action):
        def __init__(self,
                     option_strings,
                     dest,
                     help=None):
            super(MultiStoreTrue, self).__init__(
                option_strings=option_strings,
                dest=dest,
                nargs=0,
                const=None,
                default=None,
                required=False,
                help=help)

        def __call__(self, parser, namespace, values, option_string=None):
            for destination in self.dest.split(','):
                setattr(namespace, destination, True)

    argumentParser = argparse.ArgumentParser(
        description="Runs the minimal smoke test suite designed to run "
                    "during build time.",
        epilog="See the README file for further details.")

    argumentParser.add_argument("-v", "--verbose", "--debug",
                                action="store_true",
                                dest="Verbose",
                                help="log debug information")
    argumentParser.add_argument("--clean-sdk",
                                action=argparse.BooleanOptionalAction,
                                default=False,
                                dest="CleanSDK",
                                help="deletes SDK artifacts of a previous "
                                     "test run before executing the minimal "
                                     "smoke test suite")
    argumentParser.add_argument("--clean-packages",
                                action=argparse.BooleanOptionalAction,
                                default=False,
                                dest="CleanPackages",
                                help="deletes NuGet package artifacts of a"
                                     "previous test run before executing the "
                                     "minimal smoke test suite")
    argumentParser.add_argument("--clean-home",
                                action=argparse.BooleanOptionalAction,
                                default=False,
                                dest="CleanHome",
                                help="deletes the fake HOME directory of a"
                                     "previous test run before executing the "
                                     "minimal smoke test suite")
    argumentParser.add_argument("--clean-test-project",
                                action=argparse.BooleanOptionalAction,
                                default=False,
                                dest="CleanTestProject",
                                help="deletes the test project of a"
                                     "previous test run before executing the "
                                     "minimal smoke test suite")
    argumentParser.add_argument("--clean-all",
                                action=MultiStoreTrue,
                                dest="CleanSDK,"
                                     "CleanPackages,"
                                     "CleanHome,"
                                     "CleanTestProject",
                                help="equivalent to setting all --clean-* "
                                     "flags")
    argumentParser.add_argument("--force-clean",
                                action=argparse.BooleanOptionalAction,
                                default=False,
                                dest="ForceClean",
                                help="warnings do not stop the execution of "
                                     "clean actions")
    argumentParser.add_argument("--purge-after",
                                action=argparse.BooleanOptionalAction,
                                default=False,
                                dest="PurgeAfter",
                                help="purge the minimal smoke test suite "
                                     "files after a successful test run")
    argumentParser.add_argument("--test-directory",
                                metavar="PATH",
                                dest="TestDirectory",
                                help="the root directory that is used for "
                                     "generating files while running the "
                                     "minimal smoke test suite (default: "
                                     "a temporary directory will be created)")
    argumentParser.add_argument("--source-package-root",
                                metavar="PATH",
                                dest="SourcePackageRoot",
                                help="the root directory of the source package"
                                     " (default: current working directory)")

    return argumentParser.parse_args()


class TestContext:
    def __init__(
            self,
            verbose: bool,
            cleanSdk: bool,
            cleanPackages: bool,
            cleanHome: bool,
            cleanTestProject: bool,
            forceClean: bool,
            purgeAfter: bool,
            testDirectory: str | None,
            sourcePackageRoot: str | None) -> None:
        self.Verbose = verbose
        self.CleanSDK = cleanSdk
        self.CleanPackages = cleanPackages
        self.CleanHome = cleanHome
        self.CleanTestProject = cleanTestProject
        self.ForceClean = forceClean
        self.PurgeAfter = purgeAfter
        self.TestDirectory = testDirectory
        self.SourcePackageRoot = sourcePackageRoot

        self.LogDebug("Parameters:\n"
                      f"- Verbose: {self.Verbose}\n"
                      f"- CleanSDK: {self.CleanSDK}\n"
                      f"- CleanPackages: {self.CleanPackages}\n"
                      f"- CleanHome: {self.CleanHome}\n"
                      f"- CleanTestProject: {self.CleanTestProject}\n"
                      f"- ForceClean: {self.ForceClean}\n"
                      f"- PurgeAfter: {self.PurgeAfter}\n"
                      f"- TestDirectory: {self.TestDirectory}\n"
                      f"- SourcePackageRoot: {self.SourcePackageRoot}")

        self.__CheckSourcePackageRoot()

        version: SourcePackageVersion = \
            SourcePackageVersion.ParseFromChangelog(
                os.path.join(self.SourcePackageRoot, "debian", "changelog"))

        runtimeIdentifier = RuntimeIdentifier.FromPlatformData()

        self.DotnetSdkVersion = str(version.SdkVersion)
        self.DotnetRuntimeVersion = str(version.RuntimeVersion)
        self.DotnetRuntimeIdentifier = str(runtimeIdentifier)
        self.DotnetTargetFramework = f"net{version.SdkVersion.Major}.{version.SdkVersion.Minor}"
        self.DotnetArchitecture = str(runtimeIdentifier.ArchitectureIdentifier)
        self.UbuntuVersion = str(
            runtimeIdentifier.OperatingSystemIdentifier.Version)

        self.__InitializeTestDirectory()

        self.DotnetRoot = os.path.join(
            self.TestDirectory, "dotnet")
        self.NuGetPackagesDirectory = os.path.join(
            self.TestDirectory, "packages")
        self.FakeHome = os.path.join(
            self.TestDirectory, "home")
        self.TestProjectDirectory = os.path.join(
            self.TestDirectory, "test-project")
        self.TestProjectName = "hello"
        self.TestProjectFile = os.path.join(
            self.TestProjectDirectory, f"{self.TestProjectName}.csproj")

        if version.SdkVersion.Major < 9:
            self.DotnetBuiltArtifactsBasePath = (f"{self.SourcePackageRoot}"
                                                 "/artifacts/"
                                                 f"{self.DotnetArchitecture}"
                                                 "/Release")
        else:
            self.DotnetBuiltArtifactsBasePath = (f"{self.SourcePackageRoot}"
                                                 "/artifacts/assets/Release")

        self.LogDebug(
            "Full Context:\n"
            f"- TestDirectory: {self.TestDirectory}\n"
            f"- SourcePackageRoot: {self.SourcePackageRoot}\n"
            f"- DotnetBuiltArtifactsBasePath: {self.DotnetBuiltArtifactsBasePath}\n"  # noqa: E501
            f"- DotnetRoot: {self.DotnetRoot}\n"
            f"- NuGetPackagesDirectory: {self.NuGetPackagesDirectory}\n"
            f"- FakeHome: {self.FakeHome}\n"
            f"- TestProjectDirectory: {self.TestProjectDirectory}\n"
            f"- TestProjectName: {self.TestProjectName}\n"
            f"- TestProjectFile: {self.TestProjectFile}\n"
            f"- UbuntuVersion: {self.UbuntuVersion}\n"
            f"- DotnetSdkVersion: {self.DotnetSdkVersion}\n"
            f"- DotnetRuntimeVersion: {self.DotnetRuntimeVersion}\n"
            f"- DotnetRuntimeIdentifier: {self.DotnetRuntimeIdentifier}\n"
            f"- DotnetTargetFramework: {self.DotnetTargetFramework}\n"
            f"- DotnetArchitecture: {self.DotnetArchitecture}")

    def LogDebug(self, msg) -> None:
        if self.Verbose:
            print("DEBUG: " + msg, flush=True)

    def LogInfo(self, msg) -> None:
        print("INFO: " + msg, flush=True)

    def LogWarning(self, msg) -> None:
        print("WARNING: " + msg, flush=True)

    def LogErrorAndDie(self, msg) -> None:
        print("ERROR: " + msg, file=sys.stderr)
        self.LogWarning("Test directory does not get purged")
        sys.exit(1)

    def __CheckSourcePackageRoot(self):
        if self.SourcePackageRoot is None:
            self.LogDebug("No source package root specified. "
                          "Assuming current working directory.")

            self.SourcePackageRoot = os.path.realpath(os.curdir)
        else:
            if not os.path.isdir(self.SourcePackageRoot):
                self.LogErrorAndDie("Could not find specified source package "
                                    "directory.")

            self.SourcePackageRoot = os.path.realpath(self.SourcePackageRoot)

        debianDirectory = os.path.join(self.SourcePackageRoot, "debian")
        if not os.path.isdir(debianDirectory):
            self.LogErrorAndDie("Source package root does not have a "
                                "debian directory.")

        self.LogInfo(f"SourcePackageRoot='{self.SourcePackageRoot}'")

    def __InitializeTestDirectory(self):
        if self.TestDirectory is None:
            self.LogDebug("No test directory specified. "
                          "Creating temporary directory.")

            self.TestDirectory = tempfile.mkdtemp()
        else:
            if not os.path.isdir(self.TestDirectory):
                self.LogWarning("Could not find specified test directory.")
                self.LogDebug("Attempting to create it...")

                os.makedirs(self.TestDirectory)

            self.TestDirectory = os.path.realpath(self.TestDirectory)

        self.LogInfo(f"TestDirectory='{self.TestDirectory}'")

    def RunTests(self):
        self.__CleanSDK()
        self.__CleanPackages()
        self.__CleanHome()
        self.__CleanTestProject()

        self.__ExtractSdk()

        output = self.__RunDotnet(["--info"])
        self.__ValidateDotnetInfoOutput(output)

        output = self.__RunDotnet(["--version"])
        self.__ValidateDotnetVersionOutput(output)

        output = self.__RunDotnet(["--help"])
        self.__ValidateDotnetHelpOutput(output)

        self.__ExtractPackages()
        self.__CreateTestProject()
        self.__RestoreTestProject()

        dllPath = self.__BuildTestProject()
        output = self.__RunDotnet([dllPath])
        self.__ValidateDotnetTestProjectOutput(output)

        self.LogInfo("Test succeeded!")
        self.__PurgeTestDirectory()

    def __CleanSDK(self) -> None:
        if self.CleanSDK:
            self.__Clean(self.DotnetRoot, ".NET root directory")

    def __CleanPackages(self) -> None:
        if self.CleanPackages:
            self.__Clean(self.NuGetPackagesDirectory,
                         "NuGet packages directory")

    def __CleanHome(self) -> None:
        if self.CleanHome:
            self.__Clean(self.FakeHome,
                         "fake HOME directory")

    def __CleanTestProject(self) -> None:
        if self.CleanTestProject:
            self.__Clean(self.TestProjectDirectory,
                         ".NET test project directory")

    def __Clean(self, path, displayName) -> None:
        if not os.path.exists(path):
            self.LogDebug(f"{displayName} ({path}) not found. "
                          "Nothing to clean.")
            return
        if not os.path.isdir(path):
            self.LogWarning(f"{displayName} ({path}) is a file.")
            self.LogInfo("This is unexpected, because this should be a "
                         "directory from previous test runs and not a file.")

            if self.ForceClean:
                self.LogInfo("Forecfully cleaning file...")
                os.remove(path)
            else:
                sys.exit(1)

        self.LogInfo(f"Cleaning {displayName} ({path}).")
        os.rmdir(path)

    def __ExtractSdk(self) -> None:
        if os.path.exists(self.DotnetRoot):
            self.LogWarning("Dotnet root already exists. "
                            "SDK does not get extracted.")
            self.LogInfo("Consider using the --clean-sdk flag.")
            return

        self.__ExtractGZipTarball(
            tarPath=GetSourceBuiltArtifactsTarball(
                basePath=self.DotnetBuiltArtifactsBasePath,
                sdkVersion=self.DotnetSdkVersion,
                type="SDK"),
            humanReadableName=".NET SDK build artifacts",
            targetDirectory=self.DotnetRoot)

    def __ExtractPackages(self) -> None:
        if os.path.exists(self.NuGetPackagesDirectory):
            self.LogWarning("NuGet packages already exist. NuGet packages do "
                            "NOT get extracted.")
            self.LogInfo("Consider using the --clean-packages flag.")
            return

        self.__ExtractGZipTarball(
            tarPath=GetSourceBuiltArtifactsTarball(
                basePath=self.DotnetBuiltArtifactsBasePath,
                sdkVersion=self.DotnetSdkVersion),
            humanReadableName="NuGet packages artifacts",
            targetDirectory=self.NuGetPackagesDirectory)

    def __ExtractGZipTarball(
            self,
            tarPath: str,
            humanReadableName: str,
            targetDirectory: str) -> None:
        if not os.path.exists(tarPath):
            self.LogErrorAndDie(f"Could not find tarball {tarPath}")

        self.LogDebug(f"Creating target directory ('{targetDirectory}')")
        os.mkdir(targetDirectory)

        self.LogInfo(f"Extracting {humanReadableName} tarball")
        self.LogDebug(f"- tarPath='{tarPath}'")
        self.LogDebug(f"- targetDirectory='{targetDirectory}'")

        if self.Verbose:
            stdout = None  # no redirection; print to stdout
        else:
            stdout = subprocess.DEVNULL

        try:
            subprocess.check_call(["tar", "--extract", "--gzip",
                                   "--file", tarPath,
                                   "--directory", targetDirectory],
                                  stdout=stdout)
        except subprocess.CalledProcessError as error:
            self.LogErrorAndDie(f"Extraction of {humanReadableName} failed "
                                f"(ExitCode {error.returncode})!")

    def __RunDotnet(self, args: [str]) -> None:
        args = [f"{self.DotnetRoot}/dotnet"] + args

        env = {
            'HOME': self.FakeHome,
            'DOTNET_ROOT': self.DotnetRoot,
            'DOTNET_NOLOGO': 'true',
            'DOTNET_SKIP_FIRST_TIME_EXPERIENCE': 'true'
            }

        self.LogDebug("Executing: " + str(args))
        try:
            output = subprocess.check_output(cwd=self.TestDirectory,
                                             stderr=subprocess.STDOUT,
                                             args=args, env=env, text=True)
        except subprocess.CalledProcessError as error:
            self.LogErrorAndDie("Execution failure!\n"
                                f"- Exit Code: {error.returncode}\n"
                                f"- Args: {str(args)}\n"
                                f"- Output:\n{error.output}")

        self.LogInfo(f"Output:\n=======\n{output}")
        return output

    def __CreateTestProject(self) -> None:
        if os.path.exists(self.TestProjectDirectory):
            self.LogWarning("Test project already exist. Test project "
                            "does NOT get created.")
            self.LogInfo("Consider using the --clean-test-project flag.")
            return

        self.LogDebug("Creating test project from C# .NET console template.")
        self.__RunDotnet(["new", "console", "--no-restore",
                          "--name", self.TestProjectName,
                          "--output", self.TestProjectDirectory])

    def __RestoreTestProject(self) -> None:
        self.LogDebug("Restore test project dependencies.")
        self.__RunDotnet(["restore",
                          "--source", self.NuGetPackagesDirectory,
                          self.TestProjectDirectory])

    def __BuildTestProject(self) -> str:
        self.LogDebug("Build test project binaries.")
        self.__RunDotnet(["build", "--no-restore", self.TestProjectFile])

        dllPath = (f"{self.TestProjectDirectory}/bin/Debug/{self.DotnetTargetFramework}/"
                  f"{self.TestProjectName}.dll")

        return dllPath

    def __ValidateDotnetHelpOutput(self, output: str) -> None:
        if len(output) == 0:
            self.LogErrorAndDie(".NET help output is empty")

    def __ValidateDotnetVersionOutput(self, output: str) -> None:
        if len(output) == 0:
            self.LogErrorAndDie(".NET version output is empty")

        match = re.match(rf"^{re.escape(self.DotnetSdkVersion)}(\..+)?\s*$",
                         output, re.DOTALL | re.MULTILINE)
        if match is None:
            self.LogErrorAndDie(".NET version output does not match the SDK "
                                "version number "
                                f"(expected: '{self.DotnetSdkVersion}', "
                                f"actual: '{output}').")

    def __ValidateOutputMatchesPattern(
            self,
            value: str,
            pattern: str,
            description: str) -> None:
        self.LogDebug(f"Testing {description}\n- pattern='{pattern}'")
        match = re.match(pattern, value, re.DOTALL)

        if match is None:
            self.LogErrorAndDie(f"{description} output does not match the "
                                f"expected pattern ('{pattern}').")

    def __ValidateDotnetInfoOutput(self, output):
        if len(output) == 0:
            self.LogErrorAndDie(".NET info output is empty")

        UbuntuVersion = re.escape(self.UbuntuVersion)
        DotnetSdkVersion = re.escape(self.DotnetSdkVersion)
        DotnetRuntimeVersion = re.escape(self.DotnetRuntimeVersion)
        DotnetRuntimeIdentifier = re.escape(self.DotnetRuntimeIdentifier)
        DotnetArchitecture = re.escape(self.DotnetArchitecture)
        DotnetRoot = re.escape(self.DotnetRoot)

        self.__ValidateOutputMatchesPattern(
            output,
            pattern=r".*"
            r"\.NET SDK( \(reflecting any global\.json\))?:.+"
            rf"Version:\s+{DotnetSdkVersion}.+"
            r"Commit:\s+[a-f0-9]{10}",
            description=".NET SDK info")

        self.__ValidateOutputMatchesPattern(
            output,
            pattern=r".*"
            r"Runtime Environment:.+"
            r"OS Name:\s+ubuntu.+"
            rf"OS Version:\s+{UbuntuVersion}.+"
            r"OS Platform:\s+Linux.+"
            rf"RID:\s+{DotnetRuntimeIdentifier}.+"
            rf"Base Path:\s+{DotnetRoot}/sdk/{DotnetSdkVersion}(\..+)?/",
            description=".NET runtime info")

        self.__ValidateOutputMatchesPattern(
            output,
            pattern=r".*"
            r"Host:.+"
            rf"Version:\s+{DotnetRuntimeVersion}(\..+)?.+"
            rf"Architecture:\s+{DotnetArchitecture}.+"
            r"Commit:\s+([a-f0-9]{10}|static)",
            description=".NET host info")

        self.__ValidateOutputMatchesPattern(
            output,
            pattern=r".*"
            r".NET SDKs installed:.+"
            rf"{DotnetSdkVersion}(\..+)? \[{DotnetRoot}/sdk\]",
            description=".NET SDK install info")

        self.__ValidateOutputMatchesPattern(
            output,
            pattern=r".*"
            r".NET runtimes installed:.+"
            rf"Microsoft\.AspNetCore\.App\s+{DotnetRuntimeVersion}(\..+)?\s+"
            rf"\[{DotnetRoot}/shared/Microsoft\.AspNetCore\.App\].+"
            rf"Microsoft\.NETCore\.App\s+{DotnetRuntimeVersion}(\..+)?\s+"
            rf"\[{DotnetRoot}/shared/Microsoft\.NETCore\.App\]",
            description=".NET runtime install info")

    def __ValidateDotnetTestProjectOutput(self, output: str) -> None:
        if len(output) == 0:
            self.LogErrorAndDie("dotnet test project output is empty")

        match = re.match(r"^Hello, World!\s*$", output,
                         re.DOTALL | re.MULTILINE)

        if match is None:
            print("Hexdump:")
            for index, char in enumerate(output):
                print(f"{index}: {hex(ord(char))} {ord(char)} '{char}'")

            self.LogErrorAndDie(".NET test project does not output "
                                "\"Hello, World!\".")

    def __PurgeTestDirectory(self) -> None:
        if not self.PurgeAfter:
            return

        self.LogDebug(f"Purging test directory ({self.TestDirectory})")

        try:
            shutil.rmtree(self.TestDirectory, ignore_errors=True)
        except:  # noqa: E722
            self.LogWarning("While pruging the test directory "
                            "an exception occured.")


arguments = ParseArguments()
testContext = TestContext(verbose=arguments.Verbose,
                          cleanSdk=arguments.CleanSDK,
                          cleanPackages=arguments.CleanPackages,
                          cleanHome=arguments.CleanHome,
                          cleanTestProject=arguments.CleanTestProject,
                          forceClean=arguments.ForceClean,
                          purgeAfter=arguments.PurgeAfter,
                          testDirectory=arguments.TestDirectory,
                          sourcePackageRoot=arguments.SourcePackageRoot)
testContext.RunTests()
