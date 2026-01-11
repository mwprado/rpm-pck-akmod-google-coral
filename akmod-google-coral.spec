# 1. Flag de controle padrão RPM Fusion
%if 0%{?fedora}
%global buildforkernels akmod
%endif
%global debug_package %{nil}

%global akmod_name google-coral
%global repo_name gasket-driver
%global commit      5815ee3908a46a415aac616ac7b9aedcb98a504c

Name:           google-coral-kmod
Version:        1.0
Release:        28%{?dist}
Summary:        Módulos do kernel para Google Coral Edge TPU (Padrão VirtualBox)
License:        GPLv2
URL:            https://github.com/google/%{repo_name}

Source0:        %{url}/archive/%{commit}/%{repo_name}-5815ee3.tar.gz
Source1:        99-google-coral.rules
Source2:        google-coral.conf
Source3:        fix-for-no_llseek.patch
Source4:        fix-for-module-import-ns.patch
Source5:        google-coral-group.conf

# 2. Dependências de Build usando as macros oficiais do VirtualBox/Nvidia
BuildRequires:  %{AkmodsBuildRequires}
BuildRequires:  systemd-devel
BuildRequires:  systemd-rpm-macros

# 3. O "Cérebro": Invocação do kmodtool para gerar subpacotes dinâmicos
%{?kmodtool_prefix}
%(kmodtool --target %{_target_cpu} --repo %{repo_name} --akmod %{akmod_name} %{?kernels:--kmp %{?kernels}} 2>/dev/null)

%description
Metapacote para o driver Google Coral. Segue o padrão de infraestrutura
utilizado pelo VirtualBox e NVIDIA no Fedora.

# --- Seção do AKMOD (Onde ficam os fontes) ---
%package -n akmod-%{akmod_name}
Summary:        Akmod package for %{akmod_name} kernel module(s)
Requires:       akmods kmodtool
Provides:       akmod(%{akmod_name}) = %{version}-%{release}

%description -n akmod-%{akmod_name}
Este pacote contém o código-fonte patcheado para o akmods construir o driver Coral.

%prep
# Verifica se o ambiente de kernel está pronto (Macro do VirtualBox)
%{?kmodtool_check}
%setup -q -n %{repo_name}-%{commit}

# Aplica patches de compatibilidade
patch -p1 < %{SOURCE3}
patch -p1 < %{SOURCE4}

# Prepara a pasta de build isolada por arquitetura (Padrão NVIDIA)
mkdir -p _kmod_build_%{_target_cpu}
cp -r src/* _kmod_build_%{_target_cpu}/

%build
# Vazio: o build real acontece no computador do usuário

%install
# 1. Instalação dos fontes para o akmod
%global inst_dir %{_usrsrc}/akmods/%{akmod_name}-%{version}-%{release}
mkdir -p %{buildroot}%{inst_dir}
cp -r _kmod_build_%{_target_cpu}/* %{buildroot}%{inst_dir}/

# 2. Arquivo .nm (Essencial para o comando 'akmods' no Silverblue)
mkdir -p %{buildroot}%{_sysconfdir}/akmods
echo "%{akmod_name}" > %{buildroot}%{_sysconfdir}/akmods/%{akmod_name}.nm

# 3. Regras de sistema e grupos
mkdir -p %{buildroot}%{_udevrulesdir}
install -p -m 0644 %{SOURCE1} %{buildroot}%{_udevrulesdir}/99-google-coral.rules
mkdir -p %{buildroot}%{_sysconfdir}/modules-load.d
install -p -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/modules-load.d/google-coral.conf
mkdir -p %{buildroot}%{_sysusersdir}
install -p -m 0644 %{SOURCE5} %{buildroot}%{_sysusersdir}/google-coral.conf

%pre -n akmod-%{akmod_name}
%sysusers_create_package %{akmod_name} %{SOURCE5}

%post -n akmod-%{akmod_name}
# O gatilho que o VirtualBox usa para tentar compilar no momento da instalação
%{_sbindir}/akmods --force --akmod %{akmod_name} &>/dev/null || :

%files -n akmod-%{akmod_name}
%license LICENSE
%{inst_dir}
%{_sysconfdir}/akmods/%{akmod_name}.nm
%{_udevrulesdir}/99-google-coral.rules
%{_sysconfdir}/modules-load.d/google-coral.conf
%{_sysusersdir}/google-coral.conf

%changelog
* Sun Jan 11 2026 mwprado <mwprado@github> - 1.0-28
- Implementação completa baseada no padrão NVIDIA e VirtualBox.
- Uso de macros dinâmicas kmodtool e AkmodsBuildRequires.
