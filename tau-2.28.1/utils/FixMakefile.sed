s/\(.*\)#ENDIF#\(.*\)/\2\1#ENDIF#/g
s/^CONFIG_ARCH=\(.*\)/CONFIG_ARCH=ibm64linux/g
s/^TAU_ARCH=\(.*\)/TAU_ARCH=ibm64linux/g
s@^CONFIG_CC=\(.*\)@CONFIG_CC=gcc@g
s@^CONFIG_CXX=\(.*\)@CONFIG_CXX=g++@g
s@^USER_OPT=\(.*\)@USER_OPT=-O2 -g@g
s@^EXTRADIR=\(.*\)@EXTRADIR=@g
s@^EXTRADIRCXX=\(.*\)@EXTRADIRCXX=@g
s@^TAUEXTRASHLIBOPTS=\(.*\)@TAUEXTRASHLIBOPTS=@g
s;^TAU_PREFIX_INSTALL_DIR=\(.*\);TAU_PREFIX_INSTALL_DIR=/ccs/home/ssinghal/tau2-install;g
s@^CONF_ENV_FILE=\(.*\)@CONF_ENV_FILE=/gpfs/alpine/scratch/ssinghal/csc143/Dynamic_workflow_management/tau-2.28.1/.configure_env/b9491ba4d6d24e501219ecc7a95da57b@g
s@^TAUROOT=\(.*\)@TAUROOT=/gpfs/alpine/scratch/ssinghal/csc143/Dynamic_workflow_management/tau-2.28.1@g
s/#ARCH_WIDTH_64#\(.*\)/\1#ARCH_WIDTH_64#/g
s/#PROFILE#\(.*\)/\1#PROFILE#/g
s/#IOWRAPPER#\(.*\)/\1#IOWRAPPER#/g
s@^TAU_MPI_LIB=\(.*\)@TAU_MPI_LIB=-L/ccs/home/ssinghal/tau2-install/ibm64linux/lib -lTauMpi$(TAU_CONFIG) -I/autofs/nccs-svm1_sw/summit/.swci/1-compute/opt/spack/20180914/linux-rhel7-ppc64le/gcc-6.4.0/spectrum-mpi-10.3.0.0-20190419-4um5hjogm3tepg4xe23hrptlrs2y7ez6/include -pthread -L/autofs/nccs-svm1_sw/summit/.swci/1-compute/opt/spack/20180914/linux-rhel7-ppc64le/gcc-6.4.0/spectrum-mpi-10.3.0.0-20190419-4um5hjogm3tepg4xe23hrptlrs2y7ez6/lib -lmpiprofilesupport -lmpi_ibm@g
s@^TAU_MPI_FLIB=\(.*\)@TAU_MPI_FLIB=-L/ccs/home/ssinghal/tau2-install/ibm64linux/lib -lTauMpi$(TAU_CONFIG) -I/autofs/nccs-svm1_sw/summit/.swci/1-compute/opt/spack/20180914/linux-rhel7-ppc64le/gcc-6.4.0/spectrum-mpi-10.3.0.0-20190419-4um5hjogm3tepg4xe23hrptlrs2y7ez6/include -pthread -I/autofs/nccs-svm1_sw/summit/.swci/1-compute/opt/spack/20180914/linux-rhel7-ppc64le/gcc-6.4.0/spectrum-mpi-10.3.0.0-20190419-4um5hjogm3tepg4xe23hrptlrs2y7ez6/lib -L/autofs/nccs-svm1_sw/summit/.swci/1-compute/opt/spack/20180914/linux-rhel7-ppc64le/gcc-6.4.0/spectrum-mpi-10.3.0.0-20190419-4um5hjogm3tepg4xe23hrptlrs2y7ez6/lib -lmpiprofilesupport -lmpi_ibm_usempi -lmpi_ibm_mpifh -lmpi_ibm@g
s@^FULL_CXX=.*@FULL_CXX=g++@g
s@^FULL_CC=.*@FULL_CC=gcc@g
s,^TAUGFORTRANLIBDIR=.*$,TAUGFORTRANLIBDIR=/autofs/nccs-svm1_sw/summit/gcc/6.4.0/bin/../lib/gcc/powerpc64le-none-linux-gnu/6.4.0/,g
s/#GNU_GFORTRAN#\(.*\)/\1#GNU_GFORTRAN#/g
s@^FULL_CXX=.*@FULL_CXX=g++@g
s@^FULL_CC=.*@FULL_CC=gcc@g
s@^TAU_MPI_INC=\(.*\)@TAU_MPI_INC=-I/autofs/nccs-svm1_sw/summit/.swci/1-compute/opt/spack/20180914/linux-rhel7-ppc64le/gcc-6.4.0/spectrum-mpi-10.3.0.0-20190419-4um5hjogm3tepg4xe23hrptlrs2y7ez6/include -I/autofs/nccs-svm1_sw/summit/.swci/1-compute/opt/spack/20180914/linux-rhel7-ppc64le/gcc-6.4.0/spectrum-mpi-10.3.0.0-20190419-4um5hjogm3tepg4xe23hrptlrs2y7ez6/lib@g
s/#PAPI#\(.*\)/\1#PAPI#/g
s,^PAPIDIR=.*$,PAPIDIR=/ccs/home/ssinghal/papi_install,g
s,^PAPISUBDIR=.*$,PAPISUBDIR=lib,g
s/#PAPIPFM#\(.*\)/\1#PAPIPFM#/g
s/#GNU46PLUS#\(.*\)/\1#GNU46PLUS#/g
s/#GNU#\(.*\)/\1#GNU#/g
s/#COMPINST_GNU#\(.*\)/\1#COMPINST_GNU#/g
s,^TAUGCCLIBDIR=.*$,TAUGCCLIBDIR=/autofs/nccs-svm1_sw/summit/gcc/6.4.0/bin/../lib/gcc/powerpc64le-none-linux-gnu/6.4.0/,g
s,^TAUGCCSTDCXXLIBDIR=.*$,TAUGCCSTDCXXLIBDIR=/sw/summit/gcc/6.4.0/lib64/../lib64/,g
s/#LD_AUDITOR_AVAILABLE#\(.*\)/\1#LD_AUDITOR_AVAILABLE#/g
s/#PPC64#\(.*\)/\1#PPC64#/g
s/#IBM64LINUX#\(.*\)/\1#IBM64LINUX#/g
s/#IBM64PAPILINUX#\(.*\)/\1#IBM64PAPILINUX#/g
s/#IBM64LINUX_XLC#\(.*\)/\1#IBM64LINUX_XLC#/g
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
s@^TAU_MPI_LIB=\(.*\)@TAU_MPI_LIB=-L/ccs/home/ssinghal/tau2-install/ibm64linux/lib -lTauMpi$(TAU_CONFIG) -L/ccs/home/ssinghal/tau2-install/ibm64linux/lib -lTauMpi$(TAU_CONFIG) -I/autofs/nccs-svm1_sw/summit/.swci/1-compute/opt/spack/20180914/linux-rhel7-ppc64le/gcc-6.4.0/spectrum-mpi-10.3.0.0-20190419-4um5hjogm3tepg4xe23hrptlrs2y7ez6/include -pthread -L/autofs/nccs-svm1_sw/summit/.swci/1-compute/opt/spack/20180914/linux-rhel7-ppc64le/gcc-6.4.0/spectrum-mpi-10.3.0.0-20190419-4um5hjogm3tepg4xe23hrptlrs2y7ez6/lib -lmpiprofilesupport -lmpi_ibm -L/autofs/nccs-svm1_sw/summit/.swci/1-compute/opt/spack/20180914/linux-rhel7-ppc64le/gcc-6.4.0/spectrum-mpi-10.3.0.0-20190419-4um5hjogm3tepg4xe23hrptlrs2y7ez6/lib -Wl,-rpath,$(TAU_MPILIB_DIR)@g
s@^TAU_MPI_FLIB=\(.*\)@TAU_MPI_FLIB=-L/ccs/home/ssinghal/tau2-install/ibm64linux/lib -lTauMpi$(TAU_CONFIG) -I/autofs/nccs-svm1_sw/summit/.swci/1-compute/opt/spack/20180914/linux-rhel7-ppc64le/gcc-6.4.0/spectrum-mpi-10.3.0.0-20190419-4um5hjogm3tepg4xe23hrptlrs2y7ez6/include -pthread -I/autofs/nccs-svm1_sw/summit/.swci/1-compute/opt/spack/20180914/linux-rhel7-ppc64le/gcc-6.4.0/spectrum-mpi-10.3.0.0-20190419-4um5hjogm3tepg4xe23hrptlrs2y7ez6/lib -L/autofs/nccs-svm1_sw/summit/.swci/1-compute/opt/spack/20180914/linux-rhel7-ppc64le/gcc-6.4.0/spectrum-mpi-10.3.0.0-20190419-4um5hjogm3tepg4xe23hrptlrs2y7ez6/lib -lmpiprofilesupport -lmpi_ibm_usempi -lmpi_ibm_mpifh -lmpi_ibm -L/ccs/home/ssinghal/tau2-install/ibm64linux/lib -lTauMpi$(TAU_CONFIG) -L/autofs/nccs-svm1_sw/summit/.swci/1-compute/opt/spack/20180914/linux-rhel7-ppc64le/gcc-6.4.0/spectrum-mpi-10.3.0.0-20190419-4um5hjogm3tepg4xe23hrptlrs2y7ez6/lib -Wl,-rpath,$(TAU_MPILIB_DIR)@g
s@^TAU_MPILIB_DIR=\(.*\)@TAU_MPILIB_DIR=/autofs/nccs-svm1_sw/summit/.swci/1-compute/opt/spack/20180914/linux-rhel7-ppc64le/gcc-6.4.0/spectrum-mpi-10.3.0.0-20190419-4um5hjogm3tepg4xe23hrptlrs2y7ez6/lib@g
s@^TAU_MPILIB_DIRLIB=\(.*\)@TAU_MPILIB_DIRLIB=-L/autofs/nccs-svm1_sw/summit/.swci/1-compute/opt/spack/20180914/linux-rhel7-ppc64le/gcc-6.4.0/spectrum-mpi-10.3.0.0-20190419-4um5hjogm3tepg4xe23hrptlrs2y7ez6/lib@g
s@^TAU_MPI_NOWRAP_LIB=\(.*\)@TAU_MPI_NOWRAP_LIB= -L/ccs/home/ssinghal/tau2-install/ibm64linux/lib -lTauMpi$(TAU_CONFIG) -I/autofs/nccs-svm1_sw/summit/.swci/1-compute/opt/spack/20180914/linux-rhel7-ppc64le/gcc-6.4.0/spectrum-mpi-10.3.0.0-20190419-4um5hjogm3tepg4xe23hrptlrs2y7ez6/include -pthread -L/autofs/nccs-svm1_sw/summit/.swci/1-compute/opt/spack/20180914/linux-rhel7-ppc64le/gcc-6.4.0/spectrum-mpi-10.3.0.0-20190419-4um5hjogm3tepg4xe23hrptlrs2y7ez6/lib -lmpiprofilesupport -lmpi_ibm -L/autofs/nccs-svm1_sw/summit/.swci/1-compute/opt/spack/20180914/linux-rhel7-ppc64le/gcc-6.4.0/spectrum-mpi-10.3.0.0-20190419-4um5hjogm3tepg4xe23hrptlrs2y7ez6/lib -Wl,-rpath,$(TAU_MPILIB_DIR)@g
s@^TAU_MPI_NOWRAP_FLIB=\(.*\)@TAU_MPI_NOWRAP_FLIB= -I/autofs/nccs-svm1_sw/summit/.swci/1-compute/opt/spack/20180914/linux-rhel7-ppc64le/gcc-6.4.0/spectrum-mpi-10.3.0.0-20190419-4um5hjogm3tepg4xe23hrptlrs2y7ez6/include -pthread -I/autofs/nccs-svm1_sw/summit/.swci/1-compute/opt/spack/20180914/linux-rhel7-ppc64le/gcc-6.4.0/spectrum-mpi-10.3.0.0-20190419-4um5hjogm3tepg4xe23hrptlrs2y7ez6/lib -L/autofs/nccs-svm1_sw/summit/.swci/1-compute/opt/spack/20180914/linux-rhel7-ppc64le/gcc-6.4.0/spectrum-mpi-10.3.0.0-20190419-4um5hjogm3tepg4xe23hrptlrs2y7ez6/lib -lmpiprofilesupport -lmpi_ibm_usempi -lmpi_ibm_mpifh -lmpi_ibm -L/ccs/home/ssinghal/tau2-install/ibm64linux/lib -lTauMpi$(TAU_CONFIG) -L/autofs/nccs-svm1_sw/summit/.swci/1-compute/opt/spack/20180914/linux-rhel7-ppc64le/gcc-6.4.0/spectrum-mpi-10.3.0.0-20190419-4um5hjogm3tepg4xe23hrptlrs2y7ez6/lib -Wl,-rpath,$(TAU_MPILIB_DIR)@g
s@^TAU_MPILIB_DIR=\(.*\)@TAU_MPILIB_DIR=/autofs/nccs-svm1_sw/summit/.swci/1-compute/opt/spack/20180914/linux-rhel7-ppc64le/gcc-6.4.0/spectrum-mpi-10.3.0.0-20190419-4um5hjogm3tepg4xe23hrptlrs2y7ez6/lib@g
s@^TAU_MPILIB_DIRLIB=\(.*\)@TAU_MPILIB_DIRLIB=-L/autofs/nccs-svm1_sw/summit/.swci/1-compute/opt/spack/20180914/linux-rhel7-ppc64le/gcc-6.4.0/spectrum-mpi-10.3.0.0-20190419-4um5hjogm3tepg4xe23hrptlrs2y7ez6/lib@g
s/#TAU_STRSIGNAL_OK#\(.*\)/\1#TAU_STRSIGNAL_OK#/g
s/#TAU_LARGEFILE#\(.*\)/\1#TAU_LARGEFILE#/g
s/#TAU_WEAK_SUPPORTED#\(.*\)/\1#TAU_WEAK_SUPPORTED#/g
s,^BFDINCLUDE=.*$,BFDINCLUDE=-I/ccs/home/ssinghal/tau2-install/ibm64linux/binutils-2.23.2/include -I/ccs/home/ssinghal/tau2-install/ibm64linux/binutils-2.23.2/include/extra,g
s,^BFDLINK=.*$,BFDLINK=-L/ccs/home/ssinghal/tau2-install/ibm64linux/binutils-2.23.2/lib -L/ccs/home/ssinghal/tau2-install/ibm64linux/binutils-2.23.2/lib64 -Wl\,-rpath\,/ccs/home/ssinghal/tau2-install/ibm64linux/binutils-2.23.2/lib -Wl\,-rpath\,/ccs/home/ssinghal/tau2-install/ibm64linux/binutils-2.23.2/lib64,g
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
s/#TAU_UNWIND#\(.*\)/\1#TAU_UNWIND#/g
s/#TAU_UNWIND_LIBUNWIND#\(.*\)/\1#TAU_UNWIND_LIBUNWIND#/g
s,^UNWIND_FLAG=.*$,UNWIND_FLAG=-DTAU_USE_LIBUNWIND,g
s,^UNWIND_INC=.*$,UNWIND_INC=/ccs/home/ssinghal/tau2-install/ibm64linux/libunwind-1.3.1-gcc/include,g
s,^UNWIND_LIB=.*$,UNWIND_LIB=/ccs/home/ssinghal/tau2-install/ibm64linux/libunwind-1.3.1-gcc/lib,g
s@^UNWIND_LIB_FLAG=\(.*\)@UNWIND_LIB_FLAG=-lunwind -Wl,-rpath,$(UNWIND_LIB)@g
s,^UNWIND_EXTRAS=.*$,UNWIND_EXTRAS=-Wl\,-rpath=/ccs/home/ssinghal/tau2-install/ibm64linux/libunwind-1.3.1-gcc/lib,g
s/#EBS_HAS_RT#\(.*\)/\1#EBS_HAS_RT#/g
s,^EBS_CLOCK_RES=.*$,EBS_CLOCK_RES=1,g
s/#ADIOS2#\(.*\)/\1#ADIOS2#/g
s,^ADIOS2DIR=.*$,ADIOS2DIR=/ccs/home/ssinghal/ADIOS2-install,g
s,^ADIOS2_CXXFLAGS=.*$,ADIOS2_CXXFLAGS=-std=gnu++11,g
s,^ADIOS2_LIBS=.*$,ADIOS2_LIBS=-L/ccs/home/ssinghal/ADIOS2-install/lib -ladios2,g
s/#PAPIPTHREAD#\(.*\)/\1#PAPIPTHREAD#/g
s@^EXTRA_LINKER_ARGS=.*$@EXTRA_LINKER_ARGS= -Wl,--export-dynamic@g
s@^TAU_CONFIG=\(.*\)@TAU_CONFIG=-papi-gnu-mpi-pthread-adios2@g
