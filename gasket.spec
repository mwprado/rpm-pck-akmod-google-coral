%global debug_package %{nil}

%global srcname gasket-dkms

Name:           gasket
Version:        1.0
Release:        1%{?dist}
Summary:        Runtime files for Google Coral EdgeTPU kernel modules
License:        GPL-2.0-only
URL:            https://github.com/KyleGospo/gasket-dkms
Source0:        %{url}/archive/refs/heads/main.tar.gz

BuildArch:      noarch

BuildRequires:  systemd-rpm-macros

Requires:       akmod-gasket = %{version}-%{release}
Requires(pre):  shadow-utils

Provides:       gasket-kmod-common = %{version}-%{release}

Obsoletes:      gasket-dkms < %{version}-%{release}
Provides:       gasket-dkms = %{version}-%{release}

%description
Runtime configuration for the Google Coral EdgeTPU gasket/apex kernel modules.

This package installs modules-load.d configuration, udev rules, and the apex
system group. The actual kernel modules are provided by akmod-gasket.

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
* Sun Apr 26 2026 Moacyr Prado <you@example.com> - 1.0-1
- Add runtime package for akmod-gasket
