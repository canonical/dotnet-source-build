#! /usr/bin/env bash
# Deletes uscan download and fails deliberately.
#
# See the section "Package Design Considerations" > "`debian/watch` file"
# in the README.source file for more context.

while [ "$#" -gt "0" ]; do
    case "$1" in
        --upstream-version)
            if [ "$#" -lt "2" ]; then
                echo "Error: parameter --upstream-version is specified, but no value was provided"
                exit 1
            fi

            version="$2"
            shift 2

            # clean uscan download:
            find .. -name "dotnet*${version}*.tar.*" -delete
            ;;
        *)
            echo "Error: unexpected argument '$1'"
            exit 1
            ;;
    esac
done

exit 1
