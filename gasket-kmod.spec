# SPDX-License-Identifier: GPL-2.0-only

%global kmod_name      gasket

# Latest google/gasket-driver upstream commit
# 2024-04-25: "fixed eventfd_signal for kernels >= 6.8"
%global commit         5815ee3908a46a415aac616ac7b9aedcb98a504c
%global shortcommit    5815ee3

# COPR builds both Fedora and EPEL as akmods.  Without this on EL,
# kmodtool falls back to build-system kernel discovery and requires
# --repo plus buildsys-build-<repo>-kerneldevpkgs, which is not available
# in a normal COPR EPEL chroot.
%if 0%{?fedora} || 0%{?rhel}
%global buildforkernels akmod
%endif

%global debug_package %{nil}

# Kernel modules inherit the kernel build flags.
%undefine _auto_set_build_flags

Name:           %{kmod_name}-kmod
Version:        1.0.18.git20240425.%{shortcommit}
Release:        6%{?dist}
Summary:        Google Coral Gasket and Apex kernel modules

License:        GPL-2.0-only
URL:            https://github.com/google/gasket-driver

# Official Google source only.
Source0:        %{url}/archive/%{commit}/gasket-driver-%{commit}.tar.gz
# Declarative system group for the Apex udev permissions rule.
Source1:        https://raw.githubusercontent.com/mwprado/rpm-pck-akmod-google-coral/c88873bed10126c855e7a275210f72dd087819cf/apex.sysusers#/apex.sysusers

# Compatibility patches from KyleGospo/gasket-dkms.
Patch0:         https://github.com/KyleGospo/gasket-dkms/commit/697d5d228bf49d1fdf88792d7e85ee08a20065b0.patch
Patch1:         https://github.com/KyleGospo/gasket-dkms/commit/31feacdd7f4af194aafb2cf8c55d177b54e73f89.patch
Patch2:         https://github.com/KyleGospo/gasket-dkms/commit/95708ac8ecc511c71570d85da460b57f4d58e4ef.patch
Patch3:         https://github.com/KyleGospo/gasket-dkms/commit/8d1fb86016ef1c6f95a3fb36f3c717c7593ca402.patch
Patch4:         https://github.com/KyleGospo/gasket-dkms/commit/54a3c9f8a941c16483bbee99a83001d17e175863.patch
Patch5:         https://github.com/KyleGospo/gasket-dkms/commit/448f4373dd801d4ff68f1579ff2ec68d03be03e0.patch
Patch6:         https://github.com/KyleGospo/gasket-dkms/commit/56597d14586ceebe479d43d71a462710bb4bd1ba.patch

# Local correctness fixes found while auditing the archived Google driver.
Patch7:         0001-apex-fix-reset-error-handling-and-probe-delay.patch
Patch8:         0002-gasket-make-device-slot-allocation-race-free.patch
Patch9:         0003-gasket-propagate-pci-and-dma-setup-errors.patch

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
#   gasket-kmod-common >= matching package version
#
# Provide that package in this same SRPM so the akmod is self-contained
# and does not depend on a second COPR build.
%package common
Summary:        Common runtime files for Google Coral Gasket/Apex modules
BuildArch:      noarch
Requires(pre):  systemd
Conflicts:      gasket-dkms

%description common
Common runtime configuration for the Google Coral Gasket and Apex
kernel modules.

This package supplies the gasket-kmod-common dependency required by
akmod-gasket and installs the Apex udev rule, modules-load.d configuration
and a declarative systemd-sysusers definition for the apex group.


%prep

%{?kmodtool_check}

kmodtool \
    --target %{_target_cpu} \
    --kmodname %{kmod_name} \
    %{?buildforkernels:--%{buildforkernels}} \
    %{?kernels:--for-kernels "%{?kernels}"} \
    2>/dev/null

# Extract official Google source and apply compatibility and local fixes.
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

# Declare the group referenced by the upstream udev rule.  Keep the GID
# dynamic so Fedora/Silverblue can allocate it consistently.
install -D -p -m 0644 %{SOURCE1} \
    %{buildroot}%{_sysusersdir}/gasket.conf

install -d %{buildroot}%{_modulesloaddir}
cat > %{buildroot}%{_modulesloaddir}/gasket.conf <<'EOF'
gasket
apex
EOF

# Store the akmod source/SRPM under /usr/src/akmods.
%{?akmod_install}


%pre common
# Materialize the declarative group before package files are installed.
# This avoids direct groupadd manipulation and works with local admin
# overrides through the normal sysusers.d precedence rules.
%sysusers_create_package gasket %{SOURCE1}


%post common
if command -v udevadm >/dev/null 2>&1; then
    udevadm control --reload-rules || :
    udevadm trigger --subsystem-match=apex || :
fi


%files common
%license LICENSE
%doc README.md
%{_modulesloaddir}/gasket.conf
%{_sysusersdir}/gasket.conf
%{_udevrulesdir}/65-apex.rules


%changelog
* Mon Sep 21 2026 Moacyr Prado <mwprado@github> - 1.0.18.git20240425.5815ee3-6
- Generate akmod packages on EPEL/RHEL as well as Fedora
- Avoid kmodtool build-system kernel discovery and its --repo requirement
- Keep COPR EPEL builds independent of buildsys-build-*-kerneldevpkgs helpers

* Mon Sep 21 2026 Moacyr Prado <mwprado@github> - 1.0.18.git20240425.5815ee3-5
- Fix malformed unified-diff metadata in the device-slot race patch
- Revalidate local Gasket patch hunk counts before akmod build
- Avoid RPM macro expansion in a documentation comment

* Mon Sep 21 2026 Moacyr Prado <mwprado@github> - 1.0.18.git20240425.5815ee3-4
- Check apex_reset() failures during PCI probe
- Use a real millisecond sleep between Apex readiness retries
- Make Gasket device-slot allocation race-free for concurrent probes
- Check DMA mask setup and preserve original PCI setup errors

* Mon Sep 21 2026 Moacyr Prado <mwprado@github> - 1.0.18.git20240425.5815ee3-3
- Replace direct groupadd with declarative systemd-sysusers configuration
- Install the apex group definition through gasket-kmod-common
- Keep the apex GID dynamically allocated for Fedora and Silverblue

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
