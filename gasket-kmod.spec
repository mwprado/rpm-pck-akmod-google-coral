# SPDX-License-Identifier: GPL-2.0-only

%global kmod_name      gasket

# Latest google/gasket-driver upstream commit
# 2024-04-25: "fixed eventfd_signal for kernels >= 6.8"
%global commit         5815ee3908a46a415aac616ac7b9aedcb98a504c
%global shortcommit    5815ee3

%if 0%{?fedora}
%global buildforkernels akmod
%endif

%global debug_package %{nil}

# Kernel modules inherit the kernel build flags.
%undefine _auto_set_build_flags

Name:           %{kmod_name}-kmod
Version:        1.0.18.git20240425.%{shortcommit}
Release:        1%{?dist}
Summary:        Google Coral Gasket and Apex kernel modules

License:        GPL-2.0-only
URL:            https://github.com/google/gasket-driver

#
# Official Google source only.
#
Source0:        %{url}/archive/%{commit}/gasket-driver-%{commit}.tar.gz

#
# Compatibility patches from KyleGospo/gasket-dkms.
#
# no_llseek disappeared from modern kernels.
#
Patch0:         https://github.com/KyleGospo/gasket-dkms/commit/697d5d228bf49d1fdf88792d7e85ee08a20065b0.patch
Patch1:         https://github.com/KyleGospo/gasket-dkms/commit/31feacdd7f4af194aafb2cf8c55d177b54e73f89.patch

#
# RHEL 9.4 class_create() backport.
#
Patch2:         https://github.com/KyleGospo/gasket-dkms/commit/95708ac8ecc511c71570d85da460b57f4d58e4ef.patch

#
# RHEL 9.5 eventfd_signal() backport.
#
Patch3:         https://github.com/KyleGospo/gasket-dkms/commit/8d1fb86016ef1c6f95a3fb36f3c717c7593ca402.patch

#
# Linux >= 6.13:
# MODULE_IMPORT_NS() namespace became a string.
#
Patch4:         https://github.com/KyleGospo/gasket-dkms/commit/54a3c9f8a941c16483bbee99a83001d17e175863.patch

#
# Fix use of RHEL_RELEASE_VERSION() on non-RHEL kernels.
#
Patch5:         https://github.com/KyleGospo/gasket-dkms/commit/448f4373dd801d4ff68f1579ff2ec68d03be03e0.patch

#
# Linux >= 7.1:
# zap_vma_ptes() -> zap_special_vma_range().
#
Patch6:         https://github.com/KyleGospo/gasket-dkms/commit/56597d14586ceebe479d43d71a462710bb4bd1ba.patch

ExclusiveArch:  x86_64

#
# These are propagated by kmodtool into the generated akmod package,
# because they are required when akmods rebuilds against a new kernel.
#
%global AkmodsBuildRequires %{_bindir}/kmodtool, gcc, make, elfutils-libelf-devel

BuildRequires:  %{AkmodsBuildRequires}

#
# kmodtool generates:
#
#   akmod-gasket
#   kmod-gasket
#   kmod-gasket-<kernel>
#
%{expand:%(kmodtool \
    --target %{_target_cpu} \
    --kmodname %{kmod_name} \
    %{?buildforkernels:--%{buildforkernels}} \
    %{?kernels:--for-kernels "%{?kernels}"} \
    2>/dev/null)}


%description
The Coral Gasket Driver allows use of Google Coral Edge TPU devices
on Linux.

It provides two kernel modules:

  gasket - Google ASIC Software Kernel Extensions and Tools
  apex   - Google Edge TPU v1 PCIe driver

This package uses the official Google gasket-driver source with
compatibility fixes required for current Fedora kernels.


%prep

# Abort if kmodtool detected an invalid configuration.
%{?kmodtool_check}

# Useful in COPR logs: show exactly what kmodtool generated.
kmodtool \
    --target %{_target_cpu} \
    --kmodname %{kmod_name} \
    %{?buildforkernels:--%{buildforkernels}} \
    %{?kernels:--for-kernels "%{?kernels}"} \
    2>/dev/null

#
# Extract official Google source and apply Patch0..Patch6.
#
%autosetup -n gasket-driver-%{commit} -p1

#
# Google source uses #VERSION# in MODULE_VERSION().
#
find src -type f -name '*.c' \
    -exec sed -i 's/#VERSION#/%{version}/g' {} +

#
# akmods/kmodtool may request builds against more than one kernel.
# Keep an independent source tree for each one.
#
for kernel_version in %{?kernel_versions}; do
    cp -a src _kmod_build_${kernel_version%%___*}
done


%build

for kernel_version in %{?kernel_versions}; do

    echo
    echo "============================================================"
    echo " Building Gasket for ${kernel_version%%___*}"
    echo " Kernel source: ${kernel_version##*___}"
    echo "============================================================"
    echo

    make V=1 %{?_smp_mflags} \
        -C "${kernel_version##*___}" \
        M="${PWD}/_kmod_build_${kernel_version%%___*}" \
        modules
done


%install

for kernel_version in %{?kernel_versions}; do

    install -d \
        %{buildroot}%{kmodinstdir_prefix}${kernel_version%%___*}%{kmodinstdir_postfix}

    install -p -m 0755 \
        _kmod_build_${kernel_version%%___*}/gasket.ko \
        %{buildroot}%{kmodinstdir_prefix}${kernel_version%%___*}%{kmodinstdir_postfix}/gasket.ko

    install -p -m 0755 \
        _kmod_build_${kernel_version%%___*}/apex.ko \
        %{buildroot}%{kmodinstdir_prefix}${kernel_version%%___*}%{kmodinstdir_postfix}/apex.ko
done

#
# Build and install the SRPM that akmods will retain under
# /usr/src/akmods and rebuild when a new kernel is installed.
#
%{?akmod_install}


%changelog
* Sun Sep 20 2026 Moacyr Prado <mwprado@github> - 1.0.18.git20240425.5815ee3-1
- Convert Google Coral Gasket driver packaging from DKMS to akmods
- Use official google/gasket-driver source
- Add KyleGospo compatibility patches
- Support Linux 6.13+ DMA_BUF namespace changes
- Support Linux 7.1+ zap_special_vma_range
- Add Fedora akmods/kmodtool packaging
