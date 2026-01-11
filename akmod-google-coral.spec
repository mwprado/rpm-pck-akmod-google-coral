# 1. Definições de controle (Padrão NVIDIA/VirtualBox)
%if 0%{?fedora}
%global buildforkernels akmod
%endif
%global debug_package %{nil}

# Define a macro de Build caso o ambiente (Copr) não a conheça
%{!?AkmodsBuildRequires: %global AkmodsBuildRequires gcc, make, kernel-devel, kmodtool, elfutils-libelf-devel}

%global akmod_name google-coral
%global repo_name gasket-driver
%global commit      5815ee3908a46a415aac616ac7b9aedcb98a504c
%global shortcommit %(c=%{commit}; echo ${c:0:7})

Name:           google-coral-kmod
Version:        1.0
Release:        44.git%{shortcommit}%{?dist}
Summary:        Módulos do kernel para Google Coral Edge TPU (Padrão RPM Fusion)

License:        GPLv2
URL:            https://github.com/google/%{repo_name}
Source0:        %{url}/archive/%{commit}/%{repo_name}-%{shortcommit}.tar.gz
Source1:        99-google-coral.rules
Source2:        google-coral.conf
Source3:        fix-for-no_llseek.patch
Source4:        fix-for-module-import-ns.patch
Source5:        google-coral-group.conf

# 2. Dependências de Build usando a macro oficial
BuildRequires:  %{AkmodsBuildRequires}
BuildRequires:  systemd-devel
BuildRequires:  systemd-rpm-macros

# 3. Invocação do kmodtool (O "Cérebro" do nvidia-kmod.spec)
# Esta macro gera os subpacotes binários dinamicamente
%{?kmodtool_prefix}
%(kmodtool --target %{_target_cpu} --repo %{repo_name} --akmod %{akmod_name} %{?kernels:--kmp %{?kernels}} 2>/dev/null)

%description
Pacote de infraestrutura para o driver Google Coral. 
Baseado nos padrões de empacotamento da NVIDIA e VirtualBox.

# --- SEÇÃO DO AKMOD (Fontes patcheados) ---
%package -n akmod-%{akmod_name}
Summary:        Akmod package for %{akmod_name} kernel module(s)
Requires:       akmods kmodtool
Provides:       akmod(%{akmod_name}) = %{version}-%{release}

%description -n akmod-%{akmod_name}
Este pacote contém os fontes do driver Coral com patches aplicados. 
O sistema akmods usará estes arquivos para compilar o driver para o seu kernel.

%prep
# Verifica o ambiente (Macro do VirtualBox)
%{?kmodtool_check}
%setup -q -n %{repo_name}-%{commit}

# Aplica os patches de compatibilidade com Kernel 6.12+
patch -p1 < %{SOURCE3}
patch -p1 < %{SOURCE4}

# Estrutura de build isolada por arquitetura (Padrão NVIDIA)
mkdir -p _kmod_build_%{_target_cpu}
cp -r src/* _kmod_build_%{_target_cpu}/

%build
# Vazio para akmods (a compilação ocorre no cliente)

%install
# 1. Instalação dos fontes para o akmod em /usr/src/akmods/
%global inst_dir %{_usrsrc}/akmods/%{akmod_name}-%{version}-%{release}
mkdir -p %{buildroot}%{inst_dir}
cp -r _kmod_build_%{_target_cpu}/* %{buildroot}%{inst_dir}/

# 2. Arquivo de controle .nm (Fundamental para o Silverblue)
mkdir -p %{buildroot}%{_sysconfdir}/akmods
echo "%{akmod_name}" > %{buildroot}%{_sysconfdir}/akmods/%{akmod_name}.nm

# 3. Configurações de sistema (Udev, Modules-load, Groups)
mkdir -p %{buildroot}%{_udevrulesdir}
install -p -m 0644 %{SOURCE1} %{buildroot}%{_udevrulesdir}/99-google-coral.rules

mkdir -p %{buildroot}%{_sysconfdir}/modules-load.d
install -p -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/modules-load.d/google-coral.conf

mkdir -p %{buildroot}%{_sysusersdir}
install -p -m 0644 %{SOURCE5} %{buildroot}%{_sysusersdir}/google-coral.conf

%pre -n akmod-%{akmod_name}
%sysusers_create_package %{akmod_name} %{SOURCE5}

%post -n akmod-%{akmod_name}
# Força o akmods a tentar compilar logo após a instalação
%{_sbindir}/akmods --force --akmod %{akmod_name} &>/dev/null || :

%files -n akmod-%{akmod_name}
%license LICENSE
%{inst_dir}
%{_sysconfdir}/akmods/%{akmod_name}.nm
%{_udevrulesdir}/99-google-coral.rules
%{_sysconfdir}/modules-load.d/google-coral.conf
%{_sysusersdir}/google-coral.conf

%changelog
* Sun Jan 11 2026 mwprado <mwprado@github> - 1.0-44
- Versão 44: Sincronização total com specs NVIDIA/VirtualBox.
- Definição explícita de AkmodsBuildRequires para compatibilidade com Copr.
- Uso de diretório de build por arquitetura.
