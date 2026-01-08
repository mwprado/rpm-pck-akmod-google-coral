%global debug_package %{nil}
%global repo_name gasket-driver
%global commit      5815ee3908a46a415aac616ac7b9aedcb98a504c
%global shortcommit %(c=%{commit}; echo ${c:0:7})
%global snapshotdate 20260105
%global akmod_name google-coral

# Nome padronizado conforme diretrizes do Fedora Akmod
Name:           akmod-%{akmod_name}
Version:        1.0
Release:        13.%{snapshotdate}git%{shortcommit}%{?dist}
Summary:        Akmod package for Google Coral Edge TPU (Gasket & Apex)
License:        GPLv2
URL:            https://github.com/google/%{repo_name}

Source0:        %{url}/archive/%{commit}/%{repo_name}-%{shortcommit}.tar.gz

# URLs Raw do seu GitHub para centralização
%global raw_url https://raw.githubusercontent.com/mwprado/rpm-pck-akmod-google-coral/main
Source1:        %{raw_url}/99-google-coral.rules
Source2:        %{raw_url}/google-coral.conf
Source3:        %{raw_url}/fix-for-no_llseek.patch
Source4:        %{raw_url}/fix-for-module-import-ns.patch
Source5:        %{raw_url}/google-coral-group.conf

BuildRequires:  make
BuildRequires:  gcc
BuildRequires:  kernel-devel
BuildRequires:  kmodtool
BuildRequires:  systemd-devel
BuildRequires:  systemd-rpm-macros

# O pacote akmod deve prover o kmod-common correspondente
Requires:       akmods
Requires:       kmodtool
Provides:       %{akmod_name}-kmod-common = %{version}
Requires:       %{akmod_name}-kmod-common = %{version}

%description
Pacote de fontes para o driver Gasket/Apex do Google Coral.
Padronizado para reconstrução automática via akmods.

%prep
%setup -q -n %{repo_name}-%{commit}
# Aplica os patches corretivos para kernels modernos (6.12+)
patch -p1 < %{SOURCE3}
patch -p1 < %{SOURCE4}

%build
# Processo de build vazio (compilação ocorre no host do usuário)

%install
# 1. Instalação dos fontes no diretório padrão do akmods
dest_dir=%{buildroot}%{_usrsrc}/akmods/%{akmod_name}-%{version}-%{release}
mkdir -p $dest_dir
cp -r src/* $dest_dir/

# 2. Regras de Udev
mkdir -p %{buildroot}%{_udevrulesdir}
install -p -m 0644 %{SOURCE1} %{buildroot}%{_udevrulesdir}/99-google-coral.rules

# 3. Módulos para carregar no boot (modules-load.d)
mkdir -p %{buildroot}%{_sysconfdir}/modules-load.d/
install -p -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/modules-load.d/google-coral.conf

# 4. Configuração de Grupo (sysusers.d) - Vital para Silverblue
mkdir -p %{buildroot}%{_sysusersdir}
install -p -m 0644 %{SOURCE5} %{buildroot}%{_sysusersdir}/google-coral.conf

%pre
%sysusers_create_package %{akmod_name} %{SOURCE5}

%post
/usr/bin/udevadm control --reload-rules && /usr/bin/udevadm trigger || :
# No Silverblue, este comando pode falhar se não houver kernel-devel, 
# mas o rpm-ostree lidará com isso no próximo deployment.
%{_sbindir}/akmods --force --akmod %{akmod_name} &>/dev/null || :

%files
%license LICENSE
%{_usrsrc}/akmods/%{akmod_name}-%{version}-%{release}
%{_udevrulesdir}/99-google-coral.rules
%{_sysconfdir}/modules-load.d/google-coral.conf
%{_sysusersdir}/google-coral.conf

%changelog
* Thu Jan 08 2026 mwprado <mwprado@github> - 1.0-12
- Nome alterado para akmod-google-coral seguindo padrões oficiais.
- Ajustes para compatibilidade com Fedora Silverblue e sysusers.d.
