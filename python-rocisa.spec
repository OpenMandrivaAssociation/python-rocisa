# rocisa — Python/nanobind AMDGCN ISA generator for hipBLASLt TensileLite
# Built from the hipblaslt tensilelite/rocisa tree (TheRock 10.0).

Name:		python-rocisa
Version:	10.0.0
Release:	1
%{!?rocm_llvm_maj_ver:%global rocm_llvm_maj_ver 23}
Summary:	Python AMDGCN ISA generator (rocisa) for ROCm TensileLite
License:	MIT
Group:		Development/Python
URL:		https://github.com/ROCm/rocm-libraries
# rocisa lives inside the hipblaslt asset
Source0:	https://github.com/ROCm/rocm-libraries/releases/download/therock-10.0/hipblaslt.tar.gz#/hipblaslt-%{version}.tar.gz
# Conversion glue sources (also shipped in stinkytofu-devel)
Source1:	https://github.com/ROCm/rocm-libraries/releases/download/therock-10.0/stinkytofu.tar.gz#/stinkytofu-%{version}.tar.gz
Patch0:		0001-rocisa-distro-standalone.patch
Patch1:		0002-true16-ecvt-f32-to-f16.patch

BuildRequires:	rocm-rpm-macros
BuildRequires:	cmake
BuildRequires:	ninja
BuildRequires:	git-core
BuildRequires:	rocm-cmake
BuildRequires:	rocm-hip-devel
BuildRequires:	clang >= %{rocm_llvm_maj_ver}
BuildRequires:	pkgconfig(python3)
BuildRequires:	lib64python-devel
BuildRequires:	python%{pyver}dist(nanobind)
BuildRequires:	origami-devel
BuildRequires:	stinkytofu-devel
BuildRequires:	rocm-comgr-devel

Requires:	stinkytofu%{?_isa}
Requires:	origami%{?_isa}
Requires:	rocm-hip%{?_isa}

Provides:	python%{pyver}dist(rocisa) = 0.1.0
Provides:	rocisa = %{version}-%{release}

%global debug_package %{nil}


%description
rocisa is a nanobind Python extension that generates AMDGCN ISA for
hipBLASLt TensileLite (TensileLogic / TensileCreateLibrary).

%prep
%autosetup -n hipblaslt -p1
# Conversion sources: prefer tree layout matching STINKYTOFU_SOURCE_DIR
rm -rf shared/stinkytofu
mkdir -p shared
tar -xf %{SOURCE1} -C shared
# tarball top dir is stinkytofu/

%build
export CC=clang
export CXX=clang++
export ROCM_PATH=%{_prefix}
export HIP_PATH=%{_prefix}
export HIP_DEVICE_LIB_PATH=%{_libdir}/amdgcn/bitcode
CXXFLAGS=$(printf '%s' "%{optflags}" | sed -E 's/-mfpmath=[^ ]+//g; s/ -m[a-z0-9+.=]+//g')
export CXXFLAGS
export CFLAGS="$CXXFLAGS"
export LDFLAGS=$(printf '%s' "%{?__global_ldflags}" | sed -E 's/-mfpmath=[^ ]+//g; s/ -m[a-z0-9+.=]+//g')
_nanobind_dir="$(python -c 'import nanobind, os; print(os.path.join(os.path.dirname(nanobind.__file__), "cmake"))')"
_st_src="$(pwd)/shared/stinkytofu"

# Standalone rocisa project (ROCISA_STANDALONE=ON when this is the source root)
cd tensilelite/rocisa
%cmake \
	-DCMAKE_BUILD_TYPE=Release \
	-DCMAKE_CXX_COMPILER=clang++ \
	-DCMAKE_INSTALL_PREFIX=%{python3_sitearch} \
	-DCMAKE_INSTALL_LIBDIR=%{_lib} \
	-DSTINKYTOFU_SOURCE_DIR="${_st_src}" \
	-Dnanobind_DIR="${_nanobind_dir}" \
	-DROCM_PATH=%{_prefix} \
	-DCMAKE_PREFIX_PATH=%{_prefix} \
	-DBUILD_SHARED_LIBS=ON \
	-G Ninja
%ninja_build
cd ../..

%install
cd tensilelite/rocisa/build
DESTDIR=%{buildroot} /usr/bin/ninja install -j%{?_smp_build_ncpus}%{!?_smp_build_ncpus:8}
cd ../../..
# Ensure package layout: %{python3_sitearch}/rocisa/{__init__.py,_rocisa*.so}
if [ ! -e %{buildroot}%{python3_sitearch}/rocisa/__init__.py ]; then
	mkdir -p %{buildroot}%{python3_sitearch}/rocisa
	install -m 644 tensilelite/rocisa/rocisa/__init__.py \
		%{buildroot}%{python3_sitearch}/rocisa/
	# module may have been installed as top-level
	find %{buildroot} -name '_rocisa*.so' -exec mv {} %{buildroot}%{python3_sitearch}/rocisa/ \;
fi

%check
export LD_LIBRARY_PATH=%{buildroot}%{_libdir}${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
PYTHONPATH=%{buildroot}%{python3_sitearch} python -c 'from rocisa import rocIsa; print(rocIsa)'

%files
%license LICENSE.md
%{python3_sitearch}/rocisa/
