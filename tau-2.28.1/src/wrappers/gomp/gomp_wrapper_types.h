#include "omp.h"
#include "pthread.h"
typedef void * (*start_routine_p)(void *);
typedef int  (*pthread_create_p)(pthread_t *, const pthread_attr_t *, start_routine_p, void *arg);
typedef void (*omp_set_lock_p) (omp_lock_t*);
typedef void (*omp_set_nest_lock_p) (omp_nest_lock_t*);
typedef void (*GOMP_barrier_p) ();
typedef void (*GOMP_critical_start_p) ();
typedef void (*GOMP_critical_end_p) ();
typedef void (*GOMP_critical_name_start_p) (void **);
typedef void (*GOMP_critical_name_end_p) (void **);
typedef void (*GOMP_atomic_start_p) ();
typedef void (*GOMP_atomic_end_p) ();
typedef bool (*GOMP_loop_static_start_p) (long, long, long, long, long *, long *);
typedef bool (*GOMP_loop_dynamic_start_p) (long, long, long, long, long *, long *);
typedef bool (*GOMP_loop_guided_start_p) (long, long, long, long, long *, long *);
typedef bool (*GOMP_loop_runtime_start_p) (long, long, long, long *, long *);
typedef bool (*GOMP_loop_ordered_static_start_p) (long, long, long, long, long *, long *);
typedef bool (*GOMP_loop_ordered_dynamic_start_p) (long, long, long, long, long *, long *);
typedef bool (*GOMP_loop_ordered_guided_start_p) (long, long, long, long, long *, long *);
typedef bool (*GOMP_loop_ordered_runtime_start_p) (long, long, long, long *, long *);
typedef bool (*GOMP_loop_static_next_p) (long *, long *);
typedef bool (*GOMP_loop_dynamic_next_p) (long *, long *);
typedef bool (*GOMP_loop_guided_next_p) (long *, long *);
typedef bool (*GOMP_loop_runtime_next_p) (long *, long *);
typedef bool (*GOMP_loop_ordered_static_next_p) (long *, long *);
typedef bool (*GOMP_loop_ordered_dynamic_next_p) (long *, long *);
typedef bool (*GOMP_loop_ordered_guided_next_p) (long *, long *);
typedef bool (*GOMP_loop_ordered_runtime_next_p) (long *, long *);
typedef void (*GOMP_parallel_loop_static_start_p) (void (*)(void *), void *, unsigned int, long, long, long, long);
typedef void (*GOMP_parallel_loop_dynamic_start_p) (void (*)(void *), void *, unsigned int, long, long, long, long);
typedef void (*GOMP_parallel_loop_guided_start_p) (void (*)(void *), void *, unsigned int, long, long, long, long);
typedef void (*GOMP_parallel_loop_runtime_start_p) (void (*)(void *), void *, unsigned int, long, long, long);
typedef void (*GOMP_loop_end_p) ();
typedef void (*GOMP_loop_end_nowait_p) ();
typedef bool (*GOMP_loop_ull_static_start_p) (bool, unsigned long long, unsigned long long, unsigned long long, unsigned long long, unsigned long long *, unsigned long long *);
typedef bool (*GOMP_loop_ull_dynamic_start_p) (bool, unsigned long long, unsigned long long, unsigned long long, unsigned long long, unsigned long long *, unsigned long long *);
typedef bool (*GOMP_loop_ull_guided_start_p) (bool, unsigned long long, unsigned long long, unsigned long long, unsigned long long, unsigned long long *, unsigned long long *);
typedef bool (*GOMP_loop_ull_runtime_start_p) (bool, unsigned long long, unsigned long long, unsigned long long, unsigned long long *, unsigned long long *);
typedef bool (*GOMP_loop_ull_ordered_static_start_p) (bool, unsigned long long, unsigned long long, unsigned long long, unsigned long long, unsigned long long *, unsigned long long *);
typedef bool (*GOMP_loop_ull_ordered_dynamic_start_p) (bool, unsigned long long, unsigned long long, unsigned long long, unsigned long long, unsigned long long *, unsigned long long *);
typedef bool (*GOMP_loop_ull_ordered_guided_start_p) (bool, unsigned long long, unsigned long long, unsigned long long, unsigned long long, unsigned long long *, unsigned long long *);
typedef bool (*GOMP_loop_ull_ordered_runtime_start_p) (bool, unsigned long long, unsigned long long, unsigned long long, unsigned long long *, unsigned long long *);
typedef bool (*GOMP_loop_ull_static_next_p) (unsigned long long *, unsigned long long *);
typedef bool (*GOMP_loop_ull_dynamic_next_p) (unsigned long long *, unsigned long long *);
typedef bool (*GOMP_loop_ull_guided_next_p) (unsigned long long *, unsigned long long *);
typedef bool (*GOMP_loop_ull_runtime_next_p) (unsigned long long *, unsigned long long *);
typedef bool (*GOMP_loop_ull_ordered_static_next_p) (unsigned long long *, unsigned long long *);
typedef bool (*GOMP_loop_ull_ordered_dynamic_next_p) (unsigned long long *, unsigned long long *);
typedef bool (*GOMP_loop_ull_ordered_guided_next_p) (unsigned long long *, unsigned long long *);
typedef bool (*GOMP_loop_ull_ordered_runtime_next_p) (unsigned long long *, unsigned long long *);
typedef void (*GOMP_ordered_start_p) ();
typedef void (*GOMP_ordered_end_p) ();
typedef void (*GOMP_parallel_start_p) (void (*)(void *), void *, unsigned int);
typedef void (*GOMP_parallel_end_p) ();
typedef void (*GOMP_task_p) (void (*)(void *), void *, void (*)(void *, void *), long, long, bool, unsigned int);
typedef void (*GOMP_taskwait_p) ();
/* taskyield is not defined until 4.7, and even then it is just a stub */
typedef void (*GOMP_taskyield_p) ();
typedef unsigned int (*GOMP_sections_start_p) (unsigned int);
typedef unsigned int (*GOMP_sections_next_p) ();
typedef void (*GOMP_parallel_sections_start_p) (void (*)(void *), void *, unsigned int, unsigned int);
typedef void (*GOMP_sections_end_p) ();
typedef void (*GOMP_sections_end_nowait_p) ();
typedef bool (*GOMP_single_start_p) ();
typedef void * (*GOMP_single_copy_start_p) ();
typedef void (*GOMP_single_copy_end_p) (void *);