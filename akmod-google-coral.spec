%if 0%{?fedora}
%global buildforkernels akmod
%endif
%global debug_package %{nil}

Name:           google-coral-kmod
Version:        1.0
Release:        27.20260105git5815ee3%{?dist}
Summary:        Google Coral Edge TPU kernel module
License:        GPLv2
URL:            https://github.com/google/gasket-driver

Source0:        %{url}/archive/5815ee3908a46a415aac616ac7b9aedcb98a504c/gasket-driver-5815ee3.tar.gz
Source1:        99-google-coral.rules
Source2:        google-coral.conf
Source3:        fix-for-no_llseek.patch
Source4:        fix-for-module-import-ns.patch
Source5:        google-coral-group.conf

# BuildRequires idênticos ao nvidia-kmod.spec
BuildRequires:  %{_bindir}/kmodtool
BuildRequires:  gcc, make, kernel-devel, elfutils-libelf-devel
BuildRequires:  systemd-devel, systemd-rpm-macros

# O SEGREDO DO NVIDIA-KMOD: 
# Usar a chamada do kmodtool SEM o %{expand:...} que está quebrando no rpkg, 
# mas mantendo a lógica de checagem de kernels.
%{!?kernels:%{?buildforkernels: %(%{_bindir}/kmodtool --target %{_target_cpu} --repo %{name} --akmod %{name} %{?buildforkernels:--%{buildforkernels}} 2>/dev/null)}}

%description
Este pacote segue o padrão exato do driver NVIDIA (RPM Fusion).
Fornece suporte para o hardware Google Coral Edge TPU.

%prep
%setup -q -n gasket-driver-5815ee3908a46a415aac616ac7b9aedcb98a504c
%patch -P 3 -p1
%patch -P 4 -p1

# Prepara a estrutura como a NVIDIA faz
mkdir -p _kmod_build_%{_target_cpu}
cp -r src/* _kmod_build_%{_target_cpu}/

%build
for kernel_version in %{?kernel_versions} ; do
    make -C /lib/modules/${kernel_version%%___*}/build M=$(pwd)/_kmod_build_${kernel_version##*___} modules
done

%install
# Instalação dos fontes para o akmod
install -d %{buildroot}%{_usrsrc}/akmods/google-coral
cp -r src/* %{buildroot}%{_usrsrc}/akmods/google-coral/

# Arquivos auxiliares
install -D -m 0644 %{SOURCE1} %{buildroot}%{_udevrulesdir}/99-google-coral.rules
install -D -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/modules-load.d/google-coral.conf
install -D -m 0644 %{SOURCE5} %{buildroot}%{_sysusersdir}/google-coral.conf

%pre
%sysusers_create_package google-coral %{SOURCE5}

%files
%license LICENSE
%{_usrsrc}/akmods/google-coral
%{_udevrulesdir}/99-google-coral.rules
%{_sysconfdir}/modules-load.d/google-coral.conf
%{_sysusersdir}/google-coral.conf

%changelog
* Sat Jan 10 2026 mwprado <mwprado@github> - 1.0-27
- Ajuste na macro kmodtool para compatibilidade com rpkg/Copr.
- Removido %expand desnecessário que causava Unknown Tag.
