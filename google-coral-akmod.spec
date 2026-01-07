%global debug_package %{nil}
%global repo_name gasket-driver
%global commit      16a8b13c19e5d429813589b27568194f6c44247d
%global shortcommit %(c=%{commit}; echo ${c:0:7})
%global snapshotdate 20260105
%global akmod_name google-coral

Name:           google-coral-akmod
Version:        1.0
Release:        3.%{snapshotdate}git%{shortcommit}%{?dist}
Summary:        Akmod package for Google Coral Edge TPU (Gasket & Apex)
License:        GPLv2
URL:            https://github.com/google/%{repo_name}

Source0:        %{url}/archive/%{commit}/%{repo_name}-%{shortcommit}.tar.gz
Source1:        99-google-coral.rules
Source2:        google-coral.conf

BuildRequires:  make
BuildRequires:  gcc
BuildRequires:  kernel-devel
BuildRequires:  kmodtool
BuildRequires:  systemd-devel
Requires:       akmods
Requires:       kmodtool
Requires(pre):  shadow-utils

Provides:       %{akmod_name}-kmod-common = %{version}
Requires:       %{akmod_name}-kmod-common = %{version}

%description
Este pacote fornece o código fonte para o akmod gerar os drivers gasket e apex 
para o Google Coral. Configurações de udev e carregamento de módulos inclusas.

%prep
%setup -q -n %{repo_name}-%{commit}

%build
# Preparado para o runtime do akmod

%install
# 1. Instalar fontes para o akmod
dest_dir=%{buildroot}%{_usrsrc}/akmods/%{akmod_name}-%{version}-%{release}
mkdir -p $dest_dir
cp -r src/* $dest_dir/

# 2. Instalar regras de udev (Source1)
mkdir -p %{buildroot}%{_udevrulesdir}
install -p -m 0644 %{SOURCE1} %{buildroot}%{_udevrulesdir}/

# 3. Instalar configuração de carregamento de módulos (Source2)
mkdir -p %{buildroot}%{_sysconfdir}/modules-load.d/
install -p -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/modules-load.d/

%pre
getent group coral >/dev/null || groupadd -r coral
exit 0

%post
/usr/bin/udevadm control --reload-rules && /usr/bin/udevadm trigger || :
%{_sbindir}/akmods --force --akmod %{akmod_name} &>/dev/null || :

%files
%license LICENSE
%{_usrsrc}/akmods/%{akmod_name}-%{version}-%{release}
%{_udevrulesdir}/99-google-coral.rules
%{_sysconfdir}/modules-load.d/google-coral.conf

%changelog
* Tue Jan 06 2026 mwprado <mwprado@github> - 1.0-3.20260105git16a8b13
- Removida cópia redundante do Makefile.
- Movida configuração de módulos para arquivo externo (Source2).
