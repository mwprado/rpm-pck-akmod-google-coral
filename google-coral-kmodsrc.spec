Name:           google-coral-kmodsrc
Version:        1.0
Release:        1%{?dist}
Summary:        Source code for Google Coral Edge TPU kernel module
License:        GPLv2
URL:            https://github.com/google/gasket-driver

# Este pacote não compila nada, ele apenas transporta o código
BuildArch:      noarch

%description
This package provides the source code (SRPM) for the Google Coral kernel module.
It is required by the akmod package to rebuild the module for new kernels.

%prep
# Nada a preparar, apenas um container

%build
# Vazio

%install
# 1. Criar o diretório onde o akmod espera encontrar o fonte
mkdir -p %{buildroot}%{_usrsrc}/akmods/

# 2. O kmodsrc deve depositar o seu próprio SRPM (ou o SRPM do kmod) aqui.
# Em um ambiente de build real, o kmodsrc é usado para levar os arquivos 
# necessários para que o link .latest funcione.
# Nota: Você deve garantir que o arquivo .src.rpm esteja disponível no diretório.
# install -p -m 0644 %{name}-%{version}-%{release}.src.rpm %{buildroot}%{_usrsrc}/akmods/

%files
%{_usrsrc}/akmods/

%changelog
* Sun Jan 18 2026 mwprado <mwprado@github> - 1.0-1
- Initial kmodsrc package to support the split-package architecture.
