%global kmodname google-coral
%global kmodsrc_name google-coral-kmodsrc

%if 0%{?fedora}
%global buildforkernels akmod
%endif
%global debug_package %{nil}

Name:           %{kmodname}-kmod
Version:        1.0
Release:        89%{?dist}
Summary:        Kernel module for Google Coral Edge TPU
License:        GPLv2
URL:            https://github.com/google/gasket-driver

Source1:        99-google-coral.rules
Source2:        google-coral.conf
Source5:        google-coral-group.conf

BuildRequires:  %{_bindir}/kmodtool
BuildRequires:  %{kmodsrc_name} = %{version}
BuildRequires:  gcc, make, xz, time, kernel-devel, elfutils-libelf-devel, systemd-devel, systemd-rpm-macros

# 1. Invocação do kmodtool (Define o pacote akmod-google-coral dinamicamente)
%{?kmodtool_prefix}
%{expand:%(/usr/bin/kmodtool --target %{_target_cpu} --repo rpmfusion --kmodname %{name} %{?buildforkernels:--%{buildforkernels}} %{?kernels:--for-kernels "%{?kernels}"} 2>/dev/null) }

%description
Google Coral Edge TPU kernel module infrastructure.

%prep
%{?kmodtool_check}
%setup -q -T -c -n %{name}-%{version}

%build
# Vazio

%install
# 2. Instalação (Rigor VirtualBox)
mkdir -p %{buildroot}%{_usrsrc}/akmods
# O link .latest aponta para o SRPM que está no mesmo diretório (conforme seus exemplos)
ln -sf %{name}-%{version}-%{release}.src.rpm %{buildroot}%{_usrsrc}/akmods/%{kmodname}.latest

mkdir -p %{buildroot}%{_udevrulesdir}
install -p -m 0644 %{SOURCE1} %{buildroot}%{_udevrulesdir}/99-google-coral.rules
mkdir -p %{buildroot}%{_sysconfdir}/modules-load.d
install -p -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/modules-load.d/google-coral.conf
mkdir -p %{buildroot}%{_sysusersdir}
install -p -m 0644 %{SOURCE5} %{buildroot}%{_sysusersdir}/google-coral.conf

# 3. ATRIBUIÇÃO DOS ARQUIVOS (O Padrão VirtualBox)
# Definimos esta macro ANTES da chamada de arquivos do kmodtool.
# O script kmodtool usa essa macro para preencher a seção %files do pacote akmod.
%global kmodtool_files %{_udevrulesdir}/99-google-coral.rules %{_sysconfdir}/modules-load.d/google-coral.conf %{_sysusersdir}/google-coral.conf %{_usrsrc}/akmods/%{kmodname}.latest

# Chamamos a macro que injeta os arquivos na seção %files correta do subpacote
%{?kmodtool_files}

%changelog
* Tue Jan 13 2026 mwprado <mwprado@github> - 1.0-89
- Version 89: Implemented kmodtool_files macro to assign files to the dynamic akmod package.
- Removed manual %files section to avoid container package conflicts.
- Follows strict VirtualBox/RPM Fusion directory structure.
