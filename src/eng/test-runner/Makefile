CONFIGURATION:=Release
ARCH:=$(subst aarch64,arm64,$(subst x86_64,x64,$(shell uname -m)))
RUNTIME:=linux-$(ARCH)
FRAMEWORK:=net6.0

# Building Turkey with a source-built .NET SDK may fail if that SDK references a version for TargetFramework
# that is not yet released. Setting TargetBundledFramework to 'true' enables building with such SDKs by using
# the bundled framework instead.
ifeq ("${TargetBundledFramework}", "true")
	ifndef BundledNETCoreAppTargetFrameworkVersion
		$(error "BundledNETCoreAppTargetFrameworkVersion is not set")
	endif
	
	FRAMEWORK:="net${BundledNETCoreAppTargetFrameworkVersion}"
endif

all: publish

f:
	@echo "$(FRAMEWORK)"

check:
	dotnet test -f $(FRAMEWORK) -c Release --verbosity detailed Turkey.Tests

run-samples:
	rm -rf ~/.nuget.orig && mv ~/.nuget ~/.nuget.orig && mkdir -p ~/.nuget
	cd Samples && test -f ../turkey/Turkey.dll && (dotnet ../turkey/Turkey.dll || true)
	rm -rf ~/.nuget && mv ~/.nuget.orig ~/.nuget

GIT_COMMIT_ID:
	git rev-parse --short HEAD > GIT_COMMIT_ID

GIT_TAG_VERSION:
	git describe --abbrev=0 | sed -e 's/^v//' > GIT_TAG_VERSION

publish: GIT_COMMIT_ID GIT_TAG_VERSION
	cat GIT_COMMIT_ID
	cat GIT_TAG_VERSION
	(cd Turkey; \
	 dotnet publish \
	 -f $(FRAMEWORK) \
	 -c $(CONFIGURATION) \
	 -p:VersionPrefix=$$(cat ../GIT_TAG_VERSION) \
	 -p:VersionSuffix=$$(cat ../GIT_COMMIT_ID) \
	 -o $$(readlink -f $$(pwd)/../turkey))
	tar czf turkey.tar.gz turkey/

clean:
	rm -f GIT_COMMIT_ID GIT_TAG_VERSION
	rm -rf Turkey/bin Turkey/obj
	rm -rf Turkey.Tests/bin Turkey.Tests/obj
	rm -rf bin
	rm -rf turkey turkey.tar.gz
	find -iname '*.log' -delete

fix-line-endings:
	find -iname '*.cs' -exec dos2unix {} \;
	find -iname '*.csproj' -exec dos2unix {} \;
	find -iname 'nuget.config' -exec dos2unix {} \;

list-todos:
	grep -r -E 'TODO|FIXME' *
