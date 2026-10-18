# Wine, Proton and the Direct3D translation layers are built with clang, -O3,
# -march=native and thin LTO. Their ebuilds and eclasses change the flags with
# filter-flags, filter-lto, strip-flags, replace-flags and append-flags, so after
# each of those the optimisation level, -march and thin LTO are put back.
# Nothing else on this machine is touched, it keeps the flags of make.conf.
_wine_pkg() {
	case ${CATEGORY}/${PN} in
	app-emulation/wine-vanilla|app-emulation/wine-staging|app-emulation/proton-ge-custom|\
	app-emulation/dxvk|app-emulation/vkd3d-proton) return 0 ;;
	esac
	return 1
}
_restore_user_flags() {
	local v f
	for v in CFLAGS CXXFLAGS; do
		local -a out=()
		for f in ${!v}; do
			case ${f} in
			-O[0-9sgz]|-Ofast|-march=*|-flto|-flto=*) ;;
			# the ebuilds add it for mingw GCC, clang does not need it
			-mno-avx) [[ ${PN} == dxvk || ${PN} == vkd3d-proton ]] || out+=("${f}") ;;
			*) out+=("${f}") ;;
			esac
		done
		export "${v}=-O3 -march=native -flto=thin ${out[*]}"
	done
}
_wrap_flag_function() {
	declare -F "$1" >/dev/null || return 0
	declare -F "_orig_$1" >/dev/null && return 0
	eval "_orig_$(declare -f "$1")"
	eval "$1() { _orig_$1 \"\$@\"; local r=\$?; _restore_user_flags; return \$r; }"
}
_force_user_flags() {
	_wine_pkg || return 0
	local f
	for f in filter-flags filter-lto strip-flags replace-flags replace-cpu-flags \
		append-flags append-cflags append-cxxflags; do
		_wrap_flag_function "${f}"
	done
}
pre_pkg_setup() { _force_user_flags; }
pre_src_unpack() { _force_user_flags; }
pre_src_prepare() { _force_user_flags; }
pre_src_configure() { _force_user_flags; }
pre_src_compile() {
	_force_user_flags
	# wine-preloader is linked static at 0x7d7d00000000, above 4GB. With LTO the
	# code is generated at link time, and for a non-PIE link that means the static
	# relocation model and 32-bit absolute addresses, which cannot reach it.
	# makedep writes the preloader link into the Makefile with the flags already
	# expanded, so the flag goes on the line that sets the address.
	if [[ -n ${WINE_PRELOADER_PIC} && -f ${BUILD_DIR:-${S}}/Makefile ]]; then
		sed -i 's/\( -Wl,-Ttext=0x[0-9a-f]*\)$/\1 -Wl,-mllvm,-relocation-model=pic/' \
			"${BUILD_DIR:-${S}}/Makefile" || die
	fi
}
pre_src_install() { _force_user_flags; }
