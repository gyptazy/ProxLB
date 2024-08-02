cmake_minimum_required(VERSION 3.16)
project(proxmox-rebalancing-service VERSION 1.0.0)

install(FILES perl5/PVE/API2/Nodes.pm DESTINATION /usr/share/perl5/PVE/API2/)

# General
set(CPACK_PACKAGE_NAME "proxlb-additions")
set(CPACK_RESOURCE_FILE_LICENSE "${CMAKE_CURRENT_SOURCE_DIR}/../LICENSE")
set(CPACK_RESOURCE_FILE_README "${CMAKE_CURRENT_SOURCE_DIR}/../README.md")
set(CPACK_DEBIAN_PACKAGE_MAINTAINER "Florian Paul Azim <gyptazy> Hoberg <gyptazy@gyptazy.ch>")
set(CPACK_PACKAGE_CONTACT "Florian Paul Azim Hoberg <gyptazy@gyptazy.ch>")
set(CPACK_PACKAGE_VENDOR "gyptazy")

# RPM packaging
set(CPACK_PACKAGE_VERSION ${CMAKE_PROJECT_VERSION})
set(CPACK_GENERATOR "RPM")
set(CPACK_RPM_PACKAGE_ARCHITECTURE "amd64")
set(CPACK_RPM_PACKAGE_SUMMARY "ProxLB Additions - Additional optional patched libaries for ProxLB.")
set(CPACK_RPM_PACKAGE_DESCRIPTION "ProxLB Additions - Additional optional patched libaries for ProxLB.")
set(CPACK_RPM_CHANGELOG_FILE "${CMAKE_CURRENT_SOURCE_DIR}/changelog_redhat")
set(CPACK_PACKAGE_RELEASE 1)
set(CPACK_RPM_PACKAGE_LICENSE "GPL 3.0")
set(CPACK_RPM_PACKAGE_REQUIRES "python >= 3.2.0")

# DEB packaging
set(CPACK_DEBIAN_FILE_NAME DEB-DEFAULT)
set(CPACK_DEBIAN_PACKAGE_ARCHITECTURE "amd64")
set(CPACK_DEBIAN_PACKAGE_SUMMARY "ProxLB Additions - Additional optional patched libaries for ProxLB.")
set(CPACK_DEBIAN_PACKAGE_DESCRIPTION "ProxLB Additions - Additional optional patched libaries for ProxLB.")
set(CPACK_DEBIAN_PACKAGE_CONTROL_EXTRA "${CMAKE_CURRENT_SOURCE_DIR}/changelog_debian")
set(CPACK_DEBIAN_PACKAGE_DEPENDS "python3")
set(CPACK_DEBIAN_PACKAGE_LICENSE "GPL 3.0")


# Install
set(CPACK_PACKAGING_INSTALL_PREFIX ${CMAKE_INSTALL_PREFIX})
include(CPack)
