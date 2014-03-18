#!/bin/sh

if [[ "$1" != "org.fedoraproject.prod.git.receive" ]];then
    exit 0
fi

username=$1
pkgname=$3
branch=$2

# do stuff
