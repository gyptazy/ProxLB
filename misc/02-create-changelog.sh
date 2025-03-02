#!/usr/bin/env bash
git clone https://github.com/gyptazy/changelog-fragments-creator.git
./changelog-fragments-creator/changelog-creator -f .changelogs/ -o CHANGELOG.md
echo "Created changelog file"