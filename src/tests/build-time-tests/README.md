# Build time tests

A minimal smoke test suite for source-build .NET on Ubuntu designed to run
after build-time.

This test-suite requires access to build artifacts generated after a
successfull build.

## Rationale

Introduced as part of the Ubuntu main inclusion (see also: MIR process) to
increase quaality assurance.

## Usage

```
tests.py [-h] [-v] [--clean-sdk | --no-clean-sdk]
         [--clean-packages | --no-clean-packages]
         [--clean-home | --no-clean-home]
         [--clean-test-project | --no-clean-test-project]
         [--clean-all] [--force-clean | --no-force-clean]
         [--purge-after | --no-purge-after]
         [--test-directory PATH] [--source-package-root PATH]
```

Run with `--help` for more information:

```bash
python3 debian/tests/build-time-tests/tests.py --help
```

## Examples


Run the tests using the current working directory:
```bash
python3 debian/tests/build-time-tests/tests.py \
    --verbose --purge-after
```
- `--verbose` will print additional debug information to STDOUT
- `--purge-after` delete the test data after a successful run

This kind of command is useful during feature development of the build time
test: 
```bash
python3 debian/tests/build-time-tests/tests.py \
    --verbose \
    --test-directory 'test-dir' \
    --clean-all --no-clean-sdk --no-clean-packages 
```
- `--verbose` will print additional debug information to STDOUT
- `--test-directory 'test-dir'` will set the test directory to a fixed path
  between test-runs (Note: the directory will be created if it does not exists)
- `--clean-all` will delete all previous test data before running tests
- `--no-clean-sdk` will reuse the extracted sdk artifact of a previous test
  run
- `--no-clean-packages` will reuse the extracted nuget package artifacts of
  a previous test run

NOTE: The order of `--clean-*` flags is important. The flags
`--no-clean-sdk` and `--no-clean-packages` after `--clean-all` have higher
priority. You can specify as many flags as you want. Only the last
respective flag will take effect.

## Author

Dominik Viererbe \<dominik.viererbe@canonical.com\>
