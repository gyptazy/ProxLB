#!/bin/bash
mkdir packages
mkdir build
cd build
cmake ..
cpack -G DEB .
cp *.deb ../packages
cd ..
rm -rf build
echo "Packages created. Packages can be found in directory: packages"
