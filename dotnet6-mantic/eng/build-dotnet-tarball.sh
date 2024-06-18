#!/usr/bin/env bash

trap on_exit TERM
trap on_exit EXIT

set -euo pipefail
IFS=$'\n\t'

SECURITY_PARTNERS_REPOSITORY='git@ssh.dev.azure.com:v3/dotnet-security-partners/dotnet/dotnet'
MS_TARBALL_SHA512_HASH='d16f6b6713a79aaeabaf1043c4d649de8f6e07d9f575fedcbbaee993a32259046641a4c5680885a3a3a686df04429c51e934ee1a476ad2e75ed7ea94cc9a63b8'

INITIAL_DIRECTORY=$PWD

REPACK=false
CLONE_REPOSITORY=false
BOOTSTRAP=false
CLEANUP_SOURCE_TREE=true
REPOSITORY="$SECURITY_PARTNERS_REPOSITORY"

function print_usage
{
    bold_style='\033[1m'
    underline_style='\033[4m'
    reset_style='\033[0m'

    echo    ""
    echo -e "${bold_style}Usage:${reset_style} $0 [--repository ${underline_style}repository${reset_style}] --upstream-version ${underline_style}version${reset_style} [--bootstrap] [--no-clean]"
    echo    ""
    echo    "Creates the orig tarball for the dotnet7 package from a branch version at a git repository."
    echo    ""
    echo    "Parameter:"
    echo -e "  --upstream-version ${underline_style}version${reset_style}"
    echo -e "        ${underline_style}version${reset_style} is used to determain the git tag that should be pulled from the ${underline_style}repository${reset_style}"
    echo -e "  --repository ${underline_style}repository${reset_style}"
    echo    "        Address to the git repository that will be cloned. (Default: ${SECURITY_PARTNERS_REPOSITORY})"
    echo    "  --bootstrap"
    echo    "        incorporate Microsoft pre-builds into the resulting orig tarball to prepare for initial bootstraping"
    echo    "  --no-clean"
    echo -e "        does not delete the cloned ${underline_style}repository${reset_style} when the script exists"
    echo    ""
    echo    "Example:"
    echo    "  $0 --upstream-version 7.0.109"
    echo    ""
    echo -e "${bold_style}Usage:${reset_style} $0 --repack ${underline_style}tarball-url${reset_style} [--bootstrap] [--no-clean]"
    echo    ""
    echo    "Repack a source archive tarball for dotnet7."
    echo    ""
    echo    "Parameter:"
    echo -e "  --repack ${underline_style}tarball-url${reset_style}"
    echo    "        https URL from where Microsofts tarball can be downloaded"
    echo    "  --bootstrap"
    echo    "        incorporate Microsoft pre-builds into the resulting orig tarball to prepare for initial bootstraping"
    echo    "  --no-clean"
    echo    "        does not delete the unpacked tarball when the script exists"
    echo    ""
    echo    "Run $0 --help to show this usage information."
}

function on_exit
{
    if $CLEANUP_SOURCE_TREE && [ -n "$INITIAL_DIRECTORY" ] && [ -n "$SOURCE_TREE_DIRECTORY_NAME" ]; then
        rm -rf "${INITIAL_DIRECTORY:?}/${SOURCE_TREE_DIRECTORY_NAME:?}"
    fi
}

