# 1. Definições Iniciais (Padrão VirtualBox)
%if 0%{?fedora}
%global buildforkernels akmod
%endif
%global debug_package %{nil}

%global akmod_name google-coral
%global kmodsrc_name google-coral-kmodsrc

Name:           google-coral-kmod
Version:        1.0
Release:        76%{?dist}
Summary:        Kernel module for Google Coral Edge TPU
License:        GPLv2
URL:            https://github.com/google/gasket-driver

Source1:        99-google-coral.rules
Source2:        google-coral.conf
Source5:        google-coral-group.conf

# 2. BuildRequires Manuais (O que o kmodtool exigiria)
BuildRequires:  %{_bindir}/kmodtool
BuildRequires:  %{kmodsrc_name} = %{version}
BuildRequires:  gcc, make, xz, time
BuildRequires:  kernel-devel, elfutils-libelf-devel
BuildRequires:  systemd-devel, systemd-rpm-macros

# 3. EXPANSÃO MANUAL DO KMODTOOL (Para não depender de macros externas)
# Invocamos o script diretamente para gerar os subpacotes binários
%{expand:%(/usr/bin/kmodtool --target %{_target_cpu} --repo rpmfusion --kmodname %{name} %{?buildforkernels:--%{buildforkernels}} %{?kernels:--for-kernels "%{?kernels}"} 2>/dev/null) }

%description
Google Coral Edge TPU kernel module infrastructure.
This spec expands RPM Fusion macros for standalone Copr builds.

# 4. DEFINIÇÃO DO SUBPACOTE AKMOD (Expandido conforme o padrão VirtualBox)
%package -n akmod-%{akmod_name}
Summary:        Akmod package for %{akmod_name} kernel module(s)
Requires:       akmods kmodtool
Requires:       %{kmodsrc_name} = %{version}
Provides:       akmod(%{akmod_name}) = %{version}-%{release}

%description -n akmod-%{akmod_name}
This package installs the akmod infrastructure for Google Coral.

%prep
# Emulação do kmodtool_check
[ -x /usr/bin/kmodtool ] || exit 1
%setup -q -T -c -n %{name}-%{version}

%build
# Vazio

%install
# 5. EXPANSÃO MANUAL DA MACRO akmod_install (O Pulo do Gato)
# Criamos o diretório de destino do akmods
mkdir -p %{buildroot}%{_usrsrc}/akmods

# Criamos o link simbólico .latest exatamente como o RPM Fusion faz
# Ele aponta para o tarball instalado pelo pacote kmodsrc
ln -sf %{_datadir}/%{kmodsrc_name}-%{version}/%{name}-%{version}.tar.xz \
    %{buildroot}%{_usrsrc}/akmods/%{akmod_name}.latest

# Instalação dos ficheiros de sistema
mkdir -p %{buildroot}%{_udevrulesdir}
install -p -m 0644 %{SOURCE1} %{buildroot}%{_udevrulesdir}/99-google-coral.rules
mkdir -p %{buildroot}%{_sysconfdir}/modules-load.d
install -p -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/modules-load.d/google-coral.conf
mkdir -p %{buildroot}%{_sysusersdir}
install -p -m 0644 %{SOURCE5} %{buildroot}%{_sysusersdir}/google-coral.conf

# 6. SCRIPTS DE MANUTENÇÃO (Expandidos do VirtualBox)
%pre 
%sysusers_create_package %{akmod_name} %{SOURCE5}

%post 
# Força a compilação do módulo após a instalação
%{_sbindir}/akmods --force --akmod %{akmod_name} &>/dev/null || :

%files -n akmod-%{akmod_name}
# Lista de ficheiros expandida
%{_usrsrc}/akmods/%{akmod_name}.latest
%{_udevrulesdir}/99-google-coral.rules
%{_sysconfdir}/modules-load.d/google-coral.conf
%{_sysusersdir}/google-coral.conf

%changelog
* Sun Jan 11 2026 mwprado <mwprado@github> - 1.0-76
- Version 76: Manually expanded akmod_install and kmodtool macros.
- Removed dependency on external rpmfusion-macros.
- Fixed .latest symlink path to strictly match VirtualBox behavior.
