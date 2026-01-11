%if 0%{?fedora}
%global buildforkernels akmod
%endif
%global with_rhel_kabi %{nil}
%global debug_package %{nil}

# Definimos apenas para uso interno, mas não confiaremos nelas para os nomes das seções
%global kmodsrc_name google-coral-kmodsrc

Name:           google-coral-kmod
Version:        1.0
Release:        68%{?dist}
Summary:        Kernel module for Google Coral Edge TPU
License:        GPLv2
URL:            https://github.com/google/gasket-driver

Source1:        99-google-coral.rules
Source2:        google-coral.conf
Source5:        google-coral-group.conf

# 1. BuildRequires (Estrutura idêntica à do VirtualBox)
%global AkmodsBuildRequires %{_bindir}/kmodtool, %{kmodsrc_name} = %{version}, xz, time, gcc, make, kernel-devel, elfutils-libelf-devel, systemd-devel, systemd-rpm-macros
BuildRequires:  %{AkmodsBuildRequires}

# 2. Invocação do kmodtool (Define macros para o akmod_install)
%{?kmodtool_prefix}
%(kmodtool --target %{_target_cpu} --repo rpmfusion --kmodname %{name} %{?buildforkernels:--%{buildforkernels}} %{?kernels:--for-kernels "%{?kernels}"} 2>/dev/null)

%description
Package to manage Google Coral Edge TPU kernel modules.

# 3. Definição DIRETA do pacote (Sem macros no nome para o rpkg não engasgar)
%package -n akmod-google-coral
Summary:        Akmod package for google-coral kernel module(s)
Requires:       akmods kmodtool
Requires:       %{kmodsrc_name} = %{version}
Provides:       akmod(google-coral) = %{version}-%{release}

%description -n akmod-google-coral
This package installs the infrastructure to build Google Coral modules.

%prep
%{?kmodtool_check}
%setup -q -T -c -n %{name}-%{version}

%build
# Vazio

%install
# A macro akmod_install cria o link .latest em /usr/src/akmods/
%{?akmod_install}

mkdir -p %{buildroot}%{_udevrulesdir}
install -p -m 0644 %{SOURCE1} %{buildroot}%{_udevrulesdir}/99-google-coral.rules
mkdir -p %{buildroot}%{_sysconfdir}/modules-load.d
install -p -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/modules-load.d/google-coral.conf
mkdir -p %{buildroot}%{_sysusersdir}
install -p -m 0644 %{SOURCE5} %{buildroot}%{_sysusersdir}/google-coral.conf

# 4. Scripts com nome DIRETO (akmod-google-coral)
%pre -n akmod-google-coral
%sysusers_create_package google-coral %{SOURCE5}

%post -n akmod-google-coral
%{_sbindir}/akmods --force --akmod google-coral &>/dev/null || :

%files -n akmod-google-coral
%{_udevrulesdir}/99-google-coral.rules
%{_sysconfdir}/modules-load.d/google-coral.conf
%{_sysusersdir}/google-coral.conf

%changelog
* Sun Jan 11 2026 mwprado <mwprado@github> - 1.0-68
- Version 68: Hardcoded package names to bypass Copr/rpkg static parsing errors.
- Matches NVIDIA's internal structure for broad compatibility.
