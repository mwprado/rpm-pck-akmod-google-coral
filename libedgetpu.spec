# SPDX-License-Identifier: Apache-2.0

%global commit      e35aed18fea2e2d25d98352e5a5bd357c170bd4d
%global shortcommit e35aed1
%global tf_version  2.16.1

Name:           libedgetpu
Version:        16.0
Release:        1.tf%{tf_version}.git%{shortcommit}%{?dist}
Summary:        Userspace runtime library for Google Coral Edge TPU devices

License:        Apache-2.0
URL:            https://github.com/google-coral/libedgetpu

# Official Google Coral runtime source.
Source0:        %{url}/archive/%{commit}/libedgetpu-%{commit}.tar.gz

# libedgetpu's native Makefile build requires the matching TensorFlow source
# tree. Upstream's final release explicitly targets TensorFlow 2.16.1.
Source1:        https://github.com/tensorflow/tensorflow/archive/refs/tags/v%{tf_version}.tar.gz#/tensorflow-%{tf_version}.tar.gz

ExclusiveArch:  x86_64

BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  make
BuildRequires:  binutils
BuildRequires:  binutils-gold
BuildRequires:  xxd

BuildRequires:  flatbuffers-devel
BuildRequires:  flatbuffers-compiler
BuildRequires:  abseil-cpp-devel
BuildRequires:  libusb1-devel
BuildRequires:  pkgconf-pkg-config

Requires:       libusb1

%description
libedgetpu is the userspace runtime library for Google Coral Edge TPU
accelerators.

This package contains the standard-speed runtime. It is built from the
official Google Coral libedgetpu source against TensorFlow %{tf_version}.

The PCIe/M.2 Coral device is exposed by the gasket/apex kernel driver as
/dev/apex_0; libedgetpu provides the userspace interface used by TensorFlow
Lite and PyCoral.


%package devel
Summary:        Development files for libedgetpu
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
C and C++ headers and the linker symlink for applications that use
Google Coral Edge TPU through libedgetpu.


%prep
%setup -q -n libedgetpu-%{commit} -a 1

# The final upstream README requires C++17 for TensorFlow 2.16.1, while the
# standalone Makefile still carries the older c++14 setting. The build command
# below overrides it explicitly, but keep this source tree internally
# consistent as well.
sed -i 's/-std=c++14/-std=c++17/' makefile_build/Makefile


%build
TFROOT="${PWD}/tensorflow-%{tf_version}"

# New Fedora Abseil no longer ships a monolithic libabsl_flags.so. Use its
# pkg-config dependency graph instead of the historical hard-coded link list
# from libedgetpu's Makefile.
ABSL_LIBS="$(pkg-config --libs \
    absl_flags \
    absl_hash \
    absl_raw_hash_set \
    absl_str_format)"

make %{?_smp_mflags} \
    -f makefile_build/Makefile \
    TFROOT="${TFROOT}" \
    LIBEDGETPU_CFLAGS="%{build_cflags} -fPIC -Wall -std=c99" \
    LIBEDGETPU_CXXFLAGS="%{build_cxxflags} -fPIC -Wall -std=c++17 -DDARWINN_PORT_DEFAULT" \
    LIBEDGETPU_LDFLAGS="%{build_ldflags} \
        -Wl,-Map=${PWD}/out/output.map \
        -shared \
        -Wl,--soname,libedgetpu.so.1 \
        -Wl,--version-script=${PWD}/tflite/public/libedgetpu.lds \
        -fuse-ld=gold \
        -lflatbuffers \
        ${ABSL_LIBS} \
        -lusb-1.0" \
    libedgetpu-throttled


%install
install -D -p -m 0755 \
    out/throttled/k8/libedgetpu.so.1.0 \
    %{buildroot}%{_libdir}/libedgetpu.so.1.0

ln -s libedgetpu.so.1.0 \
    %{buildroot}%{_libdir}/libedgetpu.so.1

ln -s libedgetpu.so.1 \
    %{buildroot}%{_libdir}/libedgetpu.so

install -D -p -m 0644 \
    tflite/public/edgetpu.h \
    %{buildroot}%{_includedir}/edgetpu.h

install -D -p -m 0644 \
    tflite/public/edgetpu_c.h \
    %{buildroot}%{_includedir}/edgetpu_c.h


%check
readelf -d %{buildroot}%{_libdir}/libedgetpu.so.1.0 | \
    grep -q 'SONAME.*libedgetpu.so.1'

nm -D %{buildroot}%{_libdir}/libedgetpu.so.1.0 | \
    grep -q 'edgetpu_list_devices'


%files
%license LICENSE
%doc README.md
%{_libdir}/libedgetpu.so.1
%{_libdir}/libedgetpu.so.1.0


%files devel
%{_includedir}/edgetpu.h
%{_includedir}/edgetpu_c.h
%{_libdir}/libedgetpu.so


%changelog
* Mon Sep 21 2026 Moacyr Prado <mwprado@github> - 16.0-1.tf2.16.1.gite35aed1
- Initial Fedora package for Google Coral libedgetpu
- Build official upstream source against TensorFlow 2.16.1
- Use Fedora system Abseil, FlatBuffers and libusb
- Package the standard-speed runtime for Silverblue
