%if 0%{?fedora}
%global buildforkernels akmod
%endif
%global debug_package %{nil}

%global akmod_name google-coral
%global kmodsrc_name google-coral-kmodsrc

Name:           google-coral-kmod
Version:        1.0
Release:        56%{?dist}
Summary:        Kernel module for Google Coral Edge TPU

License:        GPLv2
URL:            https://github.com/google/gasket-driver
Source1:        99-google-coral.rules
Source2:        google-coral.conf
Source5:        google-coral.conf

# --- DEFINIÇÃO DE BUILD REQUIRES (Padrão RPM Fusion) ---
%global AkmodsBuildRequires %{_bindir}/kmodtool, %{kmodsrc_name} = %{version}, gcc, make, kernel-devel, elfutils-libelf-devel
BuildRequires:  %{AkmodsBuildRequires}
BuildRequires:  systemd-devel
BuildRequires:  systemd-rpm-macros

# Invocação do kmodtool (Sem flags de repositório para evitar o erro de 'tag rhel')
%{?kmodtool_prefix}
%(kmodtool --target %{_target_cpu} --kmodname %{name} --akmod 2>/dev/null)

%description
Infrastructure for Google Coral Edge TPU kernel modules.
Strictly following the RPM Fusion kmodsrc + akmod pattern.

%package -n akmod-%{akmod_name}
Summary:        Akmod package for %{akmod_name} kernel module(s)
Requires:       akmods kmodtool
Requires:       %{kmodsrc_name} = %{version}
Provides:       akmod(%{akmod_name}) = %{version}-%{release}

%description -n akmod-%{akmod_name}
This package installs the infrastructure to build Google Coral modules.

%prep
# Removi o kmodtool_check para evitar que ele injete tags de RHEL problemáticas
%setup -q -T -c -n %{name}-%{version}

%build
# Vazio

%install
# Em vez de akmod_install (que pode estar injetando o erro do RHEL no seu repo),
# vamos fazer a instalação manual identica ao que a macro faria:
mkdir -p %{buildroot}%{_usrsrc}/akmods
# O kmodsrc instala o tarball em /usr/share. Nós linkamos para /usr/src/akmods
ln -s %{_datadir}/%{kmodsrc_name}-%{version}/google-coral-kmod-%{version}.tar.xz %{buildroot}%{_usrsrc}/akmods/%{akmod_name}.latest

# Arquivos de sistema
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
# O link simbólico para o latest
%{_usrsrc}/akmods/%{akmod_name}.latest
%{_udevrulesdir}/99-google-coral.rules
%{_sysconfdir}/modules-load.d/google-coral.conf
%{_sysusersdir}/google-coral.conf

%changelog
* Sun Jan 11 2026 mwprado <mwprado@github> - 1.0-56
- Version 56: Implemented the requested BuildRequires structure.
- Manual latest link creation to bypass RHEL tag errors in akmod_install.
