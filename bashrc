# rustc calls this libc's target x86_64-unknown-linux-llvmlibc, but CHOST
# says gnu, so rust_abi is wrapped once the eclasses defining it are sourced.
pre_pkg_setup() {
	_force_user_flags
	declare -F rust_abi >/dev/null || return 0
	declare -F _gentoo_rust_abi >/dev/null ||
		eval "_gentoo_$(declare -f rust_abi)"
	rust_abi() {
		local abi
		abi=$(_gentoo_rust_abi "$@")
		[[ ${abi} == x86_64-unknown-linux-gnu ]] &&
			abi=x86_64-unknown-linux-llvmlibc
		echo "${abi}"
	}
}

# BEGIN llvmlibc crates
# The libc crate already gives x86_64-unknown-linux-llvmlibc the right types, the
# cc crate would hand clang a triple it does not know, and target-lexicon
# refuses to parse the triple at all, so each copy of any of them a package
# unpacks is told about this libc first.
post_src_unpack() {
	local crate script name
	while IFS= read -r -d '' crate; do
		case ${crate##*/} in
		cc|cc-1.*) script=cc-crate-llvmlibc.py name=cc ;;
		target-lexicon|target-lexicon-0.*) script=target-lexicon-crate-llvmlibc.py name=target-lexicon ;;
		*) continue ;;
		esac
		grep -qx "name = \"${name}\"" "${crate}/Cargo.toml" 2>/dev/null || continue
		[[ ${name} != libc ]] ||
			grep -q "^version = \"0\.2\." "${crate}/Cargo.toml" || continue
		"${EPREFIX}"/usr/bin/python3 "${EPREFIX}/etc/portage/llvmlibc/${script}" \
			"${crate}" || die "could not adapt ${crate} to this libc"
	done < <(find "${WORKDIR}" -maxdepth 7 -type d \
		\( -name libc -o -name 'libc-0.2.*' -o -name cc -o -name 'cc-1.*' \
		   -o -name target-lexicon -o -name 'target-lexicon-0.*' \) \
		-print0)
}
# END llvmlibc crates

# The flags of make.conf are the ones to build with. Ebuilds change them with
# filter-flags, strip-flags, replace-flags, filter-lto and append-flags, so
# after each of those the optimisation level, -march and thin LTO are put
# back. A package that does its own LTO through its build system sets
# LTO_SELF and keeps -flto out of CFLAGS, the rest still apply.
_restore_user_flags() {
	local v f flag
	for v in CFLAGS CXXFLAGS FCFLAGS FFLAGS; do
		local -a out=()
		for f in ${!v}; do
			case ${f} in
			-O[0-9sgz]|-Ofast|-march=*|-flto|-flto=*) ;;
			*) out+=("${f}") ;;
			esac
		done
		flag="-O3 -march=native"
		[[ -n ${LTO_SELF} ]] || flag+=" -flto=thin"
		export "${v}=${flag} ${out[*]}"
	done
}
_wrap_flag_function() {
	declare -F "$1" >/dev/null || return 0
	declare -F "_orig_$1" >/dev/null && return 0
	eval "_orig_$(declare -f "$1")"
	eval "$1() { _orig_$1 \"\$@\"; local r=\$?; _restore_user_flags; return \$r; }"
}
_force_user_flags() {
	[[ -n ${NO_FORCE_FLAGS} ]] && return 0
	local f
	for f in filter-flags filter-lto strip-flags replace-flags replace-cpu-flags \
		append-flags append-cflags append-cxxflags; do
		_wrap_flag_function "${f}"
	done
}
pre_src_unpack() { _force_user_flags; }
pre_src_prepare() { _force_user_flags; }
pre_src_configure() { _force_user_flags; }
pre_src_compile() {
	_force_user_flags
	# Mozilla's elfhack linker wrapper aborts with "Not ELF?" on the bitcode
	# objects of its own LTO, so it is turned off in the generated mozconfig.
	# makedep writes the preloader link into the Makefile with the flags
	# already expanded, so the flag goes on the line that sets the address.
	if [[ -n ${WINE_PRELOADER_PIC} && -f ${BUILD_DIR:-${S}}/Makefile ]]; then
		sed -i 's/^\( *-Wl,-Ttext=0x[0-9a-f]*\)$/\1 -Wl,-mllvm,-relocation-model=pic/' \
			"${BUILD_DIR:-${S}}/Makefile" || die
	fi
	if [[ -n ${MOZ_NO_ELFHACK} && -f ${S}/.mozconfig ]]; then
		sed -i 's/^ac_add_options --enable-elf-hack=relr.*/ac_add_options --disable-elf-hack # elfhack aborts on LTO objects/' \
			"${S}/.mozconfig" || die
	fi
}
pre_src_install() { _force_user_flags; }
