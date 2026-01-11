%if 0%{?fedora}
%global buildforkernels akmod
%endif
%global debug_package %{nil}

%global akmod_name google-coral
%global repo_name  google-coral-kmod

Name:           google-coral-kmod
Version:        1.0
Release:        49%{?dist}
Summary:        Kernel module for Google Coral Edge TPU

License:        GPLv2
URL:            https://github.com/google/gasket-driver
Source1:        99-google-coral.rules
Source2:        google-coral.conf
Source5:        google-coral-group.conf

# Padrão RPM Fusion: O BuildRequires busca o arquivo no sistema
BuildRequires:  %{_bindir}/kmodtool, gcc, make, kernel-devel, elfutils-libelf-devel
BuildRequires:  systemd-devel
# Exige os fontes para a macro akmod_install funcionar
BuildRequires:  google-coral-kmodsrc = %{version}

%{?kmodtool_prefix}
%(kmodtool --target %{_target_cpu} --repo rpmfusion --kmodname %{name} %{?buildforkernels:--%{buildforkernels}} %{?kernels:--for-kernels "%{?kernels}"} 2>/dev/null)

%description
Package to manage Google Coral Edge TPU kernel modules.

%package -n akmod-%{akmod_name}
Summary:        Akmod package for %{akmod_name} kernel module(s)
Requires:       akmods kmodtool
Requires:       google-coral-kmodsrc = %{version}
Provides:       akmod(%{akmod_name}) = %{version}-%{release}

%description -n akmod-%{akmod_name}
This package installs the infrastructure to build Google Coral modules.

%prep
%{?kmodtool_check}
# O prep aqui é mínimo, pois os fontes vêm do kmodsrc já instalados no sistema
mkdir -p %{_builddir}/%{name}-%{version}

%build
# Vazio

%install
# A macro akmod_install do RPM Fusion busca o tarball em /usr/share/%{name}-%{version}/
# que foi instalado pelo pacote kmodsrc.
%{?akmod_install}

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
%{_udevrulesdir}/99-google-coral.rules
%{_sysconfdir}/modules-load.d/google-coral.conf
%{_sysusersdir}/google-coral.conf

%changelog
* Sun Jan 11 2026 mwprado <mwprado@github> - 1.0-49
- Separated akmod from kmodsrc to match RPM Fusion official pattern.
- Relies on kmodsrc for source tarball.
