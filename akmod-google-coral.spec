%if 0%{?fedora}
%global buildforkernels akmod
%endif
%global debug_package %{nil}

%global akmod_name google-coral

Name:           google-coral-kmod
Version:        1.0
Release:        43.20260105git5815ee3%{?dist}
Summary:        Google Coral Edge TPU kernel module (Akmod Container)
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

# O Provide que o comando 'akmods' monitora
Provides:       akmod(%{akmod_name}) = %{version}-%{release}

%{!?kernels:%{?buildforkernels: %{expand:%( %{_bindir}/kmodtool --target %{_target_cpu} --repo %{name} --akmod %{akmod_name} %{?buildforkernels:--%{buildforkernels}} %{?kernels:--kmp %{?kernels}} 2>/dev/null )}}}

%description
Este pacote contém o código-fonte compactado do driver Google Coral. 
Ao ser instalado, ele disponibiliza um arquivo que o utilitário akmods 
utiliza para reconstruir o driver a cada atualização de kernel.

%prep
%setup -q -n gasket-driver-5815ee3908a46a415aac616ac7b9aedcb98a504c
%patch -P 3 -p1
%patch -P 4 -p1

%build
# Aqui nós preparamos o "conteúdo" que vai ser reconstruído pelo akmods
# No padrão NVIDIA, isso seria um .src.rpm real. 
# Como estamos no Copr, vamos entregar o tarball patcheado.

%install
install -d %{buildroot}%{_usrsrc}/akmods/

# 1. Geramos o arquivo que simula o SRPM (tarball patcheado)
# O akmodsbuild aceita .tar.gz se ele contiver a estrutura de build
tar -czf %{buildroot}%{_usrsrc}/akmods/%{akmod_name}-%{version}.tar.gz .

# 2. O LINK .LATEST (Apontando para o ARQUIVO, não pasta)
pushd %{buildroot}%{_usrsrc}/akmods/
ln -s %{akmod_name}-%{version}.tar.gz %{akmod_name}.latest
popd

# Suporte ao hardware
install -D -m 0644 %{SOURCE1} %{buildroot}%{_udevrulesdir}/99-google-coral.rules
install -D -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/modules-load.d/google-coral.conf
install -D -m 0644 %{SOURCE5} %{buildroot}%{_sysusersdir}/google-coral.conf

%pre
%sysusers_create_package google-coral %{SOURCE5}

%files
%license LICENSE
# O akmod-nvidia lista o .src.rpm aqui. Nós listamos o nosso tarball de fontes.
%{_usrsrc}/akmods/%{akmod_name}-%{version}.tar.gz
%{_usrsrc}/akmods/%{akmod_name}.latest
%{_udevrulesdir}/99-google-coral.rules
%{_sysconfdir}/modules-load.d/google-coral.conf
%{_sysusersdir}/google-coral.conf

%changelog
* Sat Jan 10 2026 mwprado <mwprado@github> - 1.0-43
- Estrutura de entrega via arquivo único (.tar.gz) para simular SRPM.
- Correção do erro 21 (É um diretório).
