#!/bin/sh

##
## This file is part of the Score-P software (http://www.score-p.org)
##
## Copyright (c) 2009-2011,
## RWTH Aachen University, Germany
##
## Copyright (c) 2009-2011,
## Gesellschaft fuer numerische Simulation mbH Braunschweig, Germany
##
## Copyright (c) 2009-2011, 2013-2014,
## Technische Universitaet Dresden, Germany
##
## Copyright (c) 2009-2011,
## University of Oregon, Eugene, USA
##
## Copyright (c) 2009-2011,
## Forschungszentrum Juelich GmbH, Germany
##
## Copyright (c) 2009-2011,
## German Research School for Simulation Sciences GmbH, Juelich/Aachen, Germany
##
## Copyright (c) 2009-2011,
## Technische Universitaet Muenchen, Germany
##
## This software may be modified and distributed under the terms of
## a BSD-style license.  See the COPYING file in the package base
## directory for details.
##

## file       test/OTF2_Integrity_test/run_otf2_integrity_test.sh

set -e

cleanup()
{
    rm -rf OTF2_Integrity_trace
}
trap cleanup EXIT

cleanup
$VALGRIND ./OTF2_Integrity_test

# we should also be able to read trace format version 1
echo "Read trace format version 1"
$VALGRIND ./OTF2_Integrity_test ./../test/OTF2_Integrity_test/OTF2_Integrity_trace_1/TestTrace.otf2
