#!/usr/bin/python
# see LICENSE file
"""
Module for watching fedmsg messages and running scripts based on those messages

    Copyright (C) 2014 Red Hat, Inc.

    This library is free software; you can redistribute it and/or
    modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 2.1 of the License, or (at your option) any later version.

    This library is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with this library; if not, write to the Free Software
    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301
    USA
"""
__version__='0.2'

import os
import logging
import subprocess

import dpath
import dpath.util
import fedmsg
import fedmsg.meta
import fedmsg.config
log = logging.getLogger()

class FedWatch(object):
    """Class to simplify running scripts based on fedmsg messages"""

    def __init__(self, topics, script_dir):
        """
        topics - dictionary where keys are topics to listen to and values are
                 lists of message data information that will be passed to
                 scripts or fedmsg.meta functions used to filter data
        script_dir - directory where scripts to be run are located

        Example:
        FedWatch({'org.fedoraproject.prod.buildsys.repo.done':['tag',
                                                               'instance',
                                                               fedmsg.meta.msg2link]},
                 '/tmp/test_dir')

        Above will listen to repo.done messages and for each received message
        execute scripts in /tmp/test_dir directory while passing 'tag',
        'instance' and http link to tag in question.
        """
        self.topics = topics
        self.script_dir = script_dir

    def __run_scripts(self, script_dir, pargs):
        try:
            for f in sorted(os.listdir(script_dir)):
                fpath=os.path.join(script_dir, f)
                if os.access(fpath, os.X_OK) and os.path.isfile(fpath):
                    procarg=[fpath]
                    procarg.extend(pargs)
                    log.info("Executing: {proc}".format(proc=procarg))
                    subprocess.Popen(procarg)
        except OSError, e:
            log.error(e)

    def watch(self):
        config = fedmsg.config.load_config()
        fedmsg.init(mute=True, **config)
        fedmsg.meta.make_processors(**config)

        for name, endpoint, topic, msg in fedmsg.tail_messages():
            log.debug("received topic: {topic}".format(topic=topic))
            for watchtop in self.topics:
                if topic == watchtop:
                    data=msg['msg']
                    log.debug("match topic {topic}=>{data}".format(topic=topic,
                                                                  data=data))
                    pargs = [topic]
                    for parg in self.topics[watchtop]:
                        if hasattr(parg, '__call__'):
                            # run this as fedmsg.meta function
                            pargs.append(parg(msg, **config))
                        elif '/' in parg:
                            # this is a dpath expression
                            path, val = dpath.util.search(msg, parg, yielded=True).next()
                            pargs.append(val)
                        elif parg in data:
                            pargs.append(msg[parg])
                    self.__run_scripts(self.script_dir, pargs)
