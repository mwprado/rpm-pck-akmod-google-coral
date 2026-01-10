%global debug_package %{nil}
%global repo_name gasket-driver
%global commit      5815ee3908a46a415aac616ac7b9aedcb98a504c
%global shortcommit %(c=%{commit}; echo ${c:0:7})
%global snapshotdate 20260105

# 1. Definimos o nome do akmod com o sufixo kmod (Padrão NVIDIA)
%global akmod_name google-coral-kmod
%global src_dir_name google-coral

%{?akmod_global}

Name:           akmod-google-coral
Version:        1.0
Release:        21.%{snapshotdate}git%{shortcommit}%{?dist}
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

# 2. Metadados de compatibilidade NVIDIA-style
Provides:       akmod(%{akmod_name}) = %{version}-%{release}
Provides:       %{src_dir_name}-kmod-common = %{version}

%{?kmodtool_prefix}
%(kmodtool --target %{_target_cpu} --repo %{repo_name} --akmod %{akmod_name} %{?kernels:--kmp %{?kernels}} 2>/dev/null)

%description
Este pacote segue o padrão akmod-nvidia. 
Permite o uso do comando: akmods --akmod google-coral-kmod

%prep
%setup -q -n %{repo_name}-%{commit}
patch -p1 < %{SOURCE3}
patch -p1 < %{SOURCE4}

%build
# Build via akmods

%install
# 3. A pasta física mantém o nome simples para evitar caminhos redundantes
%global akmod_inst_dir %{_usrsrc}/akmods/%{src_dir_name}-%{version}-%{release}
mkdir -p %{buildroot}%{akmod_inst_dir}
cp -r src/* %{buildroot}%{akmod_inst_dir}/

# 4. O ARQUIVO .NM: O segredo do comando --akmod google-coral-kmod
# O nome do arquivo é o que você digita, o conteúdo é o nome da pasta em /usr/src/akmods/
mkdir -p %{buildroot}%{_sysconfdir}/akmods
echo "%{src_dir_name}-%{version}-%{release}" > %{buildroot}%{_sysconfdir}/akmods/%{akmod_name}.nm

# Arquivos de suporte
mkdir -p %{buildroot}%{_udevrulesdir}
install -p -m 0644 %{SOURCE1} %{buildroot}%{_udevrulesdir}/99-google-coral.rules
mkdir -p %{buildroot}%{_sysconfdir}/modules-load.d/
install -p -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/modules-load.d/google-coral.conf
mkdir -p %{buildroot}%{_sysusersdir}
install -p -m 0644 %{SOURCE5} %{buildroot}%{_sysusersdir}/google-coral.conf

%pre
%sysusers_create_package %{src_dir_name} %{SOURCE5}

%post
# Agora o gatilho usa o nome com -kmod
%{_sbindir}/akmods --force --akmod %{akmod_name} &>/dev/null || :
/usr/bin/udevadm control --reload-rules && /usr/bin/udevadm trigger || :

%files
%license LICENSE
%{akmod_inst_dir}
%{_sysconfdir}/akmods/%{akmod_name}.nm
%{_udevrulesdir}/99-google-coral.rules
%{_sysconfdir}/modules-load.d/google-coral.conf
%{_sysusersdir}/google-coral.conf

%changelog
* Sat Jan 10 2026 mwprado <mwprado@github> - 1.0-21
- Padronização completa com o sufixo -kmod (estilo NVIDIA).
- Arquivo .nm configurado para mapear google-coral-kmod para a pasta de fontes.
