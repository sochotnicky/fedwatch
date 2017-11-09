fedwatch
========

Library for watching fedmsg messages and running arbitrary scripts in a nice way

Think of fedwatch as simple converter from fedmsg JSON messages into shell
arguments for scripts. 

fedwatch is like inetd for fedmsg - it listens for incoming fedmsg
traffic and spawns user-supplied executables for handling matching
messages.  It improves efficiency of scripts for reacting on fedmsg
events and makes them easier to write.

Dependencies
============
* fedmsg (duh!)
* python-dpath (https://github.com/akesterson/dpath-python)

Usage
=====

To use fedwatch you will need to create a configuration file (by default read
from /etc/fedwatch.conf) and scripts that are to be run when messages of
interest arrive (by default /etc/fedwatch.d). 

When interesting message arrives, fedmsg converts JSON data into arguments for
shell scripts and runs each script in <em>script-dir</em> based on
configuration. First argument is always topic so that scripts can handle
different topics. 

Real life example of configuration file:

    {
        "org.fedoraproject.prod.git.receive": {
            "args": [
                "msg/commit/username",
                "msg/commit/repo",
                "msg/commit/branch",
                "msg/commit/rev",
                "msg/commit/summary"
            ]
        }
    }

Above configuration means fedwatch will be waiting for <em>git.receive</em>
topic and will pass 6 arguments to any scripts in <em>script-dir</em>:
  
  1. org.fedoraproject.prod.git.receive (topic)
  2. FAS username of commiter
  3. repository (package) name
  4. branch name
  5. revision (SHA hash of commit)
  6. commit summary (1st line of git commit)

To see list of possible topics and data included in them see
https://fedora-fedmsg.readthedocs.io/

