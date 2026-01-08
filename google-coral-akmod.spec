%global debug_package %{nil}
%global repo_name gasket-driver
%global commit      5815ee3908a46a415aac616ac7b9aedcb98a504c
%global shortcommit %(c=%{commit}; echo ${c:0:7})
%global snapshotdate 20260105
%global akmod_name google-coral

Name:           google-coral-akmod
Version:        1.0
Release:        8.%{snapshotdate}git%{shortcommit}%{?dist}
Summary:        Akmod package for Google Coral Edge TPU (Gasket & Apex)
License:        GPLv2
URL:            https://github.com/google/%{repo_name}

Source0:        %{url}/archive/%{commit}/%{repo_name}-%{shortcommit}.tar.gz

# Referências Raw do seu GitHub para garantir consistência
%global raw_url https://raw.githubusercontent.com/mwprado/rpm-pck-google-coral-akmod/main
Source1:        %{raw_url}/99-google-coral.rules
Source2:        %{raw_url}/google-coral.conf
Source3:        %{raw_url}/fix-for-no_llseek.patch
Source4:        %{raw_url}/fix-for-module-import-ns.patch

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
Este pacote fornece o código fonte (já patcheado para kernels modernos) para 
o akmod gerar os drivers gasket e apex para o Google Coral.

%prep
# 1. Extrai o código do Google 
%setup -q -n %{repo_name}-%{commit}

# 2. Aplica os patches DIRETAMENTE no código antes do empacotamento 
# Isso garante que os arquivos em 'src/' que serão copiados no %install já estejam corrigidos
patch -p1 < %{SOURCE3}
patch -p1 < %{SOURCE4}

%build
# Nada a fazer aqui

%install
# 1. Instalar fontes para o akmod (Agora contendo os arquivos já alterados pelos patches)
dest_dir=%{buildroot}%{_usrsrc}/akmods/%{akmod_name}-%{version}-%{release}
mkdir -p $dest_dir
cp -r src/* $dest_dir/

# 2. Instalar udev e configs de módulos [cite: 2]
mkdir -p %{buildroot}%{_udevrulesdir}
install -p -m 0644 %{SOURCE1} %{buildroot}%{_udevrulesdir}/99-google-coral.rules

mkdir -p %{buildroot}%{_sysconfdir}/modules-load.d/
install -p -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/modules-load.d/google-coral.conf

%pre
getent group coral >/dev/null || groupadd -r coral [cite: 5]
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
* Wed Jan 07 2026 mwprado <mwprado@github> - 1.0-8
- Garantido que o código fonte seja patcheado antes da cópia para o diretório akmod.
