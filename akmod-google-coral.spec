%global akmod_name google-coral

Name:           akmod-google-coral
Version:        1.0
Release:        45.20260105git5815ee3%{?dist}
Summary:        Akmod package for Google Coral Edge TPU driver
License:        GPLv2
URL:            https://github.com/google/gasket-driver

Source0:        %{url}/archive/5815ee3908a46a415aac616ac7b9aedcb98a504c/gasket-driver-5815ee3.tar.gz
Source1:        99-google-coral.rules
Source2:        google-coral.conf
Source3:        fix-for-no_llseek.patch
Source4:        fix-for-module-import-ns.patch
Source5:        google-coral-group.conf

BuildRequires:  rpm-build, gcc, make, systemd-rpm-macros
# Precisamos garantir que o ambiente de build tenha o que é necessário para gerar o SRPM
BuildRequires:  kernel-devel

# Este Provides é o que faz o comando 'akmods --akmod google-coral' funcionar
Provides:       akmod(%{akmod_name}) = %{version}-%{release}

%description
Este pacote contém o SRPM (Source RPM) do driver Google Coral. 
Ele é projetado para que o utilitário akmods reconstrua o módulo do kernel 
automaticamente sempre que houver uma atualização de sistema.

%prep
%setup -q -n gasket-driver-5815ee3908a46a415aac616ac7b9aedcb98a504c
%patch -P 3 -p1
%patch -P 4 -p1

%build
# Criamos o SPEC interno que existirá dentro do SRPM
# Este é o SPEC que o 'akmods' realmente vai ler no futuro
cat << 'EOF' > kmod-google.spec
Name:           kmod-google-coral
Version:        %{version}
Release:        %{release}
Summary:        Google Coral Edge TPU kernel module
License:        GPLv2
%description
Módulo de kernel compilado via akmods.
%prep
%setup -q -c
%build
make -C /lib/modules/%{?kver}/build M=$(pwd)/src modules
%install
install -D -m 0644 src/gasket.ko %{buildroot}/lib/modules/%{?kver}/extra/gasket/gasket.ko
install -D -m 0644 src/apex.ko %{buildroot}/lib/modules/%{?kver}/extra/gasket/apex.ko
EOF

%install
# 1. PREPARAÇÃO DO SRPM (PACOTE DENTRO DO PACOTE)
mkdir -p rpmbuild/{SOURCES,SPECS,SRPMS}
# Criamos um tarball com o código já patcheado
tar -czf rpmbuild/SOURCES/google-coral.tar.gz .
cp kmod-google.spec rpmbuild/SPECS/

# Ajustamos o SPEC interno para usar o tarball
sed -i 's/%%setup -q -c/%%setup -q -n google-coral -c/' rpmbuild/SPECS/kmod-google.spec
sed -i '/Name:/a Source0: google-coral.tar.gz' rpmbuild/SPECS/kmod-google.spec

# Geramos o SRPM real
rpmbuild -bs rpmbuild/SPECS/kmod-google.spec \
    --define "_topdir $(pwd)/rpmbuild" \
    --define "kver %{kernel_version}"

# 2. INSTALAÇÃO NO DIRETÓRIO DE AKMODS
install -d %{buildroot}%{_usrsrc}/akmods/
install -p -m 0644 rpmbuild/SRPMS/kmod-google-coral-*.src.rpm %{buildroot}%{_usrsrc}/akmods/kmod-google.src.rpm

# 3. O LINK .LATEST (Ponto de entrada do akmods)
pushd %{buildroot}%{_usrsrc}/akmods/
ln -s kmod-google.src.rpm %{akmod_name}.latest
popd

# Arquivos de suporte (Udev, Group, Modules-load)
install -D -m 0644 %{SOURCE1} %{buildroot}%{_udevrulesdir}/99-google-coral.rules
install -D -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/modules-load.d/google-coral.conf
install -D -m 0644 %{SOURCE5} %{buildroot}%{_sysusersdir}/google-coral.conf

%pre
%sysusers_create_package google-coral %{SOURCE5}

%files
%license LICENSE
%{_usrsrc}/akmods/kmod-google.src.rpm
%{_usrsrc}/akmods/%{akmod_name}.latest
%{_udevrulesdir}/99-google-coral.rules
%{_sysconfdir}/modules-load.d/google-coral.conf
%{_sysusersdir}/google-coral.conf

%changelog
* Sat Jan 10 2026 mwprado <mwprado@github> - 1.0-45
- Pacote renomeado para akmod-google-coral.
- Agora contém um SRPM real e um link .latest para compatibilidade total com Fedora 43.
