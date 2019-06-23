#!/bin/sh

##
## This file is part of the Score-P software (http://www.score-p.org)
##
## Copyright (c) 2013,
## Technische Universitaet Dresden, Germany
##
## Copyright (c) 2014,
## Forschungszentrum Juelich GmbH, Germany
##
## This software may be modified and distributed under the terms of
## a BSD-style license.  See the COPYING file in the package base
## directory for details.
##

## this is a mini otf2-config intended to be used by a top-level configure

dir=${0%/*}
: ${dir:=.}

show_substrates()
{
    for substrate in $substrates
    do
        echo $substrate
    done
}

show_compressions()
{
    for compression in $compressions
    do
        echo $compression
    done
}

show_targets()
{
    for target in $targets
    do
        echo $target
    done
}

delegate()
{
   exec /lustre/ssinghal/tau2-install/x86_64/otf2-gcc/libexec/otf2/otf2-config-$delegate_target $command
}

frontend=true
action=
command=$*
delegate_target=
target_name=

while test $# -gt 0
do
    if [ $1 = --backend  ]; then
        frontend=false
        shift
    elif [ $1 = --features=substrates ]; then
        action=show_substrates
        shift
    elif [ $1 = --features=compressions ]; then
        action=show_compressions
        shift
    elif [ $1 = --features=targets ]; then
        . $dir/otf2-mini-config-data-backend.sh
        #. $dir/otf2-mini-config-data-frontend.sh
        show_targets
        exit 0
    elif [ $1 = --target ] || [ `expr match "$1" '--target='` = 9 ]; then
        if [ $1 = --target ]; then
            target_name=$2
            shift
        else
            target_name=`echo $1 | cut -b 10-`
        fi
        shift
        case $target_name in
        (frontend)
            frontend=true
        ;;
        (backend)
            frontend=false
        ;;
        (mic)
            delegate_target="mic"
            #frontend=false
        ;;
        (*)
            echo >&2 "otf2-mini-config.sh: unrecognized target: '$target_name'"
            exit 1
        ;;
        esac
    else
        echo >&2 "otf2-mini-config.sh: unrecognized option: '$1'"
        exit 1
    fi
done

if test -z "$action"
then
    echo >&2 "otf2-mini-config.sh: no command specified"
    exit 1
fi


if [ -n "$delegate_target" ];  then
    delegate
fi

. $dir/otf2-mini-config-data-backend.sh
#if $frontend
#then
#. $dir/otf2-mini-config-data-frontend.sh
#else
#. $dir/otf2-mini-config-data-backend.sh
#fi

$action
