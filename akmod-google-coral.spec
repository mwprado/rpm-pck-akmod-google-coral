# 1. Configurações de controle de build
%if 0%{?fedora}
%global buildforkernels akmod
%endif
%global debug_package %{nil}

# Definição manual da macro caso o sistema não a tenha (Padrão NVIDIA)
%{!?AkmodsBuildRequires: %global AkmodsBuildRequires gcc, make, kernel-devel, kmodtool, elfutils-libelf-devel}

%global akmod_name google-coral
%global repo_name gasket-driver
%global commit      5815ee3908a46a415aac616ac7b9aedcb98a504c

Name:           google-coral-kmod
Version:        1.0
Release:        29%{?dist}
Summary:        Módulos do kernel para Google Coral Edge TPU
License:        GPLv2
URL:            https://github.com/google/%{repo_name}

Source0:        %{url}/archive/%{commit}/%{repo_name}-5815ee3.tar.gz
Source1:        99-google-coral.rules
Source2:        google-coral.conf
Source3:        fix-for-no_llseek.patch
Source4:        fix-for-module-import-ns.patch
Source5:        google-coral-group.conf

# 2. Dependências de Build
BuildRequires:  %{AkmodsBuildRequires}
BuildRequires:  systemd-devel
BuildRequires:  systemd-rpm-macros

# 3. Invocação do kmodtool (O "Cérebro" dos specs que você enviou)
%{?kmodtool_prefix}
%(kmodtool --target %{_target_cpu} --repo %{repo_name} --akmod %{akmod_name} %{?kernels:--kmp %{?kernels}} 2>/dev/null)

%description
Pacote de driver para Google Coral seguindo o padrão NVIDIA/VirtualBox.

%package -n akmod-%{akmod_name}
Summary:        Akmod package for %{akmod_name} kernel module(s)
Requires:       akmods kmodtool
Provides:       akmod(%{akmod_name}) = %{version}-%{release}

%description -n akmod-%{akmod_name}
Código-fonte patcheado para compilação via akmods.

%prep
%{?kmodtool_check}
%setup -q -n %{repo_name}-%{commit}

# Aplica patches
patch -p1 < %{SOURCE3}
patch -p1 < %{SOURCE4}

# Estrutura de build isolada
mkdir -p _kmod_build_%{_target_cpu}
cp -r src/* _kmod_build_%{_target_cpu}/

%build
# Vazio para akmods

%install
%global inst_dir %{_usrsrc}/akmods/%{akmod_name}-%{version}-%{release}
mkdir -p %{buildroot}%{inst_dir}
cp -r _kmod_build_%{_target_cpu}/* %{buildroot}%{inst_dir}/

# Arquivos de controle
mkdir -p %{buildroot}%{_sysconfdir}/akmods
echo "%{akmod_name}" > %{buildroot}%{_sysconfdir}/akmods/%{akmod_name}.nm

# Configurações de sistema
mkdir -p %{buildroot}%{_udevrulesdir}
install -p -m 0644 %{SOURCE1} %{buildroot}%{_udevrulesdir}/99-google-coral.rules
mkdir -p %{buildroot}%{_sysconfdir}/modules-load.d
install -p -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/modules-load.d/google-coral.conf
mkdir -p %{buildroot}%{_sysusersdir}
install -p -m 0644 %{SOURCE5} %{buildroot}%{_sysusersdir}/google-coral.conf

%pre -n akmod-%{akmod_name}
%sysusers_create_package %{akmod_name} %{SOURCE5}

%post -n akmod-%{akmod_name}
%{_sbindir}/akmods --force --akmod %{akmod_name} &>/dev/null || :

%files -n akmod-%{akmod_name}
%license LICENSE
%{inst_dir}
%{_sysconfdir}/akmods/%{akmod_name}.nm
%{_udevrulesdir}/99-google-coral.rules
%{_sysconfdir}/modules-load.d/google-coral.conf
%{_sysusersdir}/google-coral.conf
