s/\(.*\)#ENDIF#\(.*\)/\2\1#ENDIF#/g
s/^CONFIG_ARCH=\(.*\)/CONFIG_ARCH=x86_64/g
s/^TAU_ARCH=\(.*\)/TAU_ARCH=x86_64/g
s@^CONFIG_CC=\(.*\)@CONFIG_CC=gcc@g
s@^CONFIG_CXX=\(.*\)@CONFIG_CXX=g++@g
s@^USER_OPT=\(.*\)@USER_OPT=-O2 -g@g
s@^EXTRADIR=\(.*\)@EXTRADIR=@g
s@^EXTRADIRCXX=\(.*\)@EXTRADIRCXX=@g
s@^TAUEXTRASHLIBOPTS=\(.*\)@TAUEXTRASHLIBOPTS=@g
s;^TAU_PREFIX_INSTALL_DIR=\(.*\);TAU_PREFIX_INSTALL_DIR=/lustre/ssinghal/tau2-install;g
s@^CONF_ENV_FILE=\(.*\)@CONF_ENV_FILE=/homes/ssinghal/tau-2.28.1/.configure_env/629117fbe7a375552f04b73a8e3b1e39@g
s@^TAUROOT=\(.*\)@TAUROOT=/homes/ssinghal/tau-2.28.1@g
s/#ARCH_WIDTH_64#\(.*\)/\1#ARCH_WIDTH_64#/g
s/#PROFILE#\(.*\)/\1#PROFILE#/g
s/#IOWRAPPER#\(.*\)/\1#IOWRAPPER#/g
s@^TAU_MPI_LIB=\(.*\)@TAU_MPI_LIB=-L/lustre/ssinghal/tau2-install/x86_64/lib -lTauMpi$(TAU_CONFIG) -I/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/include -pthread -L/usr/local/ofed/1.5.4.1/lib -L/cell_root/software/gcc/6.1.0/sys/lib64 -Wl,-rpath,/cell_root/software/gcc/6.1.0/sys/lib64 -L/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -Wl,-rpath,/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -L/usr/local/ofed/1.5.4.1/lib64 -Wl,-rpath,/usr/local/ofed/1.5.4.1/lib64 -Wl,-rpath -Wl,/usr/local/ofed/1.5.4.1/lib -Wl,-rpath -Wl,/cell_root/software/gcc/6.1.0/sys/lib64 -Wl,-rpath -Wl,/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -Wl,-rpath -Wl,/usr/local/ofed/1.5.4.1/lib64 -Wl,-rpath -Wl,/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -L/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -lmpi_cxx -lmpi@g
s@^TAU_MPI_FLIB=\(.*\)@TAU_MPI_FLIB=-L/lustre/ssinghal/tau2-install/x86_64/lib -lTauMpi$(TAU_CONFIG) -I/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/include -pthread -I/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -L/usr/local/ofed/1.5.4.1/lib -L/cell_root/software/gcc/6.1.0/sys/lib64 -Wl,-rpath,/cell_root/software/gcc/6.1.0/sys/lib64 -L/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -Wl,-rpath,/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -L/usr/local/ofed/1.5.4.1/lib64 -Wl,-rpath,/usr/local/ofed/1.5.4.1/lib64 -Wl,-rpath -Wl,/usr/local/ofed/1.5.4.1/lib -Wl,-rpath -Wl,/cell_root/software/gcc/6.1.0/sys/lib64 -Wl,-rpath -Wl,/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -Wl,-rpath -Wl,/usr/local/ofed/1.5.4.1/lib64 -Wl,-rpath -Wl,/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -L/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -lmpi_usempif08 -lmpi_usempi_ignore_tkr -lmpi_mpifh -lmpi@g
s@^FULL_CXX=.*@FULL_CXX=g++@g
s@^FULL_CC=.*@FULL_CC=gcc@g
s,^TAUGFORTRANLIBDIR=.*$,TAUGFORTRANLIBDIR=/afs/glue.umd.edu/software/gcc/6.1.0/.@sys/bin/../lib/gcc/x86_64-pc-linux-gnu/6.1.0/,g
s/#GNU_GFORTRAN#\(.*\)/\1#GNU_GFORTRAN#/g
s@^FULL_CXX=.*@FULL_CXX=g++@g
s@^FULL_CC=.*@FULL_CC=gcc@g
s@^TAU_MPI_INC=\(.*\)@TAU_MPI_INC=-I/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/include -I/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/include/openmpi -I/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/include/openmpi/ompi -I/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib@g
s/#PAPI#\(.*\)/\1#PAPI#/g
s,^PAPIDIR=.*$,PAPIDIR=/lustre/ssinghal/papi-install,g
s,^PAPISUBDIR=.*$,PAPISUBDIR=lib,g
s/#PAPIPFM#\(.*\)/\1#PAPIPFM#/g
s/#GNU46PLUS#\(.*\)/\1#GNU46PLUS#/g
s/#GNU#\(.*\)/\1#GNU#/g
s/#COMPINST_GNU#\(.*\)/\1#COMPINST_GNU#/g
s,^TAUGCCLIBDIR=.*$,TAUGCCLIBDIR=/afs/glue.umd.edu/software/gcc/6.1.0/.@sys/bin/../lib/gcc/x86_64-pc-linux-gnu/6.1.0/,g
s,^TAUGCCSTDCXXLIBDIR=.*$,TAUGCCSTDCXXLIBDIR=/afs/glue.umd.edu/software/gcc/6.1.0/.@sys/bin/../lib/gcc/x86_64-pc-linux-gnu/6.1.0/../../../../lib64/,g
s/#LD_AUDITOR_AVAILABLE#\(.*\)/\1#LD_AUDITOR_AVAILABLE#/g
s/#X86_64PAPI_NEW#\(.*\)/\1#X86_64PAPI_NEW#/g
s/#LINUXTIMERS#\(.*\)/\1#LINUXTIMERS#/g
s/#MPI#\(.*\)/\1#MPI#/g
s/#MPI_THREADED#\(.*\)/\1#MPI_THREADED#/g
s/#MPICH3_CONST#\(.*\)/\1#MPICH3_CONST#/g
s/#MPI2#\(.*\)/\1#MPI2#/g
s/#MPIGREQUEST#\(.*\)/\1#MPIGREQUEST#/g
s/#MPIDATAREP#\(.*\)/\1#MPIDATAREP#/g
s/#MPIERRHANDLER#\(.*\)/\1#MPIERRHANDLER#/g
s/#MPICONSTCHAR#\(.*\)/\1#MPICONSTCHAR#/g
s/#MPIATTR#\(.*\)/\1#MPIATTR#/g
s/#MPIFILE#\(.*\)/\1#MPIFILE#/g
s/#MPITYPEEX#\(.*\)/\1#MPITYPEEX#/g
s/#MPIADDERROR#\(.*\)/\1#MPIADDERROR#/g
s@^TAU_MPI_LIB=\(.*\)@TAU_MPI_LIB=-L/lustre/ssinghal/tau2-install/x86_64/lib -lTauMpi$(TAU_CONFIG) -L/lustre/ssinghal/tau2-install/x86_64/lib -lTauMpi$(TAU_CONFIG) -I/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/include -pthread -L/usr/local/ofed/1.5.4.1/lib -L/cell_root/software/gcc/6.1.0/sys/lib64 -Wl,-rpath,/cell_root/software/gcc/6.1.0/sys/lib64 -L/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -Wl,-rpath,/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -L/usr/local/ofed/1.5.4.1/lib64 -Wl,-rpath,/usr/local/ofed/1.5.4.1/lib64 -Wl,-rpath -Wl,/usr/local/ofed/1.5.4.1/lib -Wl,-rpath -Wl,/cell_root/software/gcc/6.1.0/sys/lib64 -Wl,-rpath -Wl,/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -Wl,-rpath -Wl,/usr/local/ofed/1.5.4.1/lib64 -Wl,-rpath -Wl,/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -L/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -lmpi_cxx -lmpi -L/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -lmpi -lmpi_cxx -Wl,-rpath,$(TAU_MPILIB_DIR)@g
s@^TAU_MPI_FLIB=\(.*\)@TAU_MPI_FLIB=-L/lustre/ssinghal/tau2-install/x86_64/lib -lTauMpi$(TAU_CONFIG) -I/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/include -pthread -I/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -L/usr/local/ofed/1.5.4.1/lib -L/cell_root/software/gcc/6.1.0/sys/lib64 -Wl,-rpath,/cell_root/software/gcc/6.1.0/sys/lib64 -L/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -Wl,-rpath,/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -L/usr/local/ofed/1.5.4.1/lib64 -Wl,-rpath,/usr/local/ofed/1.5.4.1/lib64 -Wl,-rpath -Wl,/usr/local/ofed/1.5.4.1/lib -Wl,-rpath -Wl,/cell_root/software/gcc/6.1.0/sys/lib64 -Wl,-rpath -Wl,/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -Wl,-rpath -Wl,/usr/local/ofed/1.5.4.1/lib64 -Wl,-rpath -Wl,/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -L/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -lmpi_usempif08 -lmpi_usempi_ignore_tkr -lmpi_mpifh -lmpi -L/lustre/ssinghal/tau2-install/x86_64/lib -lTauMpi$(TAU_CONFIG) -L/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -lmpi -lmpi_cxx -Wl,-rpath,$(TAU_MPILIB_DIR)@g
s@^TAU_MPILIB_DIR=\(.*\)@TAU_MPILIB_DIR=/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib@g
s@^TAU_MPILIB_DIRLIB=\(.*\)@TAU_MPILIB_DIRLIB=-L/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib@g
s@^TAU_MPI_NOWRAP_LIB=\(.*\)@TAU_MPI_NOWRAP_LIB= -L/lustre/ssinghal/tau2-install/x86_64/lib -lTauMpi$(TAU_CONFIG) -I/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/include -pthread -L/usr/local/ofed/1.5.4.1/lib -L/cell_root/software/gcc/6.1.0/sys/lib64 -Wl,-rpath,/cell_root/software/gcc/6.1.0/sys/lib64 -L/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -Wl,-rpath,/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -L/usr/local/ofed/1.5.4.1/lib64 -Wl,-rpath,/usr/local/ofed/1.5.4.1/lib64 -Wl,-rpath -Wl,/usr/local/ofed/1.5.4.1/lib -Wl,-rpath -Wl,/cell_root/software/gcc/6.1.0/sys/lib64 -Wl,-rpath -Wl,/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -Wl,-rpath -Wl,/usr/local/ofed/1.5.4.1/lib64 -Wl,-rpath -Wl,/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -L/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -lmpi_cxx -lmpi -L/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -lmpi -lmpi_cxx -Wl,-rpath,$(TAU_MPILIB_DIR)@g
s@^TAU_MPI_NOWRAP_FLIB=\(.*\)@TAU_MPI_NOWRAP_FLIB= -I/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/include -pthread -I/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -L/usr/local/ofed/1.5.4.1/lib -L/cell_root/software/gcc/6.1.0/sys/lib64 -Wl,-rpath,/cell_root/software/gcc/6.1.0/sys/lib64 -L/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -Wl,-rpath,/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -L/usr/local/ofed/1.5.4.1/lib64 -Wl,-rpath,/usr/local/ofed/1.5.4.1/lib64 -Wl,-rpath -Wl,/usr/local/ofed/1.5.4.1/lib -Wl,-rpath -Wl,/cell_root/software/gcc/6.1.0/sys/lib64 -Wl,-rpath -Wl,/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -Wl,-rpath -Wl,/usr/local/ofed/1.5.4.1/lib64 -Wl,-rpath -Wl,/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -L/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -lmpi_usempif08 -lmpi_usempi_ignore_tkr -lmpi_mpifh -lmpi -L/lustre/ssinghal/tau2-install/x86_64/lib -lTauMpi$(TAU_CONFIG) -L/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib -lmpi -lmpi_cxx -Wl,-rpath,$(TAU_MPILIB_DIR)@g
s@^TAU_MPILIB_DIR=\(.*\)@TAU_MPILIB_DIR=/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib@g
s@^TAU_MPILIB_DIRLIB=\(.*\)@TAU_MPILIB_DIRLIB=-L/cell_root/software/openmpi/1.10.2/gnu/6.1.0/threaded/sys/lib@g
s/#MPI_R_SUFFIX#\(.*\)/\1#MPI_R_SUFFIX#/g
s/#TAU_STRSIGNAL_OK#\(.*\)/\1#TAU_STRSIGNAL_OK#/g
s/#TAU_LARGEFILE#\(.*\)/\1#TAU_LARGEFILE#/g
s/#TAU_WEAK_SUPPORTED#\(.*\)/\1#TAU_WEAK_SUPPORTED#/g
s,^BFDINCLUDE=.*$,BFDINCLUDE=-I/lustre/ssinghal/tau2-install/x86_64/binutils-2.23.2/include -I/lustre/ssinghal/tau2-install/x86_64/binutils-2.23.2/include/extra,g
s,^BFDLINK=.*$,BFDLINK=-L/lustre/ssinghal/tau2-install/x86_64/binutils-2.23.2/lib -L/lustre/ssinghal/tau2-install/x86_64/binutils-2.23.2/lib64 -Wl\,-rpath\,/lustre/ssinghal/tau2-install/x86_64/binutils-2.23.2/lib -Wl\,-rpath\,/lustre/ssinghal/tau2-install/x86_64/binutils-2.23.2/lib64,g
s/#TAU_BFD#\(.*\)/\1#TAU_BFD#/g
s/#TAU_ELF_BFD#\(.*\)/\1#TAU_ELF_BFD#/g
s,^BFDLIBS=.*$,BFDLIBS=-lbfd -liberty -lz -ldl,g
s/#TAU_DEMANGLE#\(.*\)/\1#TAU_DEMANGLE#/g
s/#TAU_BFDSHAREDLINK#\(.*\)/\1#TAU_BFDSHAREDLINK#/g
s/#TAU_SS_ALLOC_SUPPORT#\(.*\)/\1#TAU_SS_ALLOC_SUPPORT#/g
s/#TAU_LINKS_RT#\(.*\)/\1#TAU_LINKS_RT#/g
s/#TAU_TR1_HASH_MAP#\(.*\)/\1#TAU_TR1_HASH_MAP#/g
s/#TAU_PTHREAD_WRAP#\(.*\)/\1#TAU_PTHREAD_WRAP#/g
s/#TLS_AVAILABLE#\(.*\)/\1#TLS_AVAILABLE#/g
s/#PTHREAD_AVAILABLE#\(.*\)/\1#PTHREAD_AVAILABLE#/g
s,^PTDIR=.*$,PTDIR=,g
s/#PYTHON#\(.*\)/\1#PYTHON#/g
s,^PYTHON_INCDIR=.*$,PYTHON_INCDIR=/usr/local/python3/3.5.1/bin/../include/python3.5m,g
s,^PYTHON_LIBDIR=.*$,PYTHON_LIBDIR=/usr/local/python3/3.5.1/bin/../lib/python3.5/..,g
s,^PYTHON_LIB_SO=.*$,PYTHON_LIB_SO=python3.5m,g
s/#TAU_UNWIND#\(.*\)/\1#TAU_UNWIND#/g
s/#TAU_UNWIND_LIBUNWIND#\(.*\)/\1#TAU_UNWIND_LIBUNWIND#/g
s,^UNWIND_FLAG=.*$,UNWIND_FLAG=-DTAU_USE_LIBUNWIND,g
s,^UNWIND_INC=.*$,UNWIND_INC=/lustre/ssinghal/tau2-install/x86_64/libunwind-1.3.1-gcc/include,g
s,^UNWIND_LIB=.*$,UNWIND_LIB=/lustre/ssinghal/tau2-install/x86_64/libunwind-1.3.1-gcc/lib,g
s@^UNWIND_LIB_FLAG=\(.*\)@UNWIND_LIB_FLAG=-lunwind -Wl,-rpath,$(UNWIND_LIB)@g
s,^UNWIND_EXTRAS=.*$,UNWIND_EXTRAS=-Wl\,-rpath=/lustre/ssinghal/tau2-install/x86_64/libunwind-1.3.1-gcc/lib,g
s/#EBS_HAS_RT#\(.*\)/\1#EBS_HAS_RT#/g
s,^EBS_CLOCK_RES=.*$,EBS_CLOCK_RES=1,g
s,^OTFLIB=.*$,OTFLIB=/lustre/ssinghal/tau2-install/x86_64/otf2-gcc/lib,g
s,^OTFINC=.*$,OTFINC=/lustre/ssinghal/tau2-install/x86_64/otf2-gcc/include,g
s/#OTF2#\(.*\)/\1#OTF2#/g
s,^OTFDIR=.*$,OTFDIR=/lustre/ssinghal/tau2-install/x86_64/otf2-gcc,g
s/#ADIOS2#\(.*\)/\1#ADIOS2#/g
s,^ADIOS2DIR=.*$,ADIOS2DIR=/lustre/ssinghal/ADIOS2-install,g
s,^ADIOS2_CXXFLAGS=.*$,ADIOS2_CXXFLAGS=-isystem /lustre/ssinghal/ADIOS2-install/include -std=gnu++11,g
s,^ADIOS2_LIBS=.*$,ADIOS2_LIBS=-L/lustre/ssinghal/ADIOS2-install/lib -ladios2,g
s/#PAPIPTHREAD#\(.*\)/\1#PAPIPTHREAD#/g
s@^EXTRA_LINKER_ARGS=.*$@EXTRA_LINKER_ARGS= -Wl,--export-dynamic@g
s@^TAU_CONFIG=\(.*\)@TAU_CONFIG=-papi-mpi-pthread-python-adios2@g
