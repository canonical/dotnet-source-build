import unittest
import sys
import os

sys.path.append("debian/eng")
from versionlib.dotnet import RuntimeVersion, SdkVersion, SourcePackageVersion, PrereleaseVersion, PreReleaseType  # noqa: E402, E501


class TestSourcePackageVersionParsing(unittest.TestCase):
    def test_When_ParsingFO127NonCompliantDotnetSourcePackageVersion1_Should_BeRecognizedCorrectly(self):  # noqa: E501
        version = SourcePackageVersion.Parse("7.0.100-0ubuntu1")

        self.assertEqual(version.Raw, "7.0.100-0ubuntu1")
        self.assertEqual(version.IsFO127Compliant, False)

        self.assertEqual(version.SdkVersion.Major, 7)
        self.assertEqual(version.SdkVersion.Minor, 0)
        self.assertEqual(version.SdkVersion.FeatureBand, 100)
        self.assertEqual(version.SdkVersion.Patch, 0)
        self.assertEqual(version.SdkVersion.PreReleaseVersion, None)
        self.assertEqual(version.SdkVersion, SdkVersion(7,0,100,0, None))
        self.assertEqual(version.SdkVersion.DebRepresentation(), "7.0.100")

        self.assertEqual(version.RuntimeVersion.Major, 7)
        self.assertEqual(version.RuntimeVersion.Minor, 0)
        self.assertEqual(version.RuntimeVersion.Patch, 0)
        self.assertEqual(version.RuntimeVersion.PreReleaseVersion, None)
        self.assertEqual(version.RuntimeVersion, RuntimeVersion(7,0,0, None))
        self.assertEqual(version.RuntimeVersion.DebRepresentation(), "7.0.0")

        self.assertEqual(version.DebRevision.DebianRevision, "0")
        self.assertEqual(version.DebRevision.UbuntuRevision, "1")
        self.assertEqual(version.BootstrapArchitecture, None)
        self.assertEqual(version.OverwrittenVersion, None)

    def test_When_ParsingFO127NonCompliantDotnetSourcePackageVersion2_Should_BeRecognizedCorrectly(self):  # noqa: E501
        version = SourcePackageVersion.Parse(
            "999.999.999~preview999.999-999~prefix999ubuntu999~postfix999")

        self.assertEqual(
            version.Raw,
            "999.999.999~preview999.999-999~prefix999ubuntu999~postfix999")
        self.assertEqual(version.IsFO127Compliant, False)

        self.assertEqual(version.SdkVersion.Major, 999)
        self.assertEqual(version.SdkVersion.Minor, 999)
        self.assertEqual(version.SdkVersion.FeatureBand, 900)
        self.assertEqual(version.SdkVersion.Patch, 99)
        self.assertEqual(version.SdkVersion.PreReleaseVersion.Type,
                         PreReleaseType.Preview)
        self.assertEqual(version.SdkVersion.PreReleaseVersion.Revision, 999)
        self.assertEqual(version.SdkVersion.PreReleaseVersion.BuildMetadata,
                         ["999"])
        self.assertEqual(version.SdkVersion, SdkVersion(999,999,900,99, PrereleaseVersion(PreReleaseType.Preview, 999, ["999"])))
        self.assertEqual(version.SdkOnlyDebVersion(), "999.999.999~preview999.999-999~prefix999ubuntu999~postfix999")
        self.assertEqual(version.SdkOnlyDebVersion(buildSuffix="+build1"), "999.999.999~preview999.999+build1-999~prefix999ubuntu999~postfix999")

        self.assertEqual(version.RuntimeVersion.Major, 999)
        self.assertEqual(version.RuntimeVersion.Minor, 999)
        self.assertEqual(version.RuntimeVersion.Patch, 99)
        self.assertEqual(version.RuntimeVersion.PreReleaseVersion.Type,
                         PreReleaseType.Preview)
        self.assertEqual(version.RuntimeVersion.PreReleaseVersion.Revision,
                         999)
        self.assertEqual(version
                         .RuntimeVersion.PreReleaseVersion.BuildMetadata,
                         ["999"])
        self.assertEqual(version.RuntimeVersion, RuntimeVersion(999,999,99, PrereleaseVersion(PreReleaseType.Preview, 999, ["999"])))
        self.assertEqual(version.RuntimeOnlyDebVersion(), "999.999.99~preview999.999-999~prefix999ubuntu999~postfix999")
        self.assertEqual(version.RuntimeOnlyDebVersion(buildSuffix="+build1"), "999.999.99~preview999.999+build1-999~prefix999ubuntu999~postfix999")

        self.assertEqual(version.DebRevision.DebianRevision, "999~prefix999")
        self.assertEqual(version.DebRevision.UbuntuRevision, "999~postfix999")
        self.assertEqual(version.BootstrapArchitecture, None)
        self.assertEqual(version.OverwrittenVersion, None)

    def test_When_ParsingFO127CompliantDotnetSourcePackageVersion1_Should_BeRecognizedCorrectly(self):  # noqa: E501
        version = SourcePackageVersion.Parse(
            "8.0.100-8.0.0~rc1-0ubuntu1")

        self.assertEqual(version.Raw, "8.0.100-8.0.0~rc1-0ubuntu1")
        self.assertEqual(version.IsFO127Compliant, True)

        self.assertEqual(version.SdkVersion.Major, 8)
        self.assertEqual(version.SdkVersion.Minor, 0)
        self.assertEqual(version.SdkVersion.FeatureBand, 100)
        self.assertEqual(version.SdkVersion.Patch, 0)
        self.assertEqual(version.SdkVersion.PreReleaseVersion.Type,
                         PreReleaseType.ReleaseCandidate)
        self.assertEqual(version.SdkVersion.PreReleaseVersion.Revision, 1)
        self.assertEqual(version.SdkVersion.PreReleaseVersion.BuildMetadata,
                         None)
        self.assertEqual(version.SdkVersion, SdkVersion(8, 0, 100, 0, PrereleaseVersion(PreReleaseType.ReleaseCandidate, 1, None)))
        self.assertEqual(version.SdkOnlyDebVersion(), "8.0.100~rc1-0ubuntu1")
        self.assertEqual(version.SdkOnlyDebVersion(buildSuffix="+build1"), "8.0.100~rc1+build1-0ubuntu1")

        self.assertEqual(version.RuntimeVersion.Major, 8)
        self.assertEqual(version.RuntimeVersion.Minor, 0)
        self.assertEqual(version.RuntimeVersion.Patch, 0)
        self.assertEqual(version.RuntimeVersion.PreReleaseVersion.Type,
                         PreReleaseType.ReleaseCandidate)
        self.assertEqual(version.RuntimeVersion.PreReleaseVersion.Revision, 1)
        self.assertEqual(version
                         .RuntimeVersion.PreReleaseVersion.BuildMetadata, None)
        self.assertEqual(version.RuntimeVersion, RuntimeVersion(8, 0, 0, PrereleaseVersion(PreReleaseType.ReleaseCandidate, 1, None)))
        self.assertEqual(version.RuntimeOnlyDebVersion(), "8.0.0~rc1-0ubuntu1")
        self.assertEqual(version.RuntimeOnlyDebVersion(buildSuffix="+build1"), "8.0.0~rc1+build1-0ubuntu1")

        self.assertEqual(version.DebRevision.DebianRevision, "0")
        self.assertEqual(version.DebRevision.UbuntuRevision, "1")
        self.assertEqual(version.BootstrapArchitecture, None)
        self.assertEqual(version.OverwrittenVersion, None)

    def test_When_ParsingDotnetSourcePackageVersionFromChangelog_Should_BeRecognizedCorrectly(self):   # noqa: E501
        testRoot = os.path.dirname(os.path.realpath(__file__))

        version = SourcePackageVersion.ParseFromChangelog(
            os.path.join(testRoot, "changelog.mock"))

        self.assertEqual(version.Raw, "8.0.100-8.0.0~rc1-0ubuntu1~test1")
        self.assertEqual(version.IsFO127Compliant, True)

        self.assertEqual(version.SdkVersion.Major, 8)
        self.assertEqual(version.SdkVersion.Minor, 0)
        self.assertEqual(version.SdkVersion.FeatureBand, 100)
        self.assertEqual(version.SdkVersion.Patch, 0)
        self.assertEqual(version.SdkVersion.PreReleaseVersion.Type,
                         PreReleaseType.ReleaseCandidate)
        self.assertEqual(version.SdkVersion.PreReleaseVersion.Revision, 1)
        self.assertEqual(version.SdkVersion.PreReleaseVersion.BuildMetadata,
                         None)
        self.assertEqual(version.SdkVersion, SdkVersion(8, 0, 100, 0, PrereleaseVersion(PreReleaseType.ReleaseCandidate, 1, None)))
        self.assertEqual(version.SdkOnlyDebVersion(), "8.0.100~rc1-0ubuntu1~test1")
        self.assertEqual(version.SdkOnlyDebVersion(buildSuffix="+build1"), "8.0.100~rc1+build1-0ubuntu1~test1")

        self.assertEqual(version.RuntimeVersion.Major, 8)
        self.assertEqual(version.RuntimeVersion.Minor, 0)
        self.assertEqual(version.RuntimeVersion.Patch, 0)
        self.assertEqual(version.RuntimeVersion.PreReleaseVersion.Type,
                         PreReleaseType.ReleaseCandidate)
        self.assertEqual(version.RuntimeVersion.PreReleaseVersion.Revision, 1)
        self.assertEqual(version
                         .RuntimeVersion.PreReleaseVersion.BuildMetadata, None)
        self.assertEqual(version.RuntimeVersion, RuntimeVersion(8, 0, 0, PrereleaseVersion(PreReleaseType.ReleaseCandidate, 1, None)))
        self.assertEqual(version.RuntimeOnlyDebVersion(), "8.0.0~rc1-0ubuntu1~test1")
        self.assertEqual(version.RuntimeOnlyDebVersion(buildSuffix="+build1"), "8.0.0~rc1+build1-0ubuntu1~test1")

        self.assertEqual(version.DebRevision.DebianRevision, "0")
        self.assertEqual(version.DebRevision.UbuntuRevision, "1~test1")
        self.assertEqual(version.BootstrapArchitecture, None)
        self.assertEqual(version.OverwrittenVersion, None)

    def test_When_ParsingChangelogOfCurrentPackage_Should_RaiseNoError(self):   # noqa: E501
        testRoot = os.path.dirname(os.path.realpath(__file__))

        SourcePackageVersion.ParseFromChangelog(
            os.path.join(testRoot, os.pardir, os.pardir, "changelog"))

    def test_When_ParsingOverwrittenVersionString_Should_BeRecognizedCorrectly(self):  # noqa: E501
        version = SourcePackageVersion.Parse(
            "8.0.100-8.0.0~rc1+really7.0.100-7.0.0~beta1~bootstrap+amd64-0ubuntu1")  # noqa: E501

        self.assertEqual(version.Raw, "8.0.100-8.0.0~rc1+really7.0.100-7.0.0~beta1~bootstrap+amd64-0ubuntu1")  # noqa: E501
        self.assertEqual(version.IsFO127Compliant, True)

        self.assertEqual(version.SdkVersion.Major, 7)
        self.assertEqual(version.SdkVersion.Minor, 0)
        self.assertEqual(version.SdkVersion.FeatureBand, 100)
        self.assertEqual(version.SdkVersion.Patch, 0)
        self.assertEqual(version.SdkVersion.PreReleaseVersion.Type,
                         PreReleaseType.Beta)
        self.assertEqual(version.SdkVersion.PreReleaseVersion.Revision, 1)
        self.assertEqual(version.SdkVersion.PreReleaseVersion.BuildMetadata,
                         None)
        self.assertEqual(version.SdkVersion, SdkVersion(7, 0, 100, 0, PrereleaseVersion(PreReleaseType.Beta, 1, None)))
        self.assertEqual(version.SdkOnlyDebVersion(), "7.0.100~beta1~bootstrap+amd64-0ubuntu1")
        self.assertEqual(version.SdkOnlyDebVersion(buildSuffix="+build1"), "7.0.100~beta1+build1~bootstrap+amd64-0ubuntu1")

        self.assertEqual(version.RuntimeVersion.Major, 7)
        self.assertEqual(version.RuntimeVersion.Minor, 0)
        self.assertEqual(version.RuntimeVersion.Patch, 0)
        self.assertEqual(version.RuntimeVersion.PreReleaseVersion.Type,
                         PreReleaseType.Beta)
        self.assertEqual(version.RuntimeVersion.PreReleaseVersion.Revision, 1)
        self.assertEqual(version
                         .RuntimeVersion.PreReleaseVersion.BuildMetadata, None)
        self.assertEqual(version.RuntimeVersion, RuntimeVersion(7, 0, 0, PrereleaseVersion(PreReleaseType.Beta, 1, None)))
        self.assertEqual(version.RuntimeOnlyDebVersion(), "7.0.0~beta1~bootstrap+amd64-0ubuntu1")
        self.assertEqual(version.RuntimeOnlyDebVersion(buildSuffix="+build1"), "7.0.0~beta1+build1~bootstrap+amd64-0ubuntu1")

        self.assertEqual(version.DebRevision.DebianRevision, "0")
        self.assertEqual(version.DebRevision.UbuntuRevision, "1")
        self.assertEqual(version.BootstrapArchitecture, "amd64")
        self.assertEqual(version.OverwrittenVersion, "8.0.100-8.0.0~rc1")


if __name__ == '__main__':
    unittest.main()
