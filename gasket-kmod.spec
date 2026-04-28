%if 0%{?fedora} || 0%{?rhel}
%global buildforkernels akmod
%endif

%global debug_package %{nil}
%global _kmodtool_zipmodules 0

%global srcname gasket-dkms

Name:           gasket-kmod
Version:        1.0
Release:        3%{?dist}
Summary:        Kernel modules for Google Coral EdgeTPU
License:        GPL-2.0-only
URL:            https://github.com/KyleGospo/gasket-dkms
Source0:        %{url}/archive/refs/heads/main.tar.gz
Patch0:         class-create-kernel-6.4.patch

BuildRequires:  kmodtool
BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  elfutils-libelf-devel
BuildRequires:  kernel-devel

ExclusiveArch:  x86_64 aarch64

%{expand:%(kmodtool --target %{_target_cpu} \
    --repo rpmfusion \
    --kmodname %{name} \
    %{?buildforkernels:--%{buildforkernels}} \
    %{?kernels:--for-kernels "%{?kernels}"} \
    2>/dev/null)}

%description
Kernel modules for Google Coral EdgeTPU.

This package builds the gasket and apex kernel modules using akmods.

%prep
%{?kmodtool_check}

kmodtool --target %{_target_cpu} \
    --repo rpmfusion \
    --kmodname %{name} \
    %{?buildforkernels:--%{buildforkernels}} \
    %{?kernels:--for-kernels "%{?kernels}"} \
    2>/dev/null

%autosetup -n %{srcname}-main -p1

rm -f src/dkms.conf

for kernel_version in %{?kernel_versions}; do
    cp -a src "_kmod_build_${kernel_version%%___*}"
done

%build
for kernel_version in %{?kernel_versions}; do
    make V=1 %{?_smp_mflags} \
        -C "${kernel_version##*___}" \
        M="${PWD}/_kmod_build_${kernel_version%%___*}" \
        modules
done

%install
for kernel_version in %{?kernel_versions}; do
    install -d \
        "%{buildroot}%{kmodinstdir_prefix}/${kernel_version%%___*}/%{kmodinstdir_postfix}"

    install -p -m 0755 \
        "_kmod_build_${kernel_version%%___*}/gasket.ko" \
        "%{buildroot}%{kmodinstdir_prefix}/${kernel_version%%___*}/%{kmodinstdir_postfix}/gasket.ko"

    install -p -m 0755 \
        "_kmod_build_${kernel_version%%___*}/apex.ko" \
        "%{buildroot}%{kmodinstdir_prefix}/${kernel_version%%___*}/%{kmodinstdir_postfix}/apex.ko"
done

%{?akmod_install}

%changelog
* Tue Apr 28 2026 Moacyr Prado <you@example.com> - 1.0-1
- Convert gasket driver from DKMS packaging to akmod packaging
