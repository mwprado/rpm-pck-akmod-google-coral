Name:           google-coral
Version:        1.0
Release:        1%{?dist}
Summary:        Userland support for Google Coral Edge TPU
License:        GPLv2
URL:            https://github.com/google/gasket-driver

# Fontes diretas do GitHub do projeto
Source0:        https://raw.githubusercontent.com/mwprado/rpm-pck-akmod-google-coral/main/99-google-coral.rules
Source1:        https://raw.githubusercontent.com/mwprado/rpm-pck-akmod-google-coral/main/google-coral.conf
Source2:        https://raw.githubusercontent.com/mwprado/rpm-pck-akmod-google-coral/main/google-coral-group.conf

BuildArch:      noarch

# SEÇÃO DE DEPENDÊNCIAS (Rigor RPM Fusion)
# Requer o módulo do kernel para funcionar
Requires:       google-coral-kmod >= %{version} 
# Provê a base comum exigida pela documentação Kmods2
Provides:       google-coral-kmod-common = %{version}

BuildRequires:  systemd-rpm-macros

%description
Userland configuration for Google Coral Edge TPU. 
Includes udev rules, group creation, and module loading configuration.
Following the split-package model, this contains all non-kernel files.

%prep
%setup -q -c -n %{name}-%{version} -T

%install
# 1. Regras de Udev
mkdir -p %{buildroot}%{_udevrulesdir}
install -p -m 0644 %{SOURCE0} %{buildroot}%{_udevrulesdir}/99-google-coral.rules

# 2. Carga automática do módulo
mkdir -p %{buildroot}%{_sysconfdir}/modules-load.d
install -p -m 0644 %{SOURCE1} %{buildroot}%{_sysconfdir}/modules-load.d/google-coral.conf

# 3. Definição de Grupo (Sysusers)
mkdir -p %{buildroot}%{_sysusersdir}
install -p -m 0644 %{SOURCE2} %{buildroot}%{_sysusersdir}/google-coral.conf

%pre
# Criação do grupo 'apex' via sysusers
%sysusers_create_package %{name} %{SOURCE2}

%files
%{_udevrulesdir}/99-google-coral.rules
%{_sysconfdir}/modules-load.d/google-coral.conf
%{_sysusersdir}/google-coral.conf

%changelog
* Sun Jan 18 2026 mwprado <mwprado@github> - 1.0-1
- Initial split-package version (Userland).
