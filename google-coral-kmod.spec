%global kmodname google-coral
%global kmodsrc_name google-coral-kmodsrc

%if 0%{?fedora}
%global buildforkernels akmod
%endif
%global debug_package %{nil}

Name:           %{kmodname}-kmod
Version:        1.0
Release:        85%{?dist}
Summary:        Kernel module for Google Coral Edge TPU
License:        GPLv2
URL:            https://github.com/google/gasket-driver

Source1:        99-google-coral.rules
Source2:        google-coral.conf
Source5:        google-coral-group.conf

BuildRequires:  %{_bindir}/kmodtool
BuildRequires:  %{kmodsrc_name} = %{version}
BuildRequires:  gcc, make, xz, time, kernel-devel, elfutils-libelf-devel, systemd-devel, systemd-rpm-macros

# 1. Injeção dinâmica do kmodtool (Padrão RPM Fusion)
%{expand:%(/usr/bin/kmodtool --target %{_target_cpu} --repo rpmfusion --kmodname %{name} %{?buildforkernels:--%{buildforkernels}} %{?kernels:--for-kernels "%{?kernels}"} 2>/dev/null) }

%description
Google Coral Edge TPU kernel module infrastructure.
Rigorously follows VirtualBox/NVIDIA pattern. .latest points to the SRPM in the same dir.

%prep
%{?kmodtool_check}
%setup -q -T -c -n %{name}-%{version}

%build
# Vazio

%install
# 2. O LINK .LATEST (Rigorosamente conforme NVIDIA/VirtualBox)
# O akmods espera o link dentro de /usr/src/akmods apontando para o arquivo no mesmo diretório
mkdir -p %{buildroot}%{_usrsrc}/akmods

# NOTA: O arquivo .src.rpm já é instalado aqui pelo seu pacote 'google-coral-kmodsrc'.
# Criamos o link relativo para evitar erros de path absoluto.
ln -sf %{name}-%{version}-%{release}.src.rpm %{buildroot}%{_usrsrc}/akmods/%{kmodname}.latest

# Instalação de arquivos extras
mkdir -p %{buildroot}%{_udevrulesdir}
install -p -m 0644 %{SOURCE1} %{buildroot}%{_udevrulesdir}/99-google-coral.rules
mkdir -p %{buildroot}%{_sysconfdir}/modules-load.d
install -p -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/modules-load.d/google-coral.conf
mkdir -p %{buildroot}%{_sysusersdir}
install -p -m 0644 %{SOURCE5} %{buildroot}%{_sysusersdir}/google-coral.conf

# 3. EMPACOTAMENTO DOS ARQUIVOS (Resolvendo o erro de unpackaged)
# Como o kmodtool do Fedora não aceita '%files -n' duplicado, usamos a macro interna.
%global akmod_files %{_usrsrc}/akmods/%{kmodname}.latest %{_udevrulesdir}/99-google-coral.rules %{_sysconfdir}/modules-load.d/google-coral.conf %{_sysusersdir}/google-coral.conf

%changelog
* Sun Jan 11 2026 mwprado <mwprado@github> - 1.0-85
- Version 85: Strict alignment with NVIDIA/VirtualBox symlink pattern.
- .latest link is now relative to the SRPM located in /usr/src/akmods/.
