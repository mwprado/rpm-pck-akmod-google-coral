%global debug_package %{nil}
%global repo_name gasket-driver
%global commit      5815ee3908a46a415aac616ac7b9aedcb98a504c
%global shortcommit %(c=%{commit}; echo ${c:0:7})
%global snapshotdate 20260105
%global akmod_name google-coral

# 1. Ativa a infraestrutura de akmods padrão Fedora/NVIDIA
%{?akmod_global}

Name:           akmod-google-coral
Version:        1.0
Release:        20.%{snapshotdate}git%{shortcommit}%{?dist}
Summary:        Akmod package for Google Coral Edge TPU
License:        GPLv2
URL:            https://github.com/google/%{repo_name}

Source0:        %{url}/archive/%{commit}/%{repo_name}-%{shortcommit}.tar.gz

%global raw_url https://raw.githubusercontent.com/mwprado/rpm-pck-akmod-google-coral/main
Source1:        %{raw_url}/99-google-coral.rules
Source2:        %{raw_url}/google-coral.conf
Source3:        %{raw_url}/fix-for-no_llseek.patch
Source4:        %{raw_url}/fix-for-module-import-ns.patch
Source5:        %{raw_url}/google-coral-group.conf

BuildRequires:  make gcc kernel-devel kmodtool systemd-devel systemd-rpm-macros
Requires:       akmods kmodtool

# 2. PROVIDES PADRÃO NVIDIA: Isto é o que o comando 'akmods --akmod google-coral' procura
Provides:       akmod(%{akmod_name}) = %{version}-%{release}

# 3. MACRO MÁGICA: Gera dinamicamente os metadados de subpacotes kmod
%{?kmodtool_prefix}
%(kmodtool --target %{_target_cpu} --repo %{repo_name} --akmod %{akmod_name} %{?kernels:--kmp %{?kernels}} 2>/dev/null)

%description
This package provides the akmod-google-coral kernel module.
It follows the Fedora akmod standard used by major drivers like NVIDIA.

%prep
%setup -q -n %{repo_name}-%{commit}
patch -p1 < %{SOURCE3}
patch -p1 < %{SOURCE4}

%build
# O build é disparado pelo kmodtool/akmods

%install
# 4. DIRETÓRIO DE FONTES: Deve ser idêntico ao akmod_name para evitar confusão
%global akmod_inst_dir %{_usrsrc}/akmods/%{akmod_name}-%{version}-%{release}
mkdir -p %{buildroot}%{akmod_inst_dir}
cp -r src/* %{buildroot}%{akmod_inst_dir}/

# 5. ARQUIVO .NM: O "mapa" de busca do akmods
mkdir -p %{buildroot}%{_sysconfdir}/akmods
echo "%{akmod_name}" > %{buildroot}%{_sysconfdir}/akmods/%{akmod_name}.nm

# Arquivos de suporte
mkdir -p %{buildroot}%{_udevrulesdir}
install -p -m 0644 %{SOURCE1} %{buildroot}%{_udevrulesdir}/99-google-coral.rules
mkdir -p %{buildroot}%{_sysconfdir}/modules-load.d/
install -p -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/modules-load.d/google-coral.conf
mkdir -p %{buildroot}%{_sysusersdir}
install -p -m 0644 %{SOURCE5} %{buildroot}%{_
