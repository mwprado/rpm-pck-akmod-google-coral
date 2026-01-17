Name:           google-coral
Version:        1.0
Release:        1%{?dist}
Summary:        Userland support for Google Coral Edge TPU
License:        GPLv2
URL:            https://github.com/google/gasket-driver

# Fontes vindas do seu GitHub conforme solicitado
Source0:        https://raw.githubusercontent.com/mwprado/rpm-pck-akmod-google-coral/main/99-google-coral.rules
Source1:        https://raw.githubusercontent.com/mwprado/rpm-pck-akmod-google-coral/main/google-coral.conf
Source2:        https://raw.githubusercontent.com/mwprado/rpm-pck-akmod-google-coral/main/google-coral-group.conf

BuildArch:      noarch

# REGRAS OBRIGATÓRIAS DO RPM FUSION (Seção 4 da Doc Kmods2)
# 1. O pacote se amarra ao kmod
Requires:       google-coral-kmod >= %{version}
# 2. O pacote provê a base comum para o driver
Provides:       google-coral-kmod-common = %{version}

BuildRequires:  systemd-rpm-macros

%description
Userland configuration for Google Coral Edge TPU.
Includes udev rules, group creation, and module loading configuration.
This package is required for the kernel module to function with correct permissions.

%prep
# Apenas para criar o diretório de build
%setup -q -c -n %{name}-%{version} -T

%build
# Pacote de configuração, nada para compilar aqui.

%install
# Instalação das Regras de Udev
mkdir -p %{buildroot}%{_udevrulesdir}
install -p -m 0644 %{SOURCE0} %{buildroot}%{_udevrulesdir}/99-google-coral.rules

# Instalação da carga automática do módulo
mkdir -p %{buildroot}%{_sysconfdir}/modules-load.d
install -p -m 0644 %{SOURCE1} %{buildroot}%{_sysconfdir}/modules-load.d/google-coral.conf

# Instalação da definição de Grupo (Sysusers)
mkdir -p %{buildroot}%{_sysusersdir}
install -p -m 0644 %{SOURCE2} %{buildroot}%{_sysusersdir}/google-coral.conf

%pre
# Criação do grupo via sysusers (Padrão Fedora Moderno)
%sysusers_create_package %{name} %{SOURCE2}

%files
%license
%{_udevrulesdir}/99-google-coral.rules
%{_sysconfdir}/modules-load.d/google-coral.conf
%{_sysusersdir}/google-coral.conf

%changelog
* Sat Jan 17 2026 mwprado <mwprado@github> - 1.0-1
- Initial Userland package following RPM Fusion Split-Package guidelines.
- Sources pulled directly from GitHub main branch.
