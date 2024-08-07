#!/bin/bash
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
