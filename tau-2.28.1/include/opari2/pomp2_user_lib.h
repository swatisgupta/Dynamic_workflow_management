/*
 * This file is part of the Score-P software (http://www.score-p.org)
 *
 * Copyright (c) 2009-2013,
 * RWTH Aachen University, Germany
 *
 * Copyright (c) 2009-2013,
 * Gesellschaft fuer numerische Simulation mbH Braunschweig, Germany
 *
 * Copyright (c) 2009-2013,
 * Technische Universitaet Dresden, Germany
 *
 * Copyright (c) 2009-2013,
 * University of Oregon, Eugene, USA
 *
 * Copyright (c) 2009-2013,
 * Forschungszentrum Juelich GmbH, Germany
 *
 * Copyright (c) 2009-2013,
 * German Research School for Simulation Sciences GmbH, Juelich/Aachen, Germany
 *
 * Copyright (c) 2009-2013,
 * Technische Universitaet Muenchen, Germany
 *
 * This software may be modified and distributed under the terms of
 * a BSD-style license. See the COPYING file in the package base
 * directory for details.
 *
 */
/****************************************************************************
**  SCALASCA    http://www.scalasca.org/                                   **
**  KOJAK       http://www.fz-juelich.de/jsc/kojak/                        **
*****************************************************************************
**  Copyright (c) 1998-2009                                                **
**  Forschungszentrum Juelich, Juelich Supercomputing Centre               **
**                                                                         **
**  See the file COPYRIGHT in the package base directory for details       **
****************************************************************************/
#ifndef POMP2_USER_LIB_H
#define POMP2_USER_LIB_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

/** @file
 *
 *  @brief      This file contains the declarations of all
 *              POMP2 functions.
 *
 */

/* Avoid warnings from Orcale Studio Compiler if nowait clauses are added
 * to reduction loops. Opari always inserts a barrier after such loops, so
 * the nowait is  save.*/
#if defined( __SUNPRO_C )
#pragma error_messages (off, E_NOWAIT_REDUCTION_USE)
#endif

/** Handles to identify OpenMP regions. */

/** To avoid multiple typedefs of OPARI2_Region_handle*/
#ifndef __opari2_region_handle
typedef void* OPARI2_Region_handle;
#define __opari2_region_handle
#endif

typedef OPARI2_Region_handle POMP2_USER_Region_handle;

/** @name Functions generated by the instrumenter */
/*@{*/
/**
 * Returns the number of instrumented regions.@n
 * The instrumenter scans all OPARI2-created include files with nm and greps
 * the POMP2_INIT_uuid_numRegions() function calls. Here we return the sum of
 * all numRegions.
 * @return number of instrumented regions
 */
extern size_t
POMP2_USER_Get_num_regions( void );

/**
 * Init all OPARI2-created regions.@n
 * The instrumentor scans all OPARI2-created include files with nm and greps
 * the POMP2_INIT_uuid_numRegions() function calls. The instrumentor then
 * defines these functions by calling all grepped functions.
 */
extern void
POMP2_USER_Init_regions( void );

/**
 * Returns the OPARI2 version.
 * @return version string
 */
extern const char*
POMP2_Get_opari2_version( void );

/** Finalizes the POMP2 adapter. It is inserted at the #%pragma pomp inst end.
 */
extern void
POMP2_Finalize( void );

/** Initializes the POMP2 adapter. It is inserted at the #%pragma pomp inst begin.
 */
extern void
POMP2_Init( void );

/** Disables the POMP2 adapter.
 */
extern void
POMP2_Off( void );

/** Enables the POMP2 adapter.
 */
extern void
POMP2_On( void );

/** Called at the begin of a user defined POMP2 region.
    @param pomp2_handle  The handle of the started region.
    @param ctc_string   A string containing the region data.
 */
extern void
POMP2_Begin( POMP2_USER_Region_handle* pomp2_handle,
             const char                ctc_string[] );

/** Called at the begin of a user defined POMP2 region.
    @param pomp2_handle  The handle of the started region.
 */
extern void
POMP2_End( POMP2_USER_Region_handle* pomp2_handle );

/** Registers a POMP2 region and returns a region handle.

    @param pomp2_handle  Returns the handle for the newly registered region.
    @param ctc_string   A string containing the region data.
 */
extern void
POMP2_USER_Assign_handle( POMP2_USER_Region_handle* pomp2_handle,
                          const char                ctc_string[] );

#ifdef __cplusplus
}
#endif

#endif
