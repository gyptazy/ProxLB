#!/usr/bin/env bash
VERSION="1.1.9.1"

# ProxLB
sed -i "s/^__version__ = .*/__version__ = \"$VERSION\"/" "proxlb/utils/version.py"
sed -i "s/version=\"[0-9]*\.[0-9]*\.[0-9]*\"/version=\"$VERSION\"/" setup.py

# Helm Chart
sed -i "s/^version: .*/version: \"$VERSION\"/" helm/proxlb/Chart.yaml
sed -i "s/^appVersion: .*/appVersion: \"v$VERSION\"/" helm/proxlb/Chart.yaml
sed -i "s/^tag: .*/tag: \"v$VERSION\"/" helm/proxlb/values.yaml

echo "OK: Versions have been sucessfully set to $VERSION"
