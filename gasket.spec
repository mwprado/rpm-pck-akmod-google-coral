%global debug_package %{nil}
%global srcname gasket-dkms

Name:           gasket
Version:        1.0
Release:        3%{?dist}
Summary:        Runtime files for Coral EdgeTPU gasket/apex kernel modules
License:        GPL-2.0-only
URL:            https://github.com/KyleGospo/gasket-dkms
Source0:        %{url}/archive/refs/heads/main.tar.gz

BuildArch:      noarch

BuildRequires:  systemd-rpm-macros

Requires(pre):  shadow-utils
Requires:       akmod-gasket >= %{version}-%{release}

Provides:       gasket-kmod-common = %{version}-%{release}

Conflicts:      gasket-dkms

%description
Runtime configuration for the Coral EdgeTPU gasket/apex kernel modules.

This package installs modules-load.d configuration and udev rules for the
gasket and apex kernel modules.

This package does not use DKMS. Kernel module builds are handled by akmods
through the akmod-gasket package.

%prep
%autosetup -n %{srcname}-main

%build

%install
install -D -p -m 0644 gasket.conf \
    %{buildroot}%{_modulesloaddir}/gasket.conf

install -D -p -m 0644 65-apex.rules \
    %{buildroot}%{_udevrulesdir}/65-apex.rules

%pre
getent group apex >/dev/null || groupadd -r apex || :

%post
if command -v udevadm >/dev/null 2>&1; then
    udevadm control --reload-rules || :
    udevadm trigger --subsystem-match=apex || :
fi

%files
%license LICENSE
%doc README.md
%{_modulesloaddir}/gasket.conf
%{_udevrulesdir}/65-apex.rules

%changelog
* Tue Apr 28 2026 Moacyr Prado <you@example.com> - 1.0-1
- Add akmod-only runtime package
- Install modules-load.d configuration and udev rule
- Create apex system group
- Do not provide or obsolete gasket-dkms
