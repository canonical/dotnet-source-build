# .NET SRU Test Plan

This guide is a series of manual steps that serve as a smoke test to be used with Ubuntu .NET SRUs. The goal is to verify whether a .NET installation is working correctly.

## 1. Install dotnet

```
$ sudo apt install dotnet8
```

Replace `dotnet8` if you're testing a different .NET version, e.g. `dotnet6`, `dotnet7`, and so on.

# 2. Check installation

```
$ dpkg -l | grep 'dotnet\|aspnet\|netstandard'
```
Expected output:
```
ii  aspnetcore-runtime-8.0                        8.0.7-0ubuntu1~24.04.1                          amd64        ASP.NET Core runtime
ii  aspnetcore-targeting-pack-8.0                 8.0.7-0ubuntu1~24.04.1                          amd64        Internal - targeting pack for Microsoft.AspNetCore.App 8.0
ii  dotnet-apphost-pack-8.0                       8.0.7-0ubuntu1~24.04.1                          amd64        Internal - targeting pack for Microsoft.NETCore.App 8.0
ii  dotnet-host-8.0                               8.0.7-0ubuntu1~24.04.1                          amd64        .NET host command line
ii  dotnet-hostfxr-8.0                            8.0.7-0ubuntu1~24.04.1                          amd64        .NET host resolver
ii  dotnet-runtime-8.0                            8.0.7-0ubuntu1~24.04.1                          amd64        .NET runtime
ii  dotnet-sdk-8.0                                8.0.107-0ubuntu1~24.04.1                        amd64        .NET 8.0 Software Development Kit
ii  dotnet-targeting-pack-8.0                     8.0.7-0ubuntu1~24.04.1                          amd64        Internal - targeting pack for Microsoft.NETCore.App 8.0
ii  dotnet-templates-8.0                          8.0.107-0ubuntu1~24.04.1                        amd64        .NET 8.0 templates
ii  dotnet8                                       8.0.107-8.0.7-0ubuntu1~24.04.1                  amd64        .NET CLI tools and runtime
ii  netstandard-targeting-pack-2.1-8.0            8.0.107-0ubuntu1~24.04.1                        amd64        Internal - targeting pack for NETStandard.Library 2.1
```


# 2. Basic check commands:

On this section, we're testing the installation of the .NET Runtime and SDK on the machine. Version numbers will vary depending on what version you are currently testing, so don't take the expected outputs verbatim.

It is important, though, that the commands execute successufully, i.e. exit code 0.

## 2.1. `dotnet —info`

```
$ dotnet —info
```
Expected output:
```
.NET SDK:
 Version:           8.0.107
 Commit:            1bdaef7265
 Workload version:  8.0.100-manifests.43c23f91

Runtime Environment:
 OS Name:     ubuntu
 OS Version:  24.10
 OS Platform: Linux
 RID:         ubuntu.24.10-x64
 Base Path:   /usr/lib/dotnet/sdk/8.0.107/

.NET workloads installed:
 Workload version: 8.0.100-manifests.43c23f91
There are no installed workloads to display.

Host:
  Version:      8.0.7
  Architecture: x64
  Commit:       2aade6beb0

.NET SDKs installed:
  8.0.107 [/usr/lib/dotnet/sdk]

.NET runtimes installed:
  Microsoft.AspNetCore.App 8.0.7 [/usr/lib/dotnet/shared/Microsoft.AspNetCore.App]
  Microsoft.NETCore.App 8.0.7 [/usr/lib/dotnet/shared/Microsoft.NETCore.App]

Other architectures found:
  None

Environment variables:
  Not set

global.json file:
  Not found

Learn more:
  https://aka.ms/dotnet/info

Download .NET:
  https://aka.ms/dotnet/download
```

## 2.2. `dotnet --version`

```
$ dotnet --version
```
Expected output:
```
8.0.107
```

## 2.3. `dotnet sdk check`

