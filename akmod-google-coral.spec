%global debug_package %{nil}
%global repo_name gasket-driver
%global commit      5815ee3908a46a415aac616ac7b9aedcb98a504c
%global shortcommit %(c=%{commit}; echo ${c:0:7})
%global snapshotdate 20260105
%global akmod_name google-coral

# 1. Macro essencial para ativar a infraestrutura akmod
%{?akmod_global}

Name:           akmod-google-coral
Version:        1.0
Release:        19.%{snapshotdate}git%{shortcommit}%{?dist}
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

# BuildRequires confirmados pela sua compilação manual bem-sucedida
BuildRequires:  make gcc kernel-devel kmodtool systemd-devel systemd-rpm-macros
Requires:       akmods kmodtool

# 2. Conexão com o kmodtool para gerar metadados de automação
Provides:       akmod(%{akmod_name}) = %{version}-%{release}
Provides:       %{akmod_name}-kmod-common = %{version}
%{?kmodtool_prefix}
%(kmodtool --target %{_target_cpu} --repo %{repo_name} --akmod %{akmod_name} %{?kernels:--kmp %{?kernels}} 2>/dev/null)

%description
Este pacote fornece o mecanismo akmod para o driver Google Coral (Gasket/Apex).
A versão 19 inclui macros kmodtool para automação total no Fedora Silverblue.

%prep
%setup -q -n %{repo_name}-%{commit}
# Aplicação dos patches para compatibilidade com Kernel moderno
patch -p1 < %{SOURCE3}
patch -p1 < %{SOURCE4}

%build
# Processado pelo akmods no cliente

%install
# Define o diretório exato esperado pelo utilitário akmods
%global akmod_inst_dir %{_usrsrc}/akmods/%{akmod_name}-%{version}-%{release}
mkdir -p %{buildroot}%{akmod_inst_dir}

# Copia o conteúdo de src para a raiz do diretório akmod
cp -r src/* %{buildroot}%{akmod_inst_dir}/

# Instala o arquivo de controle .nm (Vital para o comando 'akmods' no Silverblue)
mkdir -p %{buildroot}%{_sysconfdir}/akmods
echo "%{akmod_name}" > %{buildroot}%{_sysconfdir}/akmods/%{akmod_name}.nm

# Arquivos de suporte do sistema
mkdir -p %{buildroot}%{_udevrulesdir}
install -p -m 0644 %{SOURCE1} %{buildroot}%{_udevrulesdir}/99-google-coral.rules

mkdir -p %{buildroot}%{_sysconfdir}/modules-load.d/
install -p -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/modules-load.d/google-coral.conf

mkdir -p %{buildroot}%{_sysusersdir}
install -p -m 0644 %{SOURCE5} %{buildroot}%{_sysusersdir}/google-coral.conf

%pre
%sysusers_create_package %{akmod_name} %{SOURCE5}

%post
# Tenta o build imediato. Se falhar, o .nm e o kmodtool garantem o build no boot.
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
* Sat Jan 10 2026 mwprado <mwprado@github> - 1.0-19
- Inclusão da macro kmodtool para automação de subpacotes kmod.
- Confirmada dependência systemd-devel para compilação local.
- Estrutura de diretórios consolidada.
