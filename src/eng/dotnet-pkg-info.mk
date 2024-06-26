# This Makefile fragment defines the following package information variables:
#
#  DOTNET_MAJOR: Major .NET version number from the latest changelog entry.
#  DOTNET_MINOR: Minor .NET version number from the latest changelog entry.
#  DOTNET_RUNTIME_ID: .NET runtime identifier of the current host.
#  DOTNET_ARCH: .NET architecture identifier of the current host.
#  DOTNET_GIT_REPO: URI of the repository where the origiinal source is from.
#  DOTNET_GIT_COMMIT: Commit hash of the original source in the repository.
#  DOTNET_DEB_VERSION_SDK_ONLY: The version for binary deb packages that only contain SDK components in compliance with FO127.
#  DOTNET_DEB_VERSION_RUNTIME_ONLY: The version for binary deb packages that only contain Runtime components in compliance with FO127.
#  DOTNET_CONTAINS_BOOTSTRAPPING_SDK: A boolean (true/false) that indicates if the source packages contains an embedded SDK for initial bootstrapping.
#  DOTNET_60_OR_GREATER: A boolean (true/false) that indicates if the source version is equal or greater than 6.0
#  DOTNET_70_OR_GREATER: A boolean (true/false) that indicates if the source version is equal or greater than 7.0
#  DOTNET_80_OR_GREATER: A boolean (true/false) that indicates if the source version is equal or greater than 8.0

export DOTNET_MAJOR = $(shell $(CURDIR)/debian/eng/dotnet-version.py --major)
export DOTNET_MINOR = $(shell $(CURDIR)/debian/eng/dotnet-version.py --minor)

ifeq ($(DOTNET_MAJOR),6)
    DOTNET_60_OR_GREATER = true
    DOTNET_70_OR_GREATER = true
    DOTNET_80_OR_GREATER = true
else ifeq ($(DOTNET_MAJOR),7)
    DOTNET_60_OR_GREATER = false
    DOTNET_70_OR_GREATER = true
    DOTNET_80_OR_GREATER = true
else ifeq ($(DOTNET_MAJOR),8)
    DOTNET_60_OR_GREATER = false
    DOTNET_70_OR_GREATER = false
    DOTNET_80_OR_GREATER = true
else
    $(error ".NET version $(DOTNET_MAJOR).$(DOTNET_MINOR) not handled")
endif

ifeq ($(DEB_HOST_ARCH), amd64)
    export DOTNET_ARCH = x64
else ifeq ($(DEB_HOST_ARCH), i386)
    export DOTNET_ARCH = x86
else ifeq ($(DEB_HOST_ARCH), arm64)
    export DOTNET_ARCH = arm64
else ifeq ($(DEB_HOST_ARCH), armhf)
    export DOTNET_ARCH = arm
else ifeq ($(DEB_HOST_ARCH), s390x)
    export DOTNET_ARCH = s390x
else ifeq ($(DEB_HOST_ARCH), ppc64el)
    export DOTNET_ARCH = ppc64le
else ifeq ($(DEB_HOST_ARCH), powerpc)
    export DOTNET_ARCH = ppc
else ifeq ($(DEB_HOST_ARCH), riscv64)
    export DOTNET_ARCH = riscv64
else
	$(error "architecture '$(DEB_HOST_ARCH)' not handled")
endif

export DOTNET_RUNTIME_ID = $(shell . /etc/os-release; echo "$${ID}.$${VERSION_ID}-$(DOTNET_ARCH)")

ifeq ($(DOTNET_80_OR_GREATER), true)
    DOTNET_DEB_VERSION_SDK_ONLY = $(shell $(CURDIR)/debian/eng/dotnet-version.py --sdk-only-deb-version)
    DOTNET_DEB_VERSION_RUNTIME_ONLY = $(shell $(CURDIR)/debian/eng/dotnet-version.py --runtime-only-deb-version)
    
    ifeq ($(wildcard $(CURDIR)/release.info),)
        $(error "No release.info file in the source tarball found")
    endif

    DOTNET_GIT_REPO = $(shell grep --only-matching --perl-regexp '(?<=^RM_GIT_REPO=).+$$' $(CURDIR)/release.info)
    DOTNET_GIT_COMMIT = $(shell grep --only-matching --perl-regexp '(?<=^RM_GIT_COMMIT=).+$$' $(CURDIR)/release.info)

	ifeq ($(DOTNET_GIT_REPO),)
		$(error ".NET git source repository is NOT specified in release.info file.")
    else ifeq ($(DOTNET_GIT_COMMIT),)
        $(error ".NET git commit hash is NOT specified in release.info file.")
	endif
endif

ifneq ($(wildcard $(CURDIR)/.dotnet),)
    DOTNET_CONTAINS_BOOTSTRAPPING_SDK = true
else
    DOTNET_CONTAINS_BOOTSTRAPPING_SDK = false
endif
