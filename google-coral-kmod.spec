%global kmodname google-coral
%global kmodsrc_name google-coral-kmodsrc

%if 0%{?fedora}
%global buildforkernels akmod
%endif
%global debug_package %{nil}

Name:           %{kmodname}-kmod
Version:        1.0
Release:        81%{?dist}
Summary:        Kernel module for Google Coral Edge TPU
License:        GPLv2
URL:            https://github.com/google/gasket-driver

Source1:        99-google-coral.rules
Source2:        google-coral.conf
Source5:        google-coral-group.conf

BuildRequires:  %{_bindir}/kmodtool
BuildRequires:  %{kmodsrc_name} = %{version}
BuildRequires:  gcc, make, xz, time, kernel-devel, elfutils-libelf-devel, systemd-devel, systemd-rpm-macros

# 1. Injeção do kmodtool (Aqui ele cria o %package e a lista de %files básica)
%{expand:%(/usr/bin/kmodtool --target %{_target_cpu} --repo rpmfusion --kmodname %{name} %{?buildforkernels:--%{buildforkernels}} %{?kernels:--for-kernels "%{?kernels}"} 2>/dev/null) }

%description
Google Coral Edge TPU kernel module infrastructure.

%prep
%{?kmodtool_check}
%setup -q -T -c -n %{name}-%{version}

%build
# Vazio

%install
# 2. Instalação manual
mkdir -p %{buildroot}%{_usrsrc}/akmods
ln -sf %{_datadir}/%{kmodsrc_name}-%{version}/%{name}-%{version}.tar.xz \
    %{buildroot}%{_usrsrc}/akmods/%{kmodname}.latest

mkdir -p %{buildroot}%{_udevrulesdir}
install -p -m 0644 %{SOURCE1} %{buildroot}%{_udevrulesdir}/99-google-coral.rules
mkdir -p %{buildroot}%{_sysconfdir}/modules-load.d
install -p -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/modules-load.d/google-coral.conf
mkdir -p %{buildroot}%{_sysusersdir}
install -p -m 0644 %{SOURCE5} %{buildroot}%{_sysusersdir}/google-coral.conf

# 3. A SOLUÇÃO RIGOROSA: 
# O VirtualBox usa esta macro para adicionar ficheiros à lista gerada pelo kmodtool
# sem precisar de uma nova seção %files -n.
%global akmod_files %{_usrsrc}/akmods/%{kmodname}.latest %{_udevrulesdir}/99-google-coral.rules %{_sysconfdir}/modules-load.d/google-coral.conf %{_sysusersdir}/google-coral.conf

%changelog
* Sun Jan 11 2026 mwprado <mwprado@github> - 1.0-81
- Version 81: Strict VirtualBox clone. 
- Avoided '%files -n' to prevent duplicate package errors.
- Used 'akmod_files' global override to package extra system files.
