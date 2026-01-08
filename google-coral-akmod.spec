%global debug_package %{nil}
%global repo_name gasket-driver
%global commit      5815ee3908a46a415aac616ac7b9aedcb98a504c
%global shortcommit %(c=%{commit}; echo ${c:0:7})
%global snapshotdate 20260105
%global akmod_name google-coral

Name:           google-coral-akmod
Version:        1.0
Release:        9.%{snapshotdate}git%{shortcommit}%{?dist}
Summary:        Akmod package for Google Coral Edge TPU (Gasket & Apex)
License:        GPLv2
URL:            https://github.com/google/%{repo_name}

Source0:        %{url}/archive/%{commit}/%{repo_name}-%{shortcommit}.tar.gz

# Referências Raw do seu GitHub
%global raw_url https://raw.githubusercontent.com/mwprado/rpm-pck-google-coral-akmod/main
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
# Necessário para processar o arquivo de grupo durante o build
BuildRequires:  systemd-rpm-macros
Requires:       akmods
Requires:       kmodtool

Provides:       %{akmod_name}-kmod-common = %{version}
Requires:       %{akmod_name}-kmod-common = %{version}

%description
Este pacote fornece o código fonte patcheado para o akmod gerar os drivers 
gasket e apex para o Google Coral. Inclui automação para criação de grupo 
e regras de permissão.

%prep
%setup -q -n %{repo_name}-%{commit}
# Aplica os patches antes de mover para a pasta final [cite: 4]
patch -p1 < %{SOURCE3}
patch -p1 < %{SOURCE4}

%build
# Nada a fazer

%install
# 1. Instalar fontes para o akmod
dest_dir=%{buildroot}%{_usrsrc}/akmods/%{akmod_name}-%{version}-%{release}
mkdir -p $dest_dir
cp -r src/* $dest_dir/ [cite: 2]

# 2. Instalar udev rules
mkdir -p %{buildroot}%{_udevrulesdir}
install -p -m 0644 %{SOURCE1} %{buildroot}%{_udevrulesdir}/99-google-coral.rules

# 3. Instalar modules-load
mkdir -p %{buildroot}%{_sysconfdir}/modules-load.d/
install -p -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/modules-load.d/google-coral.conf [cite: 2]

# 4. Instalar sysusers.d para criação do grupo 'coral'
mkdir -p %{buildroot}%{_sysusersdir}
install -p -m 0644 %{SOURCE5} %{buildroot}%{_sysusersdir}/google-coral.conf

%pre
# O systemd-sysusers cuida disso agora, mas mantemos o gatilho de macro 
%sysusers_create_package google-coral %{SOURCE5}

%post
/usr/bin/udevadm control --reload-rules && /usr/bin/udevadm trigger || :
%{_sbindir}/akmods --force --akmod %{akmod_name} &>/dev/null || : [cite: 6]

%files
%license LICENSE
%{_usrsrc}/akmods/%{akmod_name}-%{version}-%{release}
%{_udevrulesdir}/99-google-coral.rules
%{_sysconfdir}/modules-load.d/google-coral.conf
%{_sysusersdir}/google-coral.conf

%changelog
* Wed Jan 07 2026 mwprado <mwprado@github> - 1.0-9
- Migrada criação de grupo para sysusers.d (Source5)[cite: 7].
- Mantida lógica de aplicação de patches no %prep[cite: 4].
