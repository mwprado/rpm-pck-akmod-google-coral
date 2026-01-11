%if 0%{?fedora}
%global buildforkernels akmod
%endif
%global debug_package %{nil}

# NOME IGUAL AO DA NVIDIA NO CACHE
%global akmod_name google-coral

Name:           google-coral-kmod
Version:        1.0
Release:        29.20260105git5815ee3%{?dist}
Summary:        Google Coral Edge TPU kernel module
License:        GPLv2
URL:            https://github.com/google/gasket-driver

Source0:        %{url}/archive/5815ee3908a46a415aac616ac7b9aedcb98a504c/gasket-driver-5815ee3.tar.gz
Source1:        99-google-coral.rules
Source2:        google-coral.conf
Source3:        fix-for-no_llseek.patch
Source4:        fix-for-module-import-ns.patch
Source5:        google-coral-group.conf

BuildRequires:  %{_bindir}/kmodtool
BuildRequires:  gcc, make, kernel-devel, elfutils-libelf-devel
BuildRequires:  systemd-devel, systemd-rpm-macros

# GATILHO DE PROVIDES (O que faz aparecer no cache)
Provides:       akmod(%{akmod_name}) = %{version}-%{release}

# ESTA LINHA PRECISA CRIAR O VÍNCULO COM O AKMODS
%{!?kernels:%{?buildforkernels: %{expand:%( %{_bindir}/kmodtool --target %{_target_cpu} --repo %{name} --akmod %{akmod_name} %{?buildforkernels:--%{buildforkernels}} 2>/dev/null )}}}

%description
Google Coral TPU driver. Este pacote gera o kmod no cache do akmods.

%prep
%setup -q -n gasket-driver-5815ee3908a46a415aac616ac7b9aedcb98a504c
%patch -P 3 -p1
%patch -P 4 -p1

%build
# Vazio, o build real acontece via akmods

%install
# O AKMODS procura o código em /usr/src/akmods/NOME
install -d %{buildroot}%{_usrsrc}/akmods/%{akmod_name}
cp -r src/* %{buildroot}%{_usrsrc}/akmods/%{akmod_name}/

# ARQUIVO DE MAPEAMENTO (Essencial para o comando 'akmods --akmod google-coral')
install -d %{buildroot}%{_sysconfdir}/akmods
echo "%{akmod_name}" > %{buildroot}%{_sysconfdir}/akmods/%{akmod_name}.nm

install -D -m 0644 %{SOURCE1} %{buildroot}%{_udevrulesdir}/99-google-coral.rules
install -D -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/modules-load.d/google-coral.conf
install -D -m 0644 %{SOURCE5} %{buildroot}%{_sysusersdir}/google-coral.conf

%files
%license LICENSE
%{_usrsrc}/akmods/%{akmod_name}
%{_sysconfdir}/akmods/%{akmod_name}.nm
%{_udevrulesdir}/99-google-coral.rules
%{_sysconfdir}/modules-load.d/google-coral.conf
%{_sysusersdir}/google-coral.conf

%changelog
* Sat Jan 10 2026 mwprado <mwprado@github> - 1.0-29
- Alinhamento de diretório para garantir criação de /var/cache/akmods/google-coral.
