# Patches

This directory contains patches that are applied to the cloned .NET VMR
(virtual monolithic repository) before the .NET SDK is cross-built by the
`bootstrap-sdk` job of the
[`build-orig-tarball.yaml`](../../.github/workflows/build-orig-tarball.yaml)
workflow.

## When are patches applied?

Patches are applied on the runner host, after the `Clone .NET VMR` step and
before the `Bootstrap .NET SDK` step of the `bootstrap-sdk` job. The patched
working tree is then bind-mounted into the build container, so no in-container
patching is performed.

Patches are applied with `git apply` in lexicographic (sorted) order against
the shallow clone of the .NET VMR located at `$GITHUB_WORKSPACE/dotnet-vmr`.

## Naming convention

Patch files must use the `.patch` file extension and be named so that their
sort order matches the order in which they should be applied. The recommended
convention is:

```
NNNN-short-description.patch
```

For example:

```
0001-fix-foo.patch
0002-fix-bar.patch
```

This guarantees a deterministic application order regardless of the filesystem
iteration order.

## Patch format

Patches must be unified diffs applicable with `git apply`. They can be
produced with either of:

```
git format-patch -1 <commit> -o eng/patches
git diff <ref> -- > eng/patches/<name>.patch
```

When produced with `git format-patch`, the commit message header is ignored
by `git apply` and only the diff content is used.

## Adding a patch

1. Drop the `.patch` file into this directory using the naming convention
   above.
2. No other changes are required: the workflow automatically picks up every
   `*.patch` file in this directory and applies it in sorted order.

## Notes

- If a patch fails to apply cleanly, the `bootstrap-sdk` job fails fast.
  Rebase or refresh the offending patch before re-running the workflow.
- This directory may contain other files (such as this `README.md`). Only
  files matching `*.patch` are considered by the workflow.
