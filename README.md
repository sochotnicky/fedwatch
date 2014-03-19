fedwatch
========

Library for watching fedmsg messages and running arbitrary scripts in a nice way

Think of fedwatch as simple converter from fedmsg json messages into shell
arguments for scripts. 

Dependencies
============
* fedmsg (duh!)
* python-dpath (https://github.com/akesterson/dpath-python)

Usage
=====

To use fedwatch you will need to create a configuration file (by default read
from /etc/fedwatch.conf) and scripts that are to be run when messages of
interest arrive (by default /etc/fedwatch.d). 

When interesting message arrives, fedmsg converts json data into arguments for
shell scripts and runs each script in <em>script-dir</em> based on
configuration. First argument is always topic so that scripts can handle
different topics. 

Real life example of configuration file:

    [org.fedoraproject.prod.git.receive]
    arg1=msg/commit/username
    arg2=msg/commit/repo
    arg3=msg/commit/branch
    arg4=msg/commit/rev
    arg5=msg/commit/summary

Above configuration means fedwatch will be waiting for <em>git.receive</em>
topic and will pass 6 arguments to any scripts in <em>script-dir</em>:
  
  1. org.fedoraproject.prod.git.receive (topic)
  2. FAS username of commiter
  3. repository (package) name
  4. branch name
  5. revision (SHA hash of commit)
  6. commit summary (1st line of git commit)

To see list of possible topics and data included in them see
http://fedmsg.readthedocs.org/en/latest/topics/

