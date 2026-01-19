%define buildforkernels akmod

Name:           google-coral-kmod
Version:        1.0
Release:        1%{?dist}
Summary:        Kernel module for Google Coral Edge TPU
License:        GPLv2

# Dependências obrigatórias conforme MadWiFi
BuildRequires:  sharutils
%define AkmodsBuildRequires sharutils
BuildRequires:  %{_bindir}/kmodtool
BuildRequires:  google-coral-kmodsrc = %{version}

# Expansão dinâmica do kmodtool
%{expand:%(kmodtool --target %{_target_cpu} --repo rpmfusion --kmodname %{name} %{?buildforkernels:--%{buildforkernels}} %{?kernels:--for-kernels "%{?kernels}"} 2>/dev/null) }

%description
Akmod infrastructure for the Google Coral Edge TPU driver.

%prep
%{?kmodtool_check}
%setup -q -T -c -n %{name}-%{version}

%build
# O build é processado localmente pelo akmods

%install
# A macro akmod_install trata da infraestrutura necessária (SRPM/Links) de forma automática
%{?akmod_install}

%files
# A lista de ficheiros é gerada dinamicamente pela macro kmodtool
