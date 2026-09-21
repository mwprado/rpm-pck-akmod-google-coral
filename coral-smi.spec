# SPDX-License-Identifier: MIT

%global commit 38cb3887235adca32de83732852c15073fa66afd

Name:           coral-smi
Version:        0.1.0
Release:        1%{?dist}
Summary:        Monitoring utility for Google Coral PCIe/M.2 Edge TPU devices

License:        MIT
URL:            https://github.com/mwprado/rpm-pck-akmod-google-coral

Source0:        https://raw.githubusercontent.com/mwprado/rpm-pck-akmod-google-coral/%{commit}/coral-smi#/coral-smi
Source1:        https://raw.githubusercontent.com/mwprado/rpm-pck-akmod-google-coral/%{commit}/coral-smi-LICENSE#/coral-smi-LICENSE

BuildArch:      noarch

BuildRequires:  python3
Requires:       python3

%description
coral-smi is a lightweight monitoring utility for Google Coral PCIe/M.2
Edge TPU devices using the Apex/Gasket kernel driver.

It reads the Apex sysfs interface, /proc/interrupts and process file
descriptors to report device temperature, thermal limits, mapped pages,
PCI address, active processes and interrupt activity.

The upstream Apex driver does not expose a reliable hardware busy-cycle
counter, so coral-smi intentionally does not fabricate a utilization
percentage. Continuous mode reports interrupt activity per second instead.


%prep
# No source archive to unpack.


%build
# Pure Python; nothing to compile.


%check
python3 -c 'compile(open("%{SOURCE0}", encoding="utf-8").read(), "%{SOURCE0}", "exec")'


%install
install -D -p -m 0755 %{SOURCE0}     %{buildroot}%{_bindir}/coral-smi

install -D -p -m 0644 %{SOURCE1}     %{buildroot}%{_licensedir}/%{name}/LICENSE


%files
%license %{_licensedir}/%{name}/LICENSE
%{_bindir}/coral-smi


%changelog
* Sun Sep 20 2026 Moacyr Prado <mwprado@github> - 0.1.0-1
- Initial coral-smi package
- Report Apex temperature, thermal limits and mapped pages
- Report PCI address and processes using /dev/apex_N
- Add interrupt-rate activity monitoring and JSON output
