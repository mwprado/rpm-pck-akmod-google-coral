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
Release:        2%{?dist}
Summary:        Google Coral Gasket and Apex kernel modules

License:        GPL-2.0-only
URL:            https://github.com/google/gasket-driver

# Official Google source only.
Source0:        %{url}/archive/%{commit}/gasket-driver-%{commit}.tar.gz

# Compatibility patches from KyleGospo/gasket-dkms.
Patch0:         https://github.com/KyleGospo/gasket-dkms/commit/697d5d228bf49d1fdf88792d7e85ee08a20065b0.patch
Patch1:         https://github.com/KyleGospo/gasket-dkms/commit/31feacdd7f4af194aafb2cf8c55d177b54e73f89.patch
Patch2:         https://github.com/KyleGospo/gasket-dkms/commit/95708ac8ecc511c71570d85da460b57f4d58e4ef.patch
Patch3:         https://github.com/KyleGospo/gasket-dkms/commit/8d1fb86016ef1c6f95a3fb36f3c717c7593ca402.patch
Patch4:         https://github.com/KyleGospo/gasket-dkms/commit/54a3c9f8a941c16483bbee99a83001d17e175863.patch
Patch5:         https://github.com/KyleGospo/gasket-dkms/commit/448f4373dd801d4ff68f1579ff2ec68d03be03e0.patch
Patch6:         https://github.com/KyleGospo/gasket-dkms/commit/56597d14586ceebe479d43d71a462710bb4bd1ba.patch

ExclusiveArch:  x86_64

# These are propagated into the generated akmod package and are required
# when akmods rebuilds against a newly installed kernel.
%global AkmodsBuildRequires %{_bindir}/kmodtool, gcc, make, elfutils-libelf-devel

BuildRequires:  %{AkmodsBuildRequires}
BuildRequires:  systemd-rpm-macros

# kmodtool generates akmod-gasket and kmod-gasket packages.
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


# kmodtool-generated akmod packages require:
#
#   gasket-kmod-common >= %{version}
#
# Provide that package in this same SRPM so the akmod is self-contained
# and does not depend on a second COPR build.
%package common
Summary:        Common runtime files for Google Coral Gasket/Apex modules
BuildArch:      noarch
Requires(pre):  shadow-utils
Conflicts:      gasket-dkms

%description common
Common runtime configuration for the Google Coral Gasket and Apex
kernel modules.

This package supplies the gasket-kmod-common dependency required by
akmod-gasket and installs the Apex udev rule and modules-load.d
configuration.


%prep

%{?kmodtool_check}

kmodtool \
    --target %{_target_cpu} \
    --kmodname %{kmod_name} \
    %{?buildforkernels:--%{buildforkernels}} \
    %{?kernels:--for-kernels "%{?kernels}"} \
    2>/dev/null

# Extract official Google source and apply Patch0..Patch6.
%autosetup -n gasket-driver-%{commit} -p1

# Google source uses #VERSION# in MODULE_VERSION().
find src -type f -name '*.c' \
    -exec sed -i 's/#VERSION#/%{version}/g' {} +

# Keep an independent source tree for each kernel requested by kmodtool.
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

# Runtime files for gasket-kmod-common.
install -D -p -m 0644 debian/gasket-dkms.udev \
    %{buildroot}%{_udevrulesdir}/65-apex.rules

install -d %{buildroot}%{_modulesloaddir}
cat > %{buildroot}%{_modulesloaddir}/gasket.conf <<'EOF'
gasket
apex
EOF

# Store the akmod source/SRPM under /usr/src/akmods.
%{?akmod_install}


%pre common
getent group apex >/dev/null || groupadd -r apex || :


%post common
if command -v udevadm >/dev/null 2>&1; then
    udevadm control --reload-rules || :
    udevadm trigger --subsystem-match=apex || :
fi


%files common
%license LICENSE
%doc README.md
%{_modulesloaddir}/gasket.conf
%{_udevrulesdir}/65-apex.rules


%changelog
* Mon Sep 21 2026 Moacyr Prado <mwprado@github> - 1.0.18.git20240425.5815ee3-2
- Build gasket-kmod-common in the same SRPM as akmod-gasket
- Make the akmod package self-contained for COPR and rpm-ostree
- Install upstream Apex udev rule and module loading configuration

* Sun Sep 20 2026 Moacyr Prado <mwprado@github> - 1.0.18.git20240425.5815ee3-1
- Convert Google Coral Gasket driver packaging from DKMS to akmods
- Use official google/gasket-driver source
- Add KyleGospo compatibility patches
- Support Linux 6.13+ DMA_BUF namespace changes
- Support Linux 7.1+ zap_special_vma_range
- Add Fedora akmods/kmodtool packaging
