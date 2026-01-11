%global akmod_name google-coral
%global _specname kmod-google-coral

Name:           akmod-google-coral
Version:        1.0
Release:        46.20260105git5815ee3%{?dist}
Summary:        Akmod package for Google Coral Edge TPU driver
License:        GPLv2
URL:            https://github.com/google/gasket-driver

Source0:        %{url}/archive/5815ee3908a46a415aac616ac7b9aedcb98a504c/gasket-driver-5815ee3.tar.gz
Source1:        99-google-coral.rules
Source2:        google-coral.conf
Source3:        fix-for-no_llseek.patch
Source4:        fix-for-module-import-ns.patch
Source5:        google-coral-group.conf

# Ferramentas necessárias para gerar o pacote interno durante o build
BuildRequires:  rpm-build, gcc, make, sed
BuildRequires:  systemd-rpm-macros

# Metadado que o utilitário 'akmods' busca no sistema
Provides:       akmod(%{akmod_name}) = %{version}-%{release}

%description
Este pacote instala o Source RPM (SRPM) do driver Google Coral em /usr/src/akmods/.
O utilitário akmods usará esse SRPM para compilar o módulo para cada novo kernel.

%prep
%setup -q -n gasket-driver-5815ee3908a46a415aac616ac7b9aedcb98a504c
# Aplicamos os patches no código que irá para dentro do SRPM
%patch -P 3 -p1
%patch -P 4 -p1

%build
# 1. CRIAMOS O SPEC "INTERNO" (O que vai dentro do SRPM)
cat << 'EOF' > %{_specname}.spec
Name:           %{_specname}
Version:        %{version}
Release:        %{release}
Summary:        Google Coral Edge TPU kernel module
License:        GPLv2
Source0:        google-coral-src.tar.gz

%description
Módulo de kernel compilado dinamicamente pelo akmods.

%prep
%setup -q -n google-coral-src
%build
make -C /lib/modules/%{?kver}/build M=$(pwd)/src modules
%install
install -D -m 0644 src/gasket.ko %{buildroot}/lib/modules/%{?kver}/extra/gasket/gasket.ko
install -D -m 0644 src/apex.ko %{buildroot}/lib/modules/%{?kver}/extra/gasket/apex.ko
EOF

%install
# 2. PREPARAÇÃO DO SRPM INTERNO
mkdir -p rpmbuild/{SOURCES,SPECS,SRPMS}
# Compactamos o código já patcheado para o SRPM
tar -czf rpmbuild/SOURCES/google-coral-src.tar.gz .
cp %{_specname}.spec rpmbuild/SPECS/

# Geramos o SRPM real (o kmod-google-coral.src.rpm)
rpmbuild -bs rpmbuild/SPECS/%{_specname}.spec \
    --define "_topdir $(pwd)/rpmbuild" \
    --define "kver %{kernel_version}"

# 3. INSTALAÇÃO DOS ARQUIVOS NO SISTEMA
install -d %{buildroot}%{_usrsrc}/akmods/

# Copiamos o SRPM gerado para a pasta de destino
# Usamos um nome fixo para facilitar o link .latest
install -p -m 0644 rpmbuild/SRPMS/%{_specname}-*.src.rpm %{buildroot}%{_usrsrc}/akmods/%{_specname}.src.rpm

# Criamos o link .latest apontando para o arquivo SRPM (Fim do erro 21!)
pushd %{buildroot}%{_usrsrc}/akmods/
ln -s %{_specname}.src.rpm %{akmod_name}.latest
popd

# Arquivos de configuração do sistema
install -D -m 0644 %{SOURCE1} %{buildroot}%{_udevrulesdir}/99-google-coral.rules
install -D -m 0644 %{SOURCE2} %{buildroot}%{_sysconfdir}/modules-load.d/google-coral.conf
install -D -m 0644 %{SOURCE5} %{buildroot}%{_sysusersdir}/google-coral.conf

%pre
%sysusers_create_package google-coral %{SOURCE5}

%files
%license LICENSE
%{_usrsrc}/akmods/%{_specname}.src.rpm
%{_usrsrc}/akmods/%{akmod_name}.latest
%{_udevrulesdir}/99-google-coral.rules
%{_sysconfdir}/modules-load.d/google-coral.conf
%{_sysusersdir}/google-coral.conf

%changelog
* Sat Jan 10 2026 mwprado <mwprado@github> - 1.0-46
- Arquitetura final: Pacote binário akmod carregando o SRPM do kmod.
- Link .latest agora aponta corretamente para um arquivo .src.rpm.
