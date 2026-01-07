%global debug_package %{nil}
%global repo_name gasket-driver
%global commit      5815ee3908a46a415aac616ac7b9aedcb98a504c
%global shortcommit %(c=%{commit}; echo ${c:0:7})
%global snapshotdate 20260105

Name:           akmod-google-coral
Version:        1.0
Release:        2.%{snapshotdate}git%{shortcommit}%{?dist}
Summary:        Akmod package for Google Coral Edge TPU (Gasket & Apex)
License:        GPLv2
URL:            https://github.com/google/%{repo_name}

# Source0: Código do Google
Source0:        %{url}/archive/%{commit}/%{repo_name}-%{shortcommit}.tar.gz
# Source1: Seu arquivo local no GitHub
Source1:        99-google-coral.rules

BuildRequires:  make
BuildRequires:  gcc
BuildRequires:  kernel-devel
BuildRequires:  kmodtool
BuildRequires:  systemd-devel
Requires:       akmods
#Requires:       (kmod-google-coral if kernel)
Requires(pre):  shadow-utils

%{!?kernels: %{?kmodtool_kernels}}

%description
Este pacote fornece o driver Gasket/Apex para hardware Google Coral 
via akmod, garantindo suporte persistente em atualizacoes de kernel no Fedora.

%package -n kmod-google-coral
Summary:        Modulo de kernel para Google Coral
Provides:       kmod-google-coral = %{version}-%{release}
Provides:       google-coral-kmod = %{version}-%{release}

%description -n kmod-google-coral
Modulo de kernel compilado para o Google Coral Edge TPU.

%prep
%setup -q -n %{repo_name}-%{commit}

%build
# Preparado para akmod

%install
# 1. Instalar fontes para o akmod
dest_dir=%{buildroot}%{_usrsrc}/akmods/google-coral-%{version}-%{release}
mkdir -p $dest_dir
cp -r src/* $dest_dir/
#cp Makefile $dest_dir/

# 2. Instalar regras de udev (Source1)
mkdir -p %{buildroot}%{_udevrulesdir}
install -p -m 0644 %{SOURCE1} %{buildroot}%{_udevrulesdir}/

# 3. Configuração do akmod
mkdir -p %{buildroot}%{_sysconfdir}/akmods/
echo 'MODULE_NAME="gasket apex"' > %{buildroot}%{_sysconfdir}/akmods/google-coral.conf

%pre
getent group coral >/dev/null || groupadd -r coral
exit 0

%post
/usr/bin/udevadm control --reload-rules && /usr/bin/udevadm trigger || :

%files
%license LICENSE
%{_usrsrc}/akmods/google-coral-%{version}-%{release}
%{_udevrulesdir}/99-google-coral.rules
%{_sysconfdir}/akmods/google-coral.conf

%changelog
* Mon Jan 05 2026 O Teu Nome <teu@email.com> - 1.0-1.20260105git16a8b13
- Versao inicial com akmod e regras de udev integradas.
