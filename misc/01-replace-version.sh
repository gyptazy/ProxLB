#!/usr/bin/env bash
VERSION="1.1.0"

sed -i "s/^__version__ = .*/__version__ = \"$VERSION\"/" "proxlb/utils/version.py"
sed -i "s/version=\"[0-9]*\.[0-9]*\.[0-9]*\"/version=\"$VERSION\"/" setup.py
echo "OK: Versions have been sucessfully set to $VERSION"
