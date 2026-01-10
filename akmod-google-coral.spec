%global debug_package %{nil}
%global repo_name gasket-driver
%global commit      5815ee3908a46a415aac616ac7b9aedcb98a504c
%global shortcommit %(c=%{commit}; echo ${c:0:7})
%global snapshotdate 20260105
%global akmod_name google-coral

# Macro que define este pacote como um Akmod oficial do Fedora
%{?akmod_global}

Name:           akmod-google-coral
Version:        1.0
Release:        16.%{snapshotdate}git%{shortcommit}%{?dist}
Summary:        Akmod package for Google Coral Edge TPU
License:        GPLv2
URL:            https://github.com/google/%{repo_name}

Source0:        %{url}/archive/%{commit}/%{repo_name}-%{shortcommit}.tar.gz

%global raw_url https://raw.githubusercontent.com/mwprado/rpm-pck-google-coral-akmod/main
Source1:        %{raw_url}/99-google-coral.rules
Source2:        %{raw_url}/google-coral.conf
Source3:        %{raw_url}/fix-for-no_llseek.patch
Source4:        %{raw_url}/fix-for-module-import-ns.patch
Source5:        %{raw_url}/google-coral-group.conf

BuildRequires:  make gcc kernel-devel kmodtool systemd-devel systemd-rpm-macros
Requires:       akmods kmodtool

# Metadados vitais para o utilitário 'akmods' no Silverblue
Provides:       akmod(%{akmod_name}) = %{version}-%{release}
Provides:       %{akmod_name}-kmod-common = %{version}

%description
Fontes patcheados para o driver Gasket/Apex do Google Coral.
Projetado para compilação automática em sistemas Fedora e Silverblue.

%prep
%setup -q -n %{repo_name}-%{commit}
# Aplica patches antes de mover para a pasta definitiva
patch -p1 < %{SOURCE3}
patch -p1 < %{SOURCE4}

%build
# O build do módulo ocorre no cliente via akmods

%install
# Define o diretório de destino EXATAMENTE como o akmods espera encontrar
%global akmod_inst_dir %{_usrsrc}/akmods/%{akmod_name}-%{version}-%{release}
mkdir -p %{buildroot}%{akmod_inst_dir}

# Copia os fontes já patcheados para o diretório de destino
cp -r src/* %{buildroot}%{akmod_inst_dir}/

# Cria o arquivo de mapeamento .nm necessário para o Silverblue reconhecer o nome
mkdir -p %{buildroot}%{_sysconfdir}/akmods
echo "%{akmod_name}" > %{buildroot}%{_sysconfdir}/akmods/%{akmod_name}.nm

# Arquivos de suporte (Udev, Modules-load, Sysusers)
mkdir -p %{buildroot}%{_udevrulesdir}
install -p -m 0644 %{SOURCE1} %{buildroot}%{_udevrulesdir}/99-google-coral.rules

mkdir -p %{buildroot}%{_sysconfdir}/modules-load.d/
install -p -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/modules-load.d/google-coral.conf

mkdir -p %{buildroot}%{_sysusersdir}
install -p -m 0644 %{SOURCE5} %{buildroot}%{_sysusersdir}/google-coral.conf

%pre
%sysusers_create_package %{akmod_name} %{SOURCE5}

%post
# Tenta disparar a compilação imediatamente
/usr/sbin/akmods --force --akmod %{akmod_name} &>/dev/null || :
/usr/bin/udevadm control --reload-rules && /usr/bin/udevadm trigger || :

%files
%license LICENSE
%{akmod_inst_dir}
%{_sysconfdir}/akmods/%{akmod_name}.nm
%{_udevrulesdir}/99-google-coral.rules
%{_sysconfdir}/modules-load.d/google-coral.conf
%{_sysusersdir}/google-coral.conf

%changelog
* Sat Jan 10 2026 mwprado <mwprado@github> - 1.0-16
- Correção definitiva dos metadados Provides akmod() para reconhecimento no Silverblue.
- Garantia de que o Makefile está na raiz de /usr/src/akmods/google-coral-*.
- Adição do arquivo .nm na seção %files.
