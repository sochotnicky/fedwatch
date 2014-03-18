#!/bin/bash

if [[ "$1" == "org.fedoraproject.prod.buildsys.repo.done" && "$2" == "f21-build" && "$3" == "primary" ]];then
    # update metadata for each koji regen repo
    yum --nogpgcheck --disablerepo=\* --enablerepo=koji makecache fast
fi