# parse parameter:
while [ "$#" -gt "0" ]; do
    case $1 in
        --help)
            print_usage
            exit 0
            ;;
        --upstream-version)
            if [ "$#" -lt "2" ]; then
                echo "Error: parameter --upstream-version is specified, but no value was provided"
                print_usage
                exit 1
            fi

            if $REPACK; then
                echo "Error: conflicting parameters; --upstream-version and --repack is specified"
                print_usage
                exit 1
            fi

            CLONE_REPOSITORY=true
            UPSTREAM_VERSION=$2
            shift 2
            ;;
        --repository)
            if [ "$#" -lt "2" ]; then
                echo "Error: parameter --repository is specified, but no value was provided"
                print_usage
                exit 1
            fi

            if $REPACK; then
                echo "Error: conflicting parameters; --repository and --repack is specified"
                print_usage
                exit 1
            fi

            CLONE_REPOSITORY=true
            REPOSITORY=$2
            shift 2
            ;;
        --repack)
            if [ "$#" -lt "2" ]; then
                echo "Error: parameter --repack is specified, but no value was provided"
                print_usage
                exit 1
            fi

            if $CLONE_REPOSITORY; then
                echo "Error: conflicting parameters; --repack and either --upstream-version or --repository is specified"
                print_usage
                exit 1
            fi

            REPACK=true
            MS_TARBALL_URL=$2
            MS_TARBALL_FILENAME=$(echo "${MS_TARBALL_URL}" | sed -r 's|.*/([^/]+tar.gz)\?.*|\1|')
            UPSTREAM_VERSION=$(echo "${MS_TARBALL_FILENAME}" | sed -r 's|.*-(.*).tar.gz|\1|')
            shift 2
            ;;
        --bootstrap)
            BOOTSTRAP=true;

            case "$(uname --hardware-platform)" in
                x86_64)
                    DPKG_ARCHITECTURE="amd64";
                    ;;
                aarch64)
                    DPKG_ARCHITECTURE="arm64";
                    ;;
                *)
                    echo "Error: Unknown/Unsupported architecture '$(uname --hardware-platform)'."
                    exit 1
                    ;;
            esac
            shift 1
            ;;
        --no-clean)
            CLEANUP_SOURCE_TREE=false
            shift 1
            ;;
        *)
            echo "Error: unexpected argument '$1'"
            print_usage
            exit 1
            ;;
    esac
done

if ! $CLONE_REPOSITORY && ! $REPACK; then
    echo "Error: neither --upstream-version nor --repack was specified"
    print_usage
    exit 1
fi

MAJOR_VERSION_NUMBER=${UPSTREAM_VERSION%%.*}
PKG_NAME="dotnet$MAJOR_VERSION_NUMBER"
SOURCE_TREE_DIRECTORY_NAME="$PKG_NAME-$UPSTREAM_VERSION"

if [ -d "$SOURCE_TREE_DIRECTORY_NAME" ]; then
    echo "Error an directory $SOURCE_TREE_DIRECTORY_NAME already exists; you may want to delete it"
fi

if $CLONE_REPOSITORY; then
    echo "Info: cloning repository..."
    if ! git clone --no-checkout "$REPOSITORY" "$SOURCE_TREE_DIRECTORY_NAME"; then
        echo "ERROR: failed to clone repository"
        exit 1
    fi

    pushd "$SOURCE_TREE_DIRECTORY_NAME"

    if [ "$(git tag | grep --count "$UPSTREAM_VERSION")" -ne "1" ]; then
        echo "ERROR: found none ore more than one tag that matches the upstream version"
        git tag | grep "$UPSTREAM_VERSION"
        exit 1
    fi

    echo "Info: checkout upstream version..."
    if ! git checkout "$(git tag | grep "$UPSTREAM_VERSION")"; then
        echo "ERROR: failed to checkout upstream version"
        git tag | grep "$UPSTREAM_VERSION"
        exit 1
    fi
