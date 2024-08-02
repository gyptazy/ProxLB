#!/bin/bash
sudo apt-get install rpm cmake git make python3-yaml

git clone https://github.com/gyptazy/changelog-fragments-creator.git
./changelog-fragments-creator/changelog-creator -f ../.changelogs/ -o ../CHANGELOG.md
mkdir packages
mkdir build
cd build
cmake ..
cpack -G DEB .
cpack -G RPM .
cp *.deb ../packages
cp *.rpm ../packages
cd ..
rm -rf build
echo "Packages created. Packages can be found in directory: packages"
