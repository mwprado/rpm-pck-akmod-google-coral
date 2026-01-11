# 1. Definições Iniciais (Exatamente como na NVIDIA)
%if 0%{?fedora}
%global buildforkernels akmod
%endif
%global debug_package %{nil}

%global akmod_name google-coral
%global kmodsrc_name google-coral-kmodsrc

# 2. Invocação do kmodtool com Prefix (O padrão rigoroso)
# A NVIDIA usa o prefixo para evitar que o output "suje" o cabeçalho global
%{?kmodtool_prefix}
%(kmodtool --target %{_target_cpu} --repo rpmfusion --kmodname %{name} %{?buildforkernels:--%{buildforkernels}} %{?kernels:--for-kernels "%{?kernels}"} 2>/dev/null)

Name:           google-coral-kmod
Version:        1.0
Release:        72%{?dist}
Summary:        Kernel module for Google Coral Edge TPU
License:        GPLv2
URL:            https://github.com/google/gasket-driver

Source1:        99-google-coral.rules
Source2:        google-coral.conf
Source5:        google-coral-group.conf

# 3. BuildRequires (A lista exata do RPM Fusion)
%global AkmodsBuildRequires %{_bindir}/kmodtool, %{kmodsrc_name} = %{version}, xz, time, gcc, make, kernel-devel, elfutils-libelf-devel, systemd-devel, systemd-rpm-macros
BuildRequires:  %{AkmodsBuildRequires}

# 4. Segunda expansão (Onde a NVIDIA injeta os subpacotes binários)
%{expand:%(kmodtool --target %{_target_cpu} --repo rpmfusion --kmodname %{name} %{?buildforkernels:--%{buildforkernels}} %{?kernels:--for-kernels "%{?kernels}"} 2>/dev/null) }

%description
Package to manage Google Coral Edge TPU kernel modules.
Follows NVIDIA and VirtualBox packaging standards for RPM Fusion.

# --- Nota: O %package akmod NÃO é escrito aqui, o kmodtool injeta-o ---

%prep
# Verificação de sanidade do kmodtool
%{?kmodtool_check}
%setup -q -T -c -n %{name}-%{version}

%build
# Vazio

%install
# A macro que faz a ligação ao kmodsrc e cria o .latest
%{?akmod_install}

# Instalação manual de ficheiros de suporte
mkdir -p %{buildroot}%{_udevrulesdir}
install -p -m 0644 %{SOURCE1} %{buildroot}%{_udevrulesdir}/99-google-coral.rules
mkdir -p %{buildroot}%{_sysconfdir}/modules-load.d
install -p -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/modules-load.d/google-coral.conf
mkdir -p %{buildroot}%{_sysusersdir}
install -p -m 0644 %{SOURCE5} %{buildroot}%{_sysusersdir}/google-coral.conf

# 5. Scripts vinculados ao nome que o kmodtool gera (akmod-google-coral)
%pre
%sysusers_create_package %{akmod_name} %{SOURCE5}

%files 
%{_udevrulesdir}/99-google-coral.rules
%{_sysconfdir}/modules-load.d/google-coral.conf
%{_sysusersdir}/google-coral.conf

%changelog
* Sun Jan 11 2026 mwprado <mwprado@github> - 1.0-72
- Version 72: Strictly mirrored NVIDIA/RPM Fusion spec structure.
- Corrected double-expansion of kmodtool to resolve dynamic subpackaging.
