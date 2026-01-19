%define buildforkernels akmod
%global debug_package %{nil}

Name:           google-coral-kmod
Version:        1.0
Release:        1%{?dist}
Summary:        Kernel module for Google Coral Edge TPU
License:        GPLv2

BuildRequires:  sharutils
%define AkmodsBuildRequires sharutils
BuildRequires:  %{_bindir}/kmodtool
BuildRequires:  google-coral-kmodsrc = %{version}

%{expand:%(kmodtool --target %{_target_cpu} --repo rpmfusion --kmodname %{name} %{?buildforkernels:--%{buildforkernels}} %{?kernels:--for-kernels "%{?kernels}"} 2>/dev/null) }

%description
Akmod infrastructure for the Google Coral Edge TPU driver.

%prep
%{?kmodtool_check}
%setup -q -T -c -n %{name}-%{version}

%build
# Vazio

%install
%{?akmod_install}

%files
# Gerado pelo kmodtool

%changelog
* Mon Jan 19 2026 mwprado <mwprado@github> - 1.0-1
- Initial akmod build.