elif $REPACK; then
    mkdir "$SOURCE_TREE_DIRECTORY_NAME"

    if [ -e "$MS_TARBALL_FILENAME" ]; then
        SHA512_FILEHASH=$(sha512sum "${MS_TARBALL_FILENAME}" | cut -d' ' -f1)

        if [ "$SHA512_FILEHASH" != "$MS_TARBALL_SHA512_HASH" ]; then
            echo "Error: file $MS_TARBALL_SHA512_HASH already exists, but does not match the expected hashsum; maybe the file is corrupted and you want to delete it"
            echo "  Expected SHA512-HASH: $MS_TARBALL_SHA512_HASH"
            echo "  Actual SHA512-HASH: $SHA512_FILEHASH"
            exit 1
        fi
    else
        echo "Info: downloading MS tarball..."
        wget --progress=bar "$MS_TARBALL_URL" -O "$MS_TARBALL_FILENAME"
        if [ "$?" -ne "0" ]; then
            echo "Error: wget failed"
            exit 1
        fi

        SHA512_FILEHASH=$(sha512sum "${MS_TARBALL_FILENAME}" | cut -d' ' -f1)

        if [ "$SHA512_FILEHASH" != "$MS_TARBALL_SHA512_HASH" ]; then
            echo "Error: downloaded file $MS_TARBALL_SHA512_HASH does not match the expected hashsum; have you updated the expected hash value?"
            echo "  Expected SHA512-HASH: $MS_TARBALL_SHA512_HASH"
            echo "  Actual SHA512-HASH: $SHA512_FILEHASH"
            exit 1
        fi
    fi

    echo "Info: unpacking MS tarball..."
    pushd "$SOURCE_TREE_DIRECTORY_NAME"
    tar xvzf "../$MS_TARBALL_FILENAME"
fi

if $BOOTSTRAP; then
    echo "Info: prepare bootstraping..."
    ORIG_TARBALL_FILENAME="${PKG_NAME}_$UPSTREAM_VERSION~bootstrap+$DPKG_ARCHITECTURE.orig.tar.xz"
    ./prep.sh --bootstrap
else
    ORIG_TARBALL_FILENAME="${PKG_NAME}_$UPSTREAM_VERSION.orig.tar.xz"
fi

if [ -e "../$ORIG_TARBALL_FILENAME" ]; then
    echo "Error: $ORIG_TARBALL_FILENAME already exists; maybe delete it?"
    exit 1
fi

echo "Info: removing unneeded/unwanted files..."
# Remove files with funny licenses, crypto implementations and other
# not-very-useful artifacts to reduce tarball size
# This list concords with the File-Excluded stanza in the copyright

# Binaries for gradle
rm -r src/aspnetcore/src/SignalR/clients/java/signalr/gradle*

# Unnecessary crypto implementation: IDEA
rm -r src/runtime/src/tests/JIT/Performance/CodeQuality/Bytemark/

# https://github.com/dotnet/aspnetcore/issues/34785
find src/aspnetcore/src -type d -name samples -print0 | xargs -0 rm -r

# https://github.com/NuGet/Home/issues/11094
rm -r src/nuget-client/test/EndToEnd

# Checked that are not needed in the build: this only removes under roslyn:
#src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/V?/*.dll
find src/roslyn/src/Compilers/Test/Resources -iname "*.dll" -exec rm -rf {} +

# https://github.com/microsoft/ApplicationInsights-dotnet/issues/2670
# we are applying a patch for this
#rm -r src/source-build-externals/src/application-insights/LOGGING/test/Shared/CustomTelemetryChannel.cs

# Don't remove vendorized libunwind because we need it for arm64 archs
#rm -r src/runtime/src/coreclr/pal/src/libunwind

