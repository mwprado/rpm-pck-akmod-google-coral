%global commit         5815ee3908a46a415aac616ac7b9aedcb98a504c
%global shortcommit    5815ee3

Name:           gasket
Version:        1.0.18.git20240425.%{shortcommit}
Release:        1%{?dist}
Summary:        Runtime configuration for Google Coral Gasket/Apex modules

License:        GPL-2.0-only
URL:            https://github.com/google/gasket-driver
Source0:        %{url}/archive/%{commit}/gasket-driver-%{commit}.tar.gz

BuildArch:      noarch
BuildRequires:  systemd-rpm-macros

Requires(pre):  shadow-utils
Provides:       gasket-kmod-common = %{version}-%{release}
Conflicts:      gasket-dkms

%description
Runtime configuration for the Google Coral Gasket and Apex kernel modules.

This package installs the module loading configuration and the upstream
Google udev rule for the Apex Edge TPU device. Kernel module builds are
handled by akmods through the akmod-gasket package.

%prep
%autosetup -n gasket-driver-%{commit}

%build

%install
install -D -p -m 0644 debian/gasket-dkms.udev \
    %{buildroot}%{_udevrulesdir}/65-apex.rules

install -d %{buildroot}%{_modulesloaddir}
cat > %{buildroot}%{_modulesloaddir}/gasket.conf <<'EOF'
gasket
apex
EOF

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
* Sun Sep 20 2026 Moacyr Prado <mwprado@github> - 1.0.18.git20240425.5815ee3-1
- Use official google/gasket-driver source
- Provide gasket-kmod-common for akmod-gasket
- Install upstream Apex udev permissions rule
- Load gasket and apex modules at boot
- Remove DKMS runtime dependency
- Make gasket-kmod-common independent of akmod-gasket to avoid dependency cycles
