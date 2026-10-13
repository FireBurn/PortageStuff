# Keeps the tests out of LTO, or they inline the library and fold what they check.
set(LIBC_TEST_COMPILE_OPTIONS_DEFAULT "-fno-lto" CACHE STRING "" FORCE)