```
$ dotnet sdk check
```
Expected output:
```
.NET SDKs:
Version      Status     
------------------------
8.0.107      Up to date.

Try out the newest .NET SDK features with .NET 9.0.100-preview.6.24328.19.

.NET Runtimes:
Name                          Version      Status     
------------------------------------------------------
Microsoft.AspNetCore.App      8.0.7        Up to date.
Microsoft.NETCore.App         8.0.7        Up to date.


The latest versions of .NET can be installed from https://aka.ms/dotnet-core-download. For more information about .NET lifecycles, see https://aka.ms/dotnet-core-support.
```

# 3. Checking console, solution and project commands

## 3.1. Creating console project: `dotnet new console`

```
$ dotnet new console --name Testing
```
Expected output:
```
The template "Console App" was created successfully.

Processing post-creation actions...
Restoring /home/ubuntu/Testing/Testing.csproj:
  Determining projects to restore...
  Restored /home/ubuntu/Testing/Testing.csproj (in 732 ms).
Restore succeeded.
```
Now, go into the `Testing/` directory for subsequent commands:
```
$ cd Testing/
```

## 3.2. Creating solution: `dotnet new sln`

```
$ dotnet new sln
```
Expected output:
```
The template "Solution File" was created successfully.
```

## 3.3. Adding project to the solution: `dotnet sln <sln_file> add <csproj_file>`

```
$ dotnet sln Testing.sln add Testing.csproj
```
Expected output:
```
Project `Testing.csproj` added to the solution.
```

## 3.4. Building solution: `dotnet build <sln_file>`

```
$ dotnet build Testing.sln
```
Expected output:
```
MSBuild version 17.8.5+b5265ef37 for .NET
  Determining projects to restore...
  All projects are up-to-date for restore.
  Testing -> /home/ubuntu/Testing/bin/Debug/net8.0/Testing.dll

Build succeeded.
    0 Warning(s)
    0 Error(s)

Time Elapsed 00:00:01.87
```

## 3.5. Running solution: `dotnet run`

```
$ dotnet run
```
```
Hello, World!
```

## 3.6. Project that uses a NuGet package: `dotnet add <csproj_file> package <nuget_package>`

Change your `Program.cs` to the following:

