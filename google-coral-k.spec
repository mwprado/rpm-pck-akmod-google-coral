# Define que vamos gerar um pacote do tipo akmod (ideal para Silverblue)
%define buildforkernels akmod
%global debug_package %{nil}

# Nome do módulo conforme definido no código do Google
%global kmod_name google-coral

Name:           %{kmod_name}-kmod
Version:        1.0 
Release:        1%{?dist}
Summary:        Kernel module for Google Coral Edge TPU

License:        ASL 2.0
URL:            https://github.com/google/gasket-driver
# Fonte original do Google (Exemplo: gasket-driver)
Source0:        https://github.com/google/gasket-driver/archive/refs/heads/main.tar.gz#/%{kmod_name}-%{version}.tar.gz

# Seus patches no seu GitHub (substitua pelos links reais "raw")
Patch0:         https://raw.githubusercontent.com/seu-usuario/repo/main/patch-kernel-compat.patch
Patch1:         https://raw.githubusercontent.com/seu-usuario/repo/main/fix-pci-ids.patch

BuildRequires:  %{_bindir}/kmodtool
BuildRequires:  gcc
BuildRequires:  make

# Mágica do kmodtool: gera os subpacotes akmod e as dependências de kernel
%{expand:%(kmodtool --target %{_target_cpu} --repo copr --kmodname %{name} %{?buildforkernels:--%{buildforkernels}} 2>/dev/null) }

%description
This package provides the kernel driver for Google Coral devices (Gasket/Apex).

%prep
# Verifica se o kmodtool está funcionando
%{?kmodtool_check}

# 1. Extrai o código fonte
%setup -q -c -T -a 0
cd gasket-driver-main/ # Ajuste conforme o nome da pasta dentro do tar.gz

# 2. Aplica seus patches aqui, antes da replicação
%patch0 -p1
%patch1 -p1

cd ..

# 3. Replica o código fonte para cada versão de kernel que será compilada
for kernel_version in %{?kernel_versions} ; do
    cp -a gasket-driver-main _kmod_build_${kernel_version%%___*}
done

%build
# Itera sobre as versões de kernel e compila o módulo
for kernel_version in %{?kernel_versions}; do
    make %{?_smp_mflags} -C "${kernel_version##*___}" SUBDIRS=${PWD}/_kmod_build_${kernel_version%%___*} modules
done

%install
rm -rf ${RPM_BUILD_ROOT}
for kernel_version in %{?kernel_versions}; do
    # Cria o diretório de destino para o módulo .ko
    mkdir -p ${RPM_BUILD_ROOT}%{kmodinstdir_prefix}/${kernel_version%%___*}/%{kmodinstdir_postfix}/%{kmod_name}
    
    # Instala o módulo (ajuste o nome do arquivo .ko se necessário)
    install -m 755 _kmod_build_${kernel_version%%___*}/gasket.ko \
        ${RPM_BUILD_ROOT}%{kmodinstdir_prefix}/${kernel_version%%___*}/%{kmodinstdir_postfix}/%{kmod_name}/gasket.ko
    install -m 755 _kmod_build_${kernel_version%%___*}/apex.ko \
        ${RPM_BUILD_ROOT}%{kmodinstdir_prefix}/${kernel_version%%___*}/%{kmodinstdir_postfix}/%{kmod_name}/apex.ko
done

# Executa a instalação das macros de akmod
%{?akmod_install}

%clean
rm -rf $RPM_BUILD_ROOT

%changelog
* Sat Jan 17 2026 Seu Nome <seu@email.com> - 1.0-1
- Initial build with Google sources and custom patches for Silverblue.
