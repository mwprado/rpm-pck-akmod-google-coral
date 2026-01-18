%global kmodname google-coral
%define buildforkernels akmod

Name:           google-coral-kmod
Version:        1.0
Release:        1%{?dist}
Summary:        Módulo de kernel para Google Coral Edge TPU
License:        GPLv2
URL:            https://github.com/google/gasket-driver

# Dependências de Build conforme madwifi-kmod.spec
BuildRequires:  %{_bindir}/kmodtool
BuildRequires:  google-coral-kmodsrc = %{version}
BuildRequires:  gcc, make, xz, time, kernel-devel, elfutils-libelf-devel
BuildRequires:  sharutils
%define AkmodsBuildRequires sharutils

# Expansão dinâmica do kmodtool
%{expand:%(/usr/bin/kmodtool --target %{_target_cpu} --repo rpmfusion --kmodname %{name} %{?buildforkernels:--%{buildforkernels}} %{?kernels:--for-kernels "%{?kernels}"} 2>/dev/null) }

%description
Infraestrutura akmod para o driver Google Coral Edge TPU.
Este pacote reconstrói o módulo do kernel automaticamente após atualizações.

%prep
%{?kmodtool_check}
%setup -q -T -c -n %{name}-%{version}

%build
# Vazio

%install
# 1. Preparação do diretório no BUILDROOT
mkdir -p %{buildroot}%{_usrsrc}/akmods

# 2. Geração do SRPM interno (Padrão para entrega via akmod)
rpmbuild --define '_sourcedir %{_sourcedir}' \
         --define '_srcrpmdir %{buildroot}%{_usrsrc}/akmods/' \
         --define 'dist %{dist}' \
         -bs --nodeps %{_specdir}/%{name}.spec

# 3. CORRECÇÃO DO LINK (v102): Garantindo path relativo para evitar erro de 'No such file'
pushd %{buildroot}%{_usrsrc}/akmods
    # Localiza o SRPM gerado dinamicamente
    SRPM_FILE=$(ls %{name}-%{version}-*.src.rpm)
    # Cria o link .latest conforme padrão NVIDIA/VirtualBox
    ln -sf $SRPM_FILE %{kmodname}.latest
popd

# 4. Invocação da macro de instalação oficial
%{?akmod_install}

%files
# O kmodtool gere a lista de ficheiros para o subpacote akmod
# Incluímos manualmente o diretório e o link para garantir a posse
%dir %{_usrsrc}/akmods
%{_usrsrc}/akmods/%{kmodname}.latest
%{_usrsrc}/akmods/%{name}-%{version}-*.src.rpm

%changelog
* Sun Jan 18 2026 mwprado <mwprado@github> - 1.0-1
- Versão final simplificada e corrigida.
- Implementação de pushd no %install para link simbólico resiliente.
- Removidos ficheiros de userland para evitar erro de 'unpackaged files'.
