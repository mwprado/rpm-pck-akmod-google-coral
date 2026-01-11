# 1. Definições de controle
%if 0%{?fedora}
%global buildforkernels akmod
%endif
%global debug_package %{nil}

%global akmod_name google-coral
%global kmodsrc_name google-coral-kmodsrc

# Metadados principais
Name:           google-coral-kmod
Version:        1.0
Release:        66%{?dist}
Summary:        Kernel module for Google Coral Edge TPU
License:        GPLv2
URL:            https://github.com/google/gasket-driver

Source1:        99-google-coral.rules
Source2:        google-coral.conf
Source5:        google-coral-group.conf

# 2. BuildRequires (Padrão NVIDIA)
%global AkmodsBuildRequires %{_bindir}/kmodtool, %{kmodsrc_name} = %{version}, xz, time, gcc, make, kernel-devel, elfutils-libelf-devel, systemd-devel, systemd-rpm-macros
BuildRequires:  %{AkmodsBuildRequires}

# 3. O SEGREDO DO RPM FUSION: Invocação do kmodtool com prefixo
# Isso garante que o subpacote akmod-google-coral seja criado IMEDIATAMENTE.
%{?kmodtool_prefix}
%{expand:%(kmodtool --target %{_target_cpu} --repo rpmfusion --kmodname %{name} %{?buildforkernels:--%{buildforkernels}} %{?kernels:--for-kernels "%{?kernels}"} 2>/dev/null) }

%description
Package to manage Google Coral Edge TPU kernel modules.
Follows NVIDIA and VirtualBox packaging standards for RPM Fusion.

%prep
# Verificação do kmodtool
%{?kmodtool_check}
%setup -q -T -c -n %{name}-%{version}

%build
# Vazio

%install
# A macro akmod_install cria o link .latest em /usr/src/akmods/
%{?akmod_install}

mkdir -p %{buildroot}%{_udevrulesdir}
install -p -m 0644 %{SOURCE1} %{buildroot}%{_udevrulesdir}/99-google-coral.rules
mkdir -p %{buildroot}%{_sysconfdir}/modules-load.d
install -p -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/modules-load.d/google-coral.conf
mkdir -p %{buildroot}%{_sysusersdir}
install -p -m 0644 %{SOURCE5} %{buildroot}%{_sysusersdir}/google-coral.conf

# 4. Scripts vinculados ao pacote gerado dinamicamente
%pre -n akmod-google-coral
%sysusers_create_package %{akmod_name} %{SOURCE5}

%post -n akmod-google-coral
%{_sbindir}/akmods --force --akmod %{akmod_name} &>/dev/null || :

%files -n akmod-google-coral
%{_udevrulesdir}/99-google-coral.rules
%{_sysconfdir}/modules-load.d/google-coral.conf
%{_sysusersdir}/google-coral.conf

%changelog
* Sun Jan 11 2026 mwprado <mwprado@github> - 1.0-66
- Version 66: Forced kmodtool expansion to ensure akmod-google-coral is visible to rpkg.
- Removed manual description to avoid collision with dynamic output.
