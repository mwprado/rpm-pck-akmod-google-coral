# 1. Definições Iniciais (Estrutura VirtualBox)
%if 0%{?fedora}
%global buildforkernels akmod
%endif
%global debug_package %{nil}

%global akmod_name google-coral
%global kmodsrc_name google-coral-kmodsrc

# 2. Invocação do kmodtool (Exatamente como no VirtualBox-kmod.spec)
# Note que o VirtualBox usa o kmodtool sem o prefixo em alguns casos ou 
# garante que Name e Version venham logo após.
%{?kmodtool_prefix}
%(kmodtool --target %{_target_cpu} --repo rpmfusion --kmodname google-coral-kmod %{?buildforkernels:--%{buildforkernels}} %{?kernels:--for-kernels "%{?kernels}"} 2>/dev/null)

Name:           google-coral-kmod
Version:        1.0
Release:        73%{?dist}
Summary:        Kernel module for Google Coral Edge TPU
License:        GPLv2
URL:            https://github.com/google/gasket-driver

Source1:        99-google-coral.rules
Source2:        google-coral.conf
Source5:        google-coral-group.conf

# 3. AkmodsBuildRequires (A lista exata do VirtualBox no RPM Fusion)
# O VirtualBox é muito específico com xz, time e as ferramentas de devel.
%global AkmodsBuildRequires %{_bindir}/kmodtool, %{kmodsrc_name} = %{version}, xz, time, gcc, make, kernel-devel, elfutils-libelf-devel, systemd-devel, systemd-rpm-macros
BuildRequires:  %{AkmodsBuildRequires}

# 4. Invocação Adicional de Expansão (Onde o VirtualBox injeta os pacotes)
%{expand:%(kmodtool --target %{_target_cpu} --repo rpmfusion --kmodname %{name} %{?buildforkernels:--%{buildforkernels}} %{?kernels:--for-kernels "%{?kernels}"} 2>/dev/null) }

%description
Package to manage Google Coral Edge TPU kernel modules.
This spec file is strictly based on the VirtualBox-kmod RPM Fusion template.

%prep
# Verificação de sanidade (Padrão VirtualBox)
%{?kmodtool_check}

# O VirtualBox usa setup -T -c para não descompactar nada no prep do akmod
%setup -q -T -c -n %{name}-%{version}

%build
# Vazio por design

%install
# A macro akmod_install do VirtualBox busca o tarball no kmodsrc
%{?akmod_install}

# Instalação de ficheiros auxiliares (Rules, Conf)
mkdir -p %{buildroot}%{_udevrulesdir}
install -p -m 0644 %{SOURCE1} %{buildroot}%{_udevrulesdir}/99-google-coral.rules
mkdir -p %{buildroot}%{_sysconfdir}/modules-load.d
install -p -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/modules-load.d/google-coral.conf
mkdir -p %{buildroot}%{_sysusersdir}
install -p -m 0644 %{SOURCE5} %{buildroot}%{_sysusersdir}/google-coral.conf

%pre akmod-%{akmod_name}
%sysusers_create_package %{akmod_name} %{SOURCE5}

%post akmod-%{akmod_name}
%{_sbindir}/akmods --force --akmod %{akmod_name} &>/dev/null || :

%files akmod-%{akmod_name}
%{_udevrulesdir}/99-google-coral.rules
%{_sysconfdir}/modules-load.d/google-coral.conf
%{_sysusersdir}/google-coral.conf

%changelog
* Sun Jan 11 2026 mwprado <mwprado@github> - 1.0-73
- Version 73: Strictly followed VirtualBox-kmod.spec structure from RPM Fusion.
- Uses the dual kmodtool expansion pattern.
