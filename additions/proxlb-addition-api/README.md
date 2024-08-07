## Build packages
Building the packages requires cmake and deb.
For building packages, simly run the following commands:

```
mkdir build
cd build
cmake ..
cpack -G DEB .
```

When running on Debian/Ubuntu you can directly call `01_package.sh`
to create your own packages.
