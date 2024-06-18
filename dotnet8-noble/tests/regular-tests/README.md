### These tests are written for the .NET test runner.

Please see the repository for more details: https://github.com/canonical/dotnet-test-runner

### Quick clone

If you forked it, replace `canonical` with your username.

```
$ git clone https://github.com/canonical/dotnet-test-runner && cd dotnet-test-runner && git clone https://github.com/canonical/dotnet-regular-tests
```

### Dependencies

#### apk

```
babeltrace bash bash-completion binutils coreutils file findutils g++ jq libstdc++-dev lldb lttng-ust lttng-tools npm postgresql psqlodbc sed strace unixodbc zlib-dev
```

#### apt

```
babeltrace bash bash-completion build-essential coreutils file findutils jq lldb sed strace npm postgresql unixodbc zlib1g-dev
```

#### dnf

````
babeltrace bash-completion bc findutils gcc-c++ jq libstdc++-devel lttng-ust lttng-tools npm postgresql-odbc postgresql-server strace unixODBC /usr/bin/file /usr/bin/free /usr/bin/lldb /usr/bin/readelf /usr/bin/su which zlib-devel
````