```C#
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Google.Apis;

namespace TestProject
{
    class Program
    {
        static void Main(string[] args)
        {
            Stack<int> myStack = new Stack<int>();
            var th = new Thread(()=>WaitAndPrint(myStack));
            th.Start();
            Console.WriteLine("Me first!");
            myStack.Push(1);
            Console.WriteLine("Finished tasks: {0}", myStack.Count);
            Thread.Sleep(1000);
            Console.WriteLine("Finished tasks: {0}", myStack.Count);
        }

        private static void WaitAndPrint(Stack<int> myStack)
        {
            Thread.Sleep(1000);
            Console.WriteLine("Me second!");
            myStack.Push(2);
        }
    }
}
```
Then, run:
```
$ dotnet add Testing.csproj package Google.Apis
```
Expected output:
```
  Determining projects to restore...
  Writing /tmp/tmpQpOYF8.tmp
info : X.509 certificate chain validation will use the fallback certificate bundle at '/usr/lib/dotnet/sdk/8.0.107/trustedroots/codesignctl.pem'.
info : X.509 certificate chain validation will use the fallback certificate bundle at '/usr/lib/dotnet/sdk/8.0.107/trustedroots/timestampctl.pem'.
info : Adding PackageReference for package 'Google.Apis' into project 'Testing.csproj'.
info :   GET https://api.nuget.org/v3/registration5-gz-semver2/google.apis/index.json
info :   OK https://api.nuget.org/v3/registration5-gz-semver2/google.apis/index.json 1270ms
info : Restoring packages for /home/ubuntu/Testing/Testing.csproj...
info :   GET https://api.nuget.org/v3-flatcontainer/google.apis/index.json
info :   OK https://api.nuget.org/v3-flatcontainer/google.apis/index.json 919ms
info :   GET https://api.nuget.org/v3-flatcontainer/google.apis/1.68.0/google.apis.1.68.0.nupkg
info :   OK https://api.nuget.org/v3-flatcontainer/google.apis/1.68.0/google.apis.1.68.0.nupkg 62ms
info :   GET https://api.nuget.org/v3-flatcontainer/google.apis.core/index.json
info :   OK https://api.nuget.org/v3-flatcontainer/google.apis.core/index.json 771ms
info :   GET https://api.nuget.org/v3-flatcontainer/google.apis.core/1.68.0/google.apis.core.1.68.0.nupkg
info :   OK https://api.nuget.org/v3-flatcontainer/google.apis.core/1.68.0/google.apis.core.1.68.0.nupkg 68ms
info :   GET https://api.nuget.org/v3-flatcontainer/newtonsoft.json/index.json
info :   OK https://api.nuget.org/v3-flatcontainer/newtonsoft.json/index.json 206ms
info :   GET https://api.nuget.org/v3-flatcontainer/newtonsoft.json/13.0.3/newtonsoft.json.13.0.3.nupkg
info :   OK https://api.nuget.org/v3-flatcontainer/newtonsoft.json/13.0.3/newtonsoft.json.13.0.3.nupkg 76ms
info : Installed Newtonsoft.Json 13.0.3 from https://api.nuget.org/v3/index.json with content hash HrC5BXdl00IP9zeV+0Z848QWPAoCr9P3bDEZguI+gkLcBKAOxix/tLEAAHC+UvDNPv4a2d18lOReHMOagPa+zQ==.
info : Installed Google.Apis 1.68.0 from https://api.nuget.org/v3/index.json with content hash s2MymhdpH+ybZNBeZ2J5uFgFHApBp+QXf9FjZSdM1lk/vx5VqIknJwnaWiuAzXxPrLEkesX0Q+UsiWn39yZ9zw==.
info : Installed Google.Apis.Core 1.68.0 from https://api.nuget.org/v3/index.json with content hash pAqwa6pfu53UXCR2b7A/PAPXeuVg6L1OFw38WckN27NU2+mf+KTjoEg2YGv/f0UyKxzz7DxF1urOTKg/6dTP9g==.
info :   CACHE https://api.nuget.org/v3/vulnerabilities/index.json
info :   CACHE https://api.nuget.org/v3-vulnerabilities/2024.07.24.05.36.37/vulnerability.base.json
info :   CACHE https://api.nuget.org/v3-vulnerabilities/2024.07.24.05.36.37/2024.07.26.11.36.43/vulnerability.update.json
info : Package 'Google.Apis' is compatible with all the specified frameworks in project 'Testing.csproj'.
info : PackageReference for package 'Google.Apis' version '1.68.0' added to file '/home/ubuntu/Testing/Testing.csproj'.
info : Writing assets file to disk. Path: /home/ubuntu/Testing/obj/project.assets.json
log  : Restored /home/ubuntu/Testing/Testing.csproj (in 3.05 sec).
```

## 3.7. Running project

```
$ dotnet run
```
Expected output:
```
Me first!
Finished tasks: 1
Me second!
Finished tasks: 2
```

## 3.8. Removing NuGet package

```
$ dotnet remove Testing.csproj package Google.Apis
```
Expected output:
```
info : Removing PackageReference for package 'Google.Apis' from project 'Testing.csproj'.
```
With a missing NuGet package, running the project should now fail:
```
$ dotnet run
```
Expected output:
```
/home/ubuntu/Testing/Program.cs(6,7): error CS0246: The type or namespace name 'Google' could not be found (are you missing a using directive or an assembly reference?) [/home/ubuntu/Testing/Testing.csproj]

The build failed. Fix the build errors and run again.
```