#CPC-1578 prebuilts not used in build
rm src/roslyn/src/Compilers/Test/Resources/Core/DiagnosticTests/ErrTestMod01.netmodule
rm src/roslyn/src/Compilers/Test/Resources/Core/DiagnosticTests/ErrTestMod02.netmodule
rm src/roslyn/src/Compilers/Test/Resources/Core/ExpressionCompiler/LibraryA.winmd
rm src/roslyn/src/Compilers/Test/Resources/Core/ExpressionCompiler/LibraryB.winmd
rm src/roslyn/src/Compilers/Test/Resources/Core/ExpressionCompiler/Windows.Data.winmd
rm src/roslyn/src/Compilers/Test/Resources/Core/ExpressionCompiler/Windows.Storage.winmd
rm src/roslyn/src/Compilers/Test/Resources/Core/ExpressionCompiler/Windows.winmd
rm src/roslyn/src/Compilers/Test/Resources/Core/MetadataTests/Invalid/EmptyModuleTable.netmodule
rm src/roslyn/src/Compilers/Test/Resources/Core/MetadataTests/NetModule01/ModuleCS00.mod
rm src/roslyn/src/Compilers/Test/Resources/Core/MetadataTests/NetModule01/ModuleCS01.mod
rm src/roslyn/src/Compilers/Test/Resources/Core/MetadataTests/NetModule01/ModuleVB01.mod
rm src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/CustomModifiers/Modifiers.netmodule
rm src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/MultiModule/mod2.netmodule
rm src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/MultiModule/mod3.netmodule
rm src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/MultiTargeting/Source1Module.netmodule
rm src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/MultiTargeting/Source3Module.netmodule
rm src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/MultiTargeting/Source4Module.netmodule
rm src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/MultiTargeting/Source5Module.netmodule
rm src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/MultiTargeting/Source7Module.netmodule
rm src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/RetargetingCycle/V1/ClassB.netmodule
rm src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/TypeForwarders/Forwarded.netmodule
rm src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/V1/MTTestModule1.netmodule
rm src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/V1/MTTestModule2.netmodule
rm src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/V2/MTTestModule1.netmodule
rm src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/V2/MTTestModule3.netmodule
rm src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/V3/MTTestModule1.netmodule
rm src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/V3/MTTestModule4.netmodule
rm 'src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/With Spaces.netmodule'
rm src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/netModule/CrossRefModule1.netmodule
rm src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/netModule/CrossRefModule2.netmodule
rm src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/netModule/hash_module.netmodule
rm src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/netModule/netModule1.netmodule
rm src/roslyn/src/Compilers/Test/Resources/Core/SymbolsTests/netModule/netModule2.netmodule
rm src/roslyn/src/Compilers/Test/Resources/Core/WinRt/W1.winmd
rm src/roslyn/src/Compilers/Test/Resources/Core/WinRt/W2.winmd
rm src/roslyn/src/Compilers/Test/Resources/Core/WinRt/WB.winmd
rm src/roslyn/src/Compilers/Test/Resources/Core/WinRt/WB_Version1.winmd
rm src/roslyn/src/Compilers/Test/Resources/Core/WinRt/WImpl.winmd
rm src/roslyn/src/Compilers/Test/Resources/Core/WinRt/WinMDPrefixing.winmd
rm src/roslyn/src/Compilers/Test/Resources/Core/WinRt/Windows.Languages.WinRTTest.winmd
rm src/roslyn/src/Compilers/Test/Resources/Core/WinRt/Windows.winmd
rm src/roslyn/src/ExpressionEvaluator/Core/Source/ExpressionCompiler/Resources/WindowsProxy.winmd
rm src/runtime/src/libraries/System.Reflection.Metadata/tests/Resources/NetModule/ModuleCS00.mod
rm src/runtime/src/libraries/System.Reflection.Metadata/tests/Resources/NetModule/ModuleCS01.mod
rm src/runtime/src/libraries/System.Reflection.Metadata/tests/Resources/NetModule/ModuleVB01.mod
rm src/runtime/src/libraries/System.Reflection.Metadata/tests/Resources/WinRT/Lib.winmd
rm src/linker/external/cecil/Test/Resources/assemblies/ManagedWinmd.winmd
rm src/linker/external/cecil/Test/Resources/assemblies/NativeWinmd.winmd
rm src/linker/external/cecil/Test/Resources/assemblies/moda.netmodule
rm src/linker/external/cecil/Test/Resources/assemblies/modb.netmodule
rm src/linker/external/cecil/Test/Resources/assemblies/winrtcomp.winmd

popd

echo "Info: creating orig tarball..."
tar --use-compress-program 'xz --threads 0' --create --file "../${ORIG_TARBALL_FILENAME}" "${SOURCE_TREE_DIRECTORY_NAME}"

echo "Info: Done! orig tarball at ../${ORIG_TARBALL_FILENAME}"
exit 0
