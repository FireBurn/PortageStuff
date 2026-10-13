//! What LLVM's libc defines differently from glibc on x86_64.
//!
//! The x86_64-unknown-linux-llvmlibc target builds the way the gnu target
//! does and sets target_abi = "llvmlibc". Each item here stands in for a
//! glibc definition that cfg(not(target_abi = "llvmlibc")) keeps away from
//! that target. Paths start from the crate root, so that the file reads the
//! same in every version of the crate it is added to.

s! {
    // The kernel's signal set, a single word, rather than glibc's 1024 bits.
    pub struct sigset_t {
        __val: [crate::c_ulong; 1],
    }

    // st_mode comes before st_nlink, and the block size and count come last.
    pub struct stat {
        pub st_dev: crate::dev_t,
        pub st_ino: crate::ino_t,
        pub st_mode: crate::mode_t,
        __pad0: crate::c_int,
        pub st_nlink: crate::nlink_t,
        pub st_uid: crate::uid_t,
        pub st_gid: crate::gid_t,
        pub st_rdev: crate::dev_t,
        pub st_size: crate::off_t,
        pub st_atime: crate::time_t,
        pub st_atime_nsec: i64,
        pub st_mtime: crate::time_t,
        pub st_mtime_nsec: i64,
        pub st_ctime: crate::time_t,
        pub st_ctime_nsec: i64,
        pub st_blksize: crate::blksize_t,
        pub st_blocks: crate::blkcnt_t,
    }

    pub struct stat64 {
        pub st_dev: crate::dev_t,
        pub st_ino: crate::ino64_t,
        pub st_mode: crate::mode_t,
        __pad0: crate::c_int,
        pub st_nlink: crate::nlink_t,
        pub st_uid: crate::uid_t,
        pub st_gid: crate::gid_t,
        pub st_rdev: crate::dev_t,
        pub st_size: crate::off64_t,
        pub st_atime: crate::time_t,
        pub st_atime_nsec: i64,
        pub st_mtime: crate::time_t,
        pub st_mtime_nsec: i64,
        pub st_ctime: crate::time_t,
        pub st_ctime_nsec: i64,
        pub st_blksize: crate::blksize_t,
        pub st_blocks: crate::blkcnt64_t,
    }

    // In the order the C standard lists the members.
    pub struct lconv {
        pub decimal_point: *mut crate::c_char,
        pub thousands_sep: *mut crate::c_char,
        pub grouping: *mut crate::c_char,
        pub mon_decimal_point: *mut crate::c_char,
        pub mon_thousands_sep: *mut crate::c_char,
        pub mon_grouping: *mut crate::c_char,
        pub positive_sign: *mut crate::c_char,
        pub negative_sign: *mut crate::c_char,
        pub currency_symbol: *mut crate::c_char,
        pub frac_digits: crate::c_char,
        pub p_cs_precedes: crate::c_char,
        pub n_cs_precedes: crate::c_char,
        pub p_sep_by_space: crate::c_char,
        pub n_sep_by_space: crate::c_char,
        pub p_sign_posn: crate::c_char,
        pub n_sign_posn: crate::c_char,
        pub int_curr_symbol: *mut crate::c_char,
        pub int_frac_digits: crate::c_char,
        pub int_p_cs_precedes: crate::c_char,
        pub int_n_cs_precedes: crate::c_char,
        pub int_p_sep_by_space: crate::c_char,
        pub int_n_sep_by_space: crate::c_char,
        pub int_p_sign_posn: crate::c_char,
        pub int_n_sign_posn: crate::c_char,
    }

    // LLVM's libc gives each member its own field and puts the value third.
    // It converts to the kernel's layout itself before a system call.
    #[allow(unpredictable_function_pointer_comparisons)]
    pub struct sigevent {
        pub sigev_notify: crate::c_int,
        pub sigev_signo: crate::c_int,
        pub sigev_value: crate::sigval,
        pub sigev_notify_function: ::core::option::Option<extern "C" fn(crate::sigval)>,
        pub sigev_notify_attributes: *mut crate::pthread_attr_t,
        pub sigev_notify_thread_id: crate::pid_t,
    }

    pub struct pthread_barrier_t {
        size: [u8; crate::__SIZEOF_PTHREAD_BARRIER_T],
        __align: [u64; 0],
    }

    pub struct pthread_condattr_t {
        size: [u8; crate::__SIZEOF_PTHREAD_CONDATTR_T],
        __align: [crate::c_int; 0],
    }
}

pub type regoff_t = isize;
pub type nfds_t = crate::c_uint;
// A byte for the lock and the owner's thread id.
pub type pthread_spinlock_t = i64;

pub const __SIZEOF_PTHREAD_BARRIER_T: usize = 88;
pub const __SIZEOF_PTHREAD_CONDATTR_T: usize = 8;

// A condition variable waits against CLOCK_REALTIME unless told otherwise,
// and LLVM's libc records that in a byte of the variable itself.
pub const PTHREAD_COND_INITIALIZER: crate::pthread_cond_t = {
    let mut bytes = [0u8; crate::__SIZEOF_PTHREAD_COND_T];
    bytes[21] = 1;
    unsafe { ::core::mem::transmute::<[u8; crate::__SIZEOF_PTHREAD_COND_T], crate::pthread_cond_t>(bytes) }
};

pub const PTHREAD_MUTEX_ERRORCHECK: crate::c_int = 1;
pub const PTHREAD_MUTEX_RECURSIVE: crate::c_int = 2;

pub const REG_NOSUB: crate::c_int = 4;
pub const REG_NEWLINE: crate::c_int = 8;

pub const LC_ALL_MASK: crate::c_int = 0x7fffffff;

pub const BUFSIZ: crate::c_uint = 1024;

pub const _PC_FILESIZEBITS: crate::c_int = 0;
pub const _PC_LINK_MAX: crate::c_int = 1;
pub const _PC_MAX_CANON: crate::c_int = 2;
pub const _PC_MAX_INPUT: crate::c_int = 3;
pub const _PC_NAME_MAX: crate::c_int = 4;
pub const _PC_PATH_MAX: crate::c_int = 5;
pub const _PC_PIPE_BUF: crate::c_int = 6;
pub const _PC_2_SYMLINKS: crate::c_int = 7;
pub const _PC_ALLOC_SIZE_MIN: crate::c_int = 8;
pub const _PC_REC_INCR_XFER_SIZE: crate::c_int = 9;
pub const _PC_REC_MAX_XFER_SIZE: crate::c_int = 10;
pub const _PC_REC_MIN_XFER_SIZE: crate::c_int = 11;
pub const _PC_REC_XFER_ALIGN: crate::c_int = 12;
pub const _PC_SYMLINK_MAX: crate::c_int = 13;
pub const _PC_CHOWN_RESTRICTED: crate::c_int = 14;
pub const _PC_NO_TRUNC: crate::c_int = 15;
pub const _PC_VDISABLE: crate::c_int = 16;
pub const _PC_ASYNC_IO: crate::c_int = 17;
pub const _PC_PRIO_IO: crate::c_int = 18;
pub const _PC_SYNC_IO: crate::c_int = 19;
// LLVM's libc has no such name, and glibc's number for it is LLVM's
// _PC_REC_XFER_ALIGN, so it is given one that pathconf refuses.
pub const _PC_SOCK_MAXBUF: crate::c_int = -1;
