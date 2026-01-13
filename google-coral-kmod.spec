%global kmodname google-coral
%global kmodsrc_name google-coral-kmodsrc

%if 0%{?fedora}
%global buildforkernels akmod
%endif
%global debug_package %{nil}

Name:           %{kmodname}-kmod
Version:        1.0
Release:        87%{?dist}
Summary:        Kernel module for Google Coral Edge TPU
License:        GPLv2
URL:            https://github.com/google/gasket-driver

Source1:        99-google-coral.rules
Source2:        google-coral.conf
Source5:        google-coral-group.conf

BuildRequires:  %{_bindir}/kmodtool
BuildRequires:  %{kmodsrc_name} = %{version}
BuildRequires:  gcc, make, xz, time, kernel-devel, elfutils-libelf-devel, systemd-devel, systemd-rpm-macros

# 1. Injeção dinâmica (Como manda a seção 2.1 da doc)
%{expand:%(/usr/bin/kmodtool --target %{_target_cpu} --repo rpmfusion --kmodname %{name} %{?buildforkernels:--%{buildforkernels}} %{?kernels:--for-kernels "%{?kernels}"} 2>/dev/null) }

%description
Google Coral Edge TPU kernel module infrastructure.
Rigorously follows RPM Fusion Kmods2 documentation.

%prep
%{?kmodtool_check}
%setup -q -T -c -n %{name}-%{version}

%build
# Vazio

%install
# 2. O link .latest (Relativo conforme NVIDIA/VirtualBox)
mkdir -p %{buildroot}%{_usrsrc}/akmods
ln -sf %{name}-%{version}-%{release}.src.rpm %{buildroot}%{_usrsrc}/akmods/%{kmodname}.latest

# Instalação de arquivos extras
mkdir -p %{buildroot}%{_udevrulesdir}
install -p -m 0644 %{SOURCE1} %{buildroot}%{_udevrulesdir}/99-google-coral.rules
mkdir -p %{buildroot}%{_sysconfdir}/modules-load.d
install -p -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/modules-load.d/google-coral.conf
mkdir -p %{buildroot}%{_sysusersdir}
install -p -m 0644 %{SOURCE5} %{buildroot}%{_sysusersdir}/google-coral.conf

# 3. A SOLUÇÃO DA DOCUMENTAÇÃO (Seção 5.1 - Extra files)
# Definimos a variável que o kmodtool usa para construir a seção %files dinamicamente.
# Isso evita o erro de "unpackaged files" sem precisar de %files -n manual.
%global kmod_files %{_udevrulesdir}/99-google-coral.rules %{_sysconfdir}/modules-load.d/google-coral.conf %{_sysusersdir}/google-coral.conf %{_usrsrc}/akmods/%{kmodname}.latest

%changelog
* Tue Jan 13 2026 mwprado <mwprado@github> - 1.0-87
- Version 87: Implemented kmod_files global as per RPM Fusion Kmods2 documentation.
- Resolved unpackaged files error by injecting files into the dynamic filelist.
