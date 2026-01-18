%define buildforkernels akmod

Name:           google-coral-kmod
Version:        1.0
Release:        1%{?dist}
Summary:        Kernel module for Google Coral Edge TPU
License:        GPLv2
URL:            https://github.com/google/gasket-driver

# Este pacote foca apenas no kmodtool e no código fonte
BuildRequires:  %{_bindir}/kmodtool
BuildRequires:  google-coral-kmodsrc = %{version}
BuildRequires:  gcc, make, xz, time, kernel-devel, elfutils-libelf-devel
# Exigência para o funcionamento do akmod 
BuildRequires:  sharutils 
%define AkmodsBuildRequires sharutils 

# Injeção mágica do kmodtool (Padrão MadWiFi/RPM Fusion)
%{expand:%(kmodtool --target %{_target_cpu} --repo rpmfusion --kmodname %{name} %{?buildforkernels:--%{buildforkernels}} %{?kernels:--for-kernels "%{?kernels}"} 2>/dev/null) }

%description
This package contains the akmod infrastructure for the Google Coral Edge TPU driver.
It provides the source package for automatic kernel module building.

%prep
%{?kmodtool_check} 
%setup -q -T -c -n %{name}-%{version}

%build
# Vazio: o build real ocorre no cliente via akmods 
%install
# Garante que o diretório de destino existe no BUILDROOT
mkdir -p %{buildroot}%{_usrsrc}/akmods

# Entra no diretório para fazer o link relativo sem erro de path
pushd %{buildroot}%{_usrsrc}/akmods
# O SRPM deve ser colocado aqui (geralmente pelo kmodtool ou manualmente)
# Criamos o link relativo puro
ln -sf %{name}-%{version}-%{release}.src.rpm %{kmodname}.latest
popd

%{?akmod_install}
%files
# O kmodtool preenche esta seção automaticamente para o subpacote akmod 

%changelog
* Sun Jan 18 2026 mwprado <mwprado@github> - 1.0-1
- Clean kmod-only package based on MadWiFi template.
