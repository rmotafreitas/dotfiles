#!/bin/sh
# Install the packages listed in linux/packages/*.txt with apt. Prints the plan by default;
# --apply installs the missing ones (apt still asks for confirmation). Nothing is removed.
set -eu

if ! command -v apt-get >/dev/null 2>&1; then
    echo 'apt-based systems only (Debian, Ubuntu)' >&2
    exit 1
fi

apply=0
[ "${1:-}" != --apply ] || apply=1
lists="$(dirname "$0")/packages"

missing=
unavailable=
for pkg in $(sed 's/#.*//' "$lists/debian.txt" "$lists/third-party.txt"); do
    if [ "$(dpkg-query -W -f='${Status}' "$pkg" 2>/dev/null)" = 'install ok installed' ]; then
        continue
    fi
    candidate=$(apt-cache policy "$pkg" 2>/dev/null | awk '/Candidate:/ { print $2 }')
    if [ -n "$candidate" ] && [ "$candidate" != '(none)' ]; then
        missing="$missing $pkg"
    else
        unavailable="$unavailable $pkg"
    fi
done

if [ -n "$unavailable" ]; then
    echo "Not provided by any configured apt source (see $lists/third-party.txt):$unavailable"
fi
if [ -z "$missing" ]; then
    echo 'Every available listed package is installed.'
elif [ "$apply" = 1 ]; then
    # Word splitting of $missing is intended: one argument per package.
    sudo apt-get install $missing
else
    echo "Would install:$missing"
    echo 'Preview only. Add --apply to install.'
fi
