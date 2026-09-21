# SPDX-License-Identifier: Apache-2.0

%global commit      e35aed18fea2e2d25d98352e5a5bd357c170bd4d
%global shortcommit e35aed1
%global tf_version  2.16.1
%global flatbuffers_commit 7d6d99c6befa635780a4e944d37ebfd58e68a108
%global flatbuffers_version 23.5.26

Name:           libedgetpu
Version:        16.0
Release:        6.tf%{tf_version}.git%{shortcommit}%{?dist}
Summary:        PCIe userspace runtime library for Google Coral Edge TPU

License:        Apache-2.0
URL:            https://github.com/google-coral/libedgetpu

# Official Google Coral runtime source.
Source0:        %{url}/archive/%{commit}/libedgetpu-%{commit}.tar.gz

# The native Makefile build needs the matching TensorFlow source tree.
Source1:        https://github.com/tensorflow/tensorflow/archive/refs/tags/v%{tf_version}.tar.gz#/tensorflow-%{tf_version}.tar.gz

# TensorFlow 2.16.1 pins FlatBuffers 23.5.26. Fedora 44 ships a newer
# incompatible major version, so use the exact TensorFlow-pinned source as a
# private build dependency rather than replacing Fedora's system FlatBuffers.
Source2:        https://github.com/google/flatbuffers/archive/%{flatbuffers_commit}/flatbuffers-%{flatbuffers_commit}.tar.gz

# Local correctness fixes found while auditing the archived libedgetpu source.
Patch0:         0001-libedgetpu-fix-mmu-ioctl-fallback-and-open-cleanup.patch
Patch1:         0002-libedgetpu-clean-up-partial-register-mappings.patch
Patch2:         0003-libedgetpu-validate-eventfd-and-event-index.patch

ExclusiveArch:  x86_64

BuildRequires:  gcc
BuildRequires:  gcc-c++
BuildRequires:  make
BuildRequires:  python3
BuildRequires:  cmake
BuildRequires:  binutils
BuildRequires:  binutils-gold

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
%setup -q -n libedgetpu-%{commit} -a 1 -a 2
%autopatch -p1

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
FLATBUFFERS_SRC="${PWD}/flatbuffers-%{flatbuffers_commit}"
FLATBUFFERS_BUILD="${PWD}/_flatbuffers"

# TensorFlow 2.16.1 generated headers require FlatBuffers 23.x exactly.
# Build the TensorFlow-pinned 23.5.26 privately for libedgetpu.  Nothing from
# this private FlatBuffers build is installed into the resulting RPM.
cmake \
    -S "${FLATBUFFERS_SRC}" \
    -B "${FLATBUFFERS_BUILD}" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
    -DFLATBUFFERS_BUILD_TESTS=OFF \
    -DFLATBUFFERS_BUILD_FLATC=ON \
    -DFLATBUFFERS_BUILD_FLATLIB=ON \
    -DFLATBUFFERS_BUILD_SHAREDLIB=OFF

cmake --build "${FLATBUFFERS_BUILD}" \
    --parallel %{?_smp_build_ncpus} \
    --target flatc flatbuffers

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
    FLATC="${FLATBUFFERS_BUILD}/flatc" \
    LIBEDGETPU_CXXFLAGS="%{build_cxxflags} -I${FLATBUFFERS_SRC}/include -fPIC -Wall -std=c++17 -DDARWINN_PORT_DEFAULT" \
    LIBEDGETPU_LDFLAGS="%{build_ldflags} \
        -Wl,-Map=${PWD}/out/output.map \
        -shared \
        -Wl,--soname,libedgetpu.so.1 \
        -Wl,--version-script=${PWD}/tflite/public/libedgetpu.lds \
        -fuse-ld=gold \
        -Wl,--whole-archive \
        ${FLATBUFFERS_BUILD}/libflatbuffers.a \
        -Wl,--no-whole-archive \
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

# Catch unresolved runtime symbols that a normal shared-library link permits.
# This specifically prevents static archive ordering mistakes (such as
# FlatBuffers ClassicLocale) from producing an RPM that builds but cannot be
# dlopen()'d.
python3 - <<'PY'
import ctypes
ctypes.CDLL(r"%{buildroot}%{_libdir}/libedgetpu.so.1.0")
PY


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
* Mon Sep 21 2026 Moacyr Prado <mwprado@github> - 16.0-6.tf2.16.1.gite35aed1
- Fix Linux ioctl fallback for legacy Gasket map-buffer support
- Close MMU device fd when page-table partitioning fails
- Clean up partial PCI register mappings when a later mmap fails
- Fix inverted unmap error logging and Read32 alignment diagnostic
- Validate eventfd creation and event indices before registration

* Mon Sep 21 2026 Moacyr Prado <mwprado@github> - 16.0-5.tf2.16.1.gite35aed1
- Force inclusion of the private FlatBuffers static archive at link time
- Fix unresolved flatbuffers::ClassicLocale runtime symbol
- Add dlopen smoke test to catch unresolved symbols during COPR build

* Mon Sep 21 2026 Moacyr Prado <mwprado@github> - 16.0-4.tf2.16.1.gite35aed1
- Build privately against TensorFlow-pinned FlatBuffers 23.5.26
- Avoid Fedora 44 FlatBuffers 25 header incompatibility
- Keep the private FlatBuffers build out of the installed runtime

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
