%global debug_package %{nil}
%global repo_name gasket-driver
%global commit      5815ee3908a46a415aac616ac7b9aedcb98a504c
%global shortcommit %(c=%{commit}; echo ${c:0:7})
%global snapshotdate 20260105

# NOME DO AKMOD: O identificador que o comando akmods usa
%global akmod_name google-coral

Name:           akmod-google-coral
Version:        1.0
Release:        23.%{snapshotdate}git%{shortcommit}%{?dist}
Summary:        Akmod package for Google Coral Edge TPU
License:        GPLv2
URL:            https://github.com/google/%{repo_name}

Source0:        %{url}/archive/%{commit}/%{repo_name}-%{shortcommit}.tar.gz
Source1:        https://raw.githubusercontent.com/mwprado/rpm-pck-akmod-google-coral/main/99-google-coral.rules
Source2:        https://raw.githubusercontent.com/mwprado/rpm-pck-akmod-google-coral/main/google-coral.conf
Source3:        https://raw.githubusercontent.com/mwprado/rpm-pck-akmod-google-coral/main/fix-for-no_llseek.patch
Source4:        https://raw.githubusercontent.com/mwprado/rpm-pck-akmod-google-coral/main/fix-for-module-import-ns.patch
Source5:        https://raw.githubusercontent.com/mwprado/rpm-pck-akmod-google-coral/main/google-coral-group.conf

BuildRequires:  make gcc kernel-devel kmodtool systemd-devel systemd-rpm-macros
Requires:       akmods kmodtool

# 1. METADADOS NATIVOS: É isso que o akmods busca no banco de dados RPM
Provides:       akmod(%{akmod_name}) = %{version}-%{release}
Provides:       %{akmod_name}-kmod-common = %{version}

# 2. MACRO DE GERAÇÃO: Cria os subpacotes virtuais idêntico ao nvidia-kmod
%{?akmod_global}
%{?kmodtool_prefix}
%(kmodtool --target %{_target_cpu} --repo %{repo_name} --akmod %{akmod_name} %{?kernels:--kmp %{?kernels}} 2>/dev/null)

%description
Google Coral TPU driver in the native Fedora akmod format.
Optimized to work without .nm files, relying on RPM metadata.

%prep
%setup -q -n %{repo_name}-%{commit}
patch -p1 < %{SOURCE3}
patch -p1 < %{SOURCE4}

%build
# O build é disparado pelo akmods

%install
# 3. ESTRUTURA DE DIRETÓRIO NATIVA:
# O akmods busca por /usr/src/akmods/NOME-VERSÃO ou apenas NOME
%global akmod_inst_dir %{_usrsrc}/akmods/%{akmod_name}-%{version}
mkdir -p %{buildroot}%{akmod_inst_dir}
cp -r src/* %{buildroot}%{akmod_inst_dir}/

# NÃO criamos o arquivo .nm aqui para testar o modo nativo puro

# 4. ARQUIVOS DE SUPORTE
mkdir -p %{buildroot}%{_udevrulesdir}
install -p -m 0644 %{SOURCE1} %{buildroot}%{_udevrulesdir}/99-google-coral.rules

mkdir -p %{buildroot}%{_sysconfdir}/modules-load.d/
install -p -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/modules-load.d/google-coral.conf

mkdir -p %{buildroot}%{_sysusersdir}
install -p -m 0644 %{SOURCE5} %{buildroot}%{_sysusersdir}/google-coral.conf

%pre
%sysusers_create_package %{akmod_name} %{SOURCE5}

%post
# Gatilho automático
%{_sbindir}/akmods --force --akmod %{akmod_name} &>/dev/null || :
/usr/bin/udevadm control --reload-rules && /usr/bin/udevadm trigger || :

%files
%license LICENSE
%{akmod_inst_dir}
%{_udevrulesdir}/99-google-coral.rules
%{_sysconfdir}/modules-load.d/google-coral.conf
%{_sysusersdir}/google-coral.conf

%changelog
* Sat Jan 10 2026 mwprado <mwprado@github> - 1.0-23
- Remoção do arquivo .nm para uso do sistema de metadados nativo do kmodtool.
- Ajuste da pasta para o padrão nome-versão.
