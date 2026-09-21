# SPDX-License-Identifier: Apache-2.0

%global commit      e35aed18fea2e2d25d98352e5a5bd357c170bd4d
%global shortcommit e35aed1
%global tf_version  2.16.1

Name:           libedgetpu
Version:        16.0
Release:        3.tf%{tf_version}.git%{shortcommit}%{?dist}
Summary:        PCIe userspace runtime library for Google Coral Edge TPU

License:        Apache-2.0
URL:            https://github.com/google-coral/libedgetpu

# Official Google Coral runtime source.
Source0:        %{url}/archive/%{commit}/libedgetpu-%{commit}.tar.gz

# The native Makefile build needs the matching TensorFlow source tree.
Source1:        https://github.com/tensorflow/tensorflow/archive/refs/tags/v%{tf_version}.tar.gz#/tensorflow-%{tf_version}.tar.gz

ExclusiveArch:  x86_64

BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  make
BuildRequires:  python3
BuildRequires:  binutils
BuildRequires:  binutils-gold

BuildRequires:  flatbuffers-devel
BuildRequires:  flatbuffers-compiler
BuildRequires:  abseil-cpp-devel
BuildRequires:  pkgconf-pkg-config

%description
libedgetpu is the userspace runtime library for Google Coral Edge TPU
accelerators.

This Fedora build is intentionally PCIe/M.2-only.  It targets Coral devices
exposed by the gasket/apex kernel driver as /dev/apex_N and omits the USB
transport, DFU firmware handling and libusb dependency.

The package is built from the official Google Coral libedgetpu source against
TensorFlow %{tf_version}.


%package devel
Summary:        Development files for libedgetpu
Requires:       %{name}%{?_isa} = %{version}-%{release}

%description devel
C and C++ headers and the linker symlink for applications that use
Google Coral Edge TPU through libedgetpu.


%prep
%setup -q -n libedgetpu-%{commit} -a 1

python3 - <<'PY'
from pathlib import Path

p = Path("makefile_build/Makefile")
text = p.read_text()

# Upstream's last released standalone Makefile predates the TensorFlow 2.16
# source layout.  Follow the later upstream maintenance work: the old C source
# is gone and the required TensorFlow Lite implementation files are C++.
text = text.replace("-std=c++14", "-std=c++17")
text = text.replace(
    "LIBEDGETPU_CSRCS := $(TFROOT)/tensorflow/lite/c/common.c",
    "LIBEDGETPU_CSRCS :="
)

needle = "\t$(TFROOT)/tensorflow/lite/util.cc\n"
replacement = (
    "\t$(TFROOT)/tensorflow/lite/core/c/common.cc \\\n"
    "\t$(TFROOT)/tensorflow/lite/util.cc \\\n"
    "\t$(TFROOT)/tensorflow/lite/array.cc\n"
)
if needle not in text:
    raise SystemExit("TensorFlow Lite source-list anchor not found")
text = text.replace(needle, replacement, 1)

# This machine uses a PCIe/M.2 Coral (/dev/apex_0).  Remove the entire USB
# provider and USB transport from the standalone build.  This also avoids
# compiling obsolete DFU code with current Fedora/GCC.
remove_sources = [
    "$(BUILDROOT)/driver/beagle/beagle_usb_driver_provider.cc",
    "$(BUILDROOT)/driver/usb/libusb_options_default.cc",
    "$(BUILDROOT)/driver/usb/local_usb_device.cc",
    "$(BUILDROOT)/driver/usb/usb_dfu_commands.cc",
    "$(BUILDROOT)/driver/usb/usb_dfu_util.cc",
    "$(BUILDROOT)/driver/usb/usb_driver.cc",
    "$(BUILDROOT)/driver/usb/usb_io_request.cc",
    "$(BUILDROOT)/driver/usb/usb_ml_commands.cc",
    "$(BUILDROOT)/driver/usb/usb_registers.cc",
    "$(BUILDROOT)/driver/usb/usb_standard_commands.cc",
]

lines = text.splitlines()
lines = [
    line for line in lines
    if not any(src in line for src in remove_sources)
]
text = "\n".join(lines) + "\n"

# No legacy C object remains.
text = text.replace(" firmware $(LIBEDGETPU_FLATC_OBJS) $(LIBEDGETPU_COBJS) ",
                    " $(LIBEDGETPU_FLATC_OBJS) ")
text = text.replace(" $(LIBEDGETPU_FLATC_OBJS) $(LIBEDGETPU_COBJS) ",
                    " $(LIBEDGETPU_FLATC_OBJS) ")
text = text.replace("$(LIBEDGETPU_COBJS) $(LIBEDGETPU_CCOBJS)",
                    "$(LIBEDGETPU_CCOBJS)")

p.write_text(text)
PY


%build
TFROOT="${PWD}/tensorflow-%{tf_version}"

# Fedora's modern Abseil is split into many libraries.  Let pkg-config provide
# the complete transitive link set rather than using the historical hard-coded
# Debian library list.
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
        ${ABSL_LIBS}" \
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
* Mon Sep 21 2026 Moacyr Prado <mwprado@github> - 16.0-3.tf2.16.1.gite35aed1
- Build a PCIe/M.2-only runtime for gasket/apex devices
- Remove obsolete USB/DFU sources and the libusb dependency
- Align standalone Makefile source list with modern TensorFlow Lite
- Add tensorflow/lite/core/c/common.cc and tensorflow/lite/array.cc

* Mon Sep 21 2026 Moacyr Prado <mwprado@github> - 16.0-2.tf2.16.1.gite35aed1
- Fix standalone Makefile for TensorFlow 2.16.1 common.cc location
- Compile TensorFlow Lite common.cc as C++

* Mon Sep 21 2026 Moacyr Prado <mwprado@github> - 16.0-1.tf2.16.1.gite35aed1
- Initial Fedora package for Google Coral libedgetpu
- Build official upstream source against TensorFlow 2.16.1
- Use Fedora system Abseil and FlatBuffers
- Package the standard-speed runtime for Silverblue
