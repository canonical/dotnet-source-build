#!/usr/bin/env bash

# This script is expects to be called by uscan(1). There are some
# safeguards this script will check for, but please only invoke 
# this script manually if you know what you are doing.

# What does this script do?
# 1. extract orig tarball
# 2. parse sdk version number
# 3. rename extracted source tree to "8.0.XXX-8.0.X" pattern
# 4. repack source tree
# 5. delete temprary uscan(1) files
# 6. copy debian folder to new source tree
# 7. create changelog entry

old_source_tree="$PWD"
log_file="$(realpath "../$(basename "$PWD").watch-script.log")"
default_changelog_entry_msg="New upstream release."

function log()
{
    # The logs are writen to a log file, because uscan
    # swallows the output if the exit code is not 0.
    echo "$0 $1: $2" | tee --append "$log_file"
}

function log_error()
{
    log "error" "$1"
}

function log_warn()
{
    log "warning" "$1"
}

function log_info()
{
    log "info" "$1"
}

function log_debug()
{
    log "debug" "$1"
}

log_debug "started on $(date)"

if [ "$#" != "2" ]; then
    log_debug "parameters: $*"
    log_error "expected 2 parameters; got $#"
    exit 1
elif [ "$1" != "--upstream-version" ]; then
    log_debug "parameters: $*"
    log_error "expected --upstream-version as first parameter; got $1"
    exit 1
else
    version="$2"
    log_debug "version=$version"
fi

# just check if we are at the root of a source tree
if [ ! -d "./debian" ]; then
    log_error "could not find a debian folder; expected to be inside a debian source tree"
    exit 1 
elif [ ! -s "./debian/changelog" ]; then
    log_error "could not find a debian/changelog file; expected to be inside a debian source tree"
    exit 1
elif [ ! -s "./debian/copyright" ]; then
    log_error "could not find a debian/copyright file; expected to be inside a debian source tree"
    exit 1
fi

cd ..

orig_tarball="dotnet8_$version.orig.tar.xz"
log_debug "orig_tarball=$orig_tarball"
if [ ! -s "$orig_tarball" ]; then
    log_error "could not find orig tarball that should have been created by uscan(1)"
    exit 1
fi

log_info "extracting orig tarball"
if ! tar --extract --xz --file "$orig_tarball" ; then
    log_error "failed to extract orig tarball ../$orig_tarball"
    exit 1
fi

# parses the SDK version
source_tree="dotnet8-$version"
if [ ! -d "$source_tree" ]; then
    log_error "extracted source tree ../$source_tree could not be found"
    exit 1
elif ! sdk_version="$(grep --only-matching \
    --perl-regexp '(?<=<OutputPackageVersion>)8\.0\.1\d\d(\.\d+)*(?=.*<\/OutputPackageVersion>)' \
    "$source_tree/prereqs/git-info/sdk.props")"
then
    log_error "failed to parse sdk metadata from extracted orig tarball"
    log_info "deleting extracted source tree"
    rm -rf "$source_tree" || log_warn "failed to delete extracted source tree"
    exit 1
elif [ -z "$sdk_version" ]; then
    log_error "sdk_version is empty; must have been a parsing error; maybe the format of prereqs/git-info/sdk.props has changed"
    log_info "deleting extracted source tree"
    rm -rf "$source_tree" || log_warn "failed to delete extracted source tree"
    exit 1
else
    log_debug "sdk_version=$sdk_version"
fi

# rename the source tree from a "8.0.X" pattern to a "8.0.XXX-8.0.X" pattern
new_source_tree="${source_tree/$version/$sdk_version-$version}"
if mv "$source_tree" "$new_source_tree"; then
    echo "$0 info: renamed '../$source_tree' to '../$new_source_tree'"
    source_tree="$new_source_tree"
    version="${source_tree/dotnet8-/}"
else
    log_debug "failed to rename '../$source_tree' to '../$new_source_tree'"
    log_info "deleting extracted source tree"
    rm -rf "$source_tree" || log_warn "failed to delete extracted source tree"
    exit 1
fi

# repack source tree, because top-level dir in the orig tarball has also the "8.0.X" pattern
log_info "repack source tree"
if ! tar --create --use-compress-program 'xz --threads 0' --file "dotnet8_$version.orig.tar.xz" "$new_source_tree"; then
    log_debug "failed to repack orig tarball"
    log_info "deleting extracted source tree"
    rm -rf "$source_tree" || log_warn "failed to delete extracted source tree"
    exit 1
fi

log_info "cleaning up uscan(1) temporary artifacts"
rm -rf "dotnet8-temporary.*.git" || log_warn "failed to delete temporary bare git repository"
rm -f "$orig_tarball" ||  log_warn "failed to delete temporary orig tarball $orig_tarball"
rm -f "dotnet8-${version/8\.0\.1[0-9][0-9]-/}.tar.xz" || log_warn "failed to delete temporary tarball"

log_info "copy debian folder"
if ! cp -r "$old_source_tree/debian" "$source_tree/"; then
    log_warn "failed to copy the debian folder to the new source tree"
    exit 1
fi

if ! cd "$source_tree"; then
    log_warn "failed to change working directory to new source tree"
    exit 1
fi 

log_info "new source tree at $PWD"

log_info "create changelog entry"
debchange --newversion "$version-0ubuntu1" "$default_changelog_entry_msg" \
 || log_warn "failed to create changelog entry"
