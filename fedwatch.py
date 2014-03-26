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
__version__='0.4'

import errno
import os
import logging
import stat
import subprocess

import dpath
import dpath.util
import fedmsg
import fedmsg.meta
import fedmsg.config
log = logging.getLogger()


class SUIDError(OSError):
    pass

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

    @staticmethod
    def __generate_setuid(uid):
        def change_setuid():
            try:
                os.setuid(uid)
            except OSError, e:
                log.warn("setuid() call failed: {e}".format(e=e))
                raise SUIDError()

        return change_setuid

    def __run_scripts(self, script_dir, pargs):
        try:
            for f in sorted(os.listdir(script_dir)):
                fpath=os.path.join(script_dir, f)
                if not os.path.isfile(fpath):
                    continue

                if not os.access(fpath, os.X_OK):
                    log.warn("Non-executable file in script dir: {fpath}"
                            .format(fpath=fpath))
                    continue

                procarg=[fpath]
                procarg.extend(pargs)
                st = os.stat(fpath)
                proc_owner = os.getuid()
                mode = st.st_mode
                preexec = None
                if mode & stat.S_ISUID:
                    preexec = FedWatch.__generate_setuid(st.st_uid)
                    proc_owner = st.st_uid
                log.info("Executing (UID={uid}): {proc}"
                         .format(proc=procarg,
                                 uid=proc_owner))
                try:
                    subprocess.Popen(procarg, preexec_fn=preexec)
                except SUIDError, e:
                    pass

        except OSError, e:
            log.error(e)

    def watch(self):
        config = fedmsg.config.load_config()
        fedmsg.init(mute=True, **config)
        fedmsg.meta.make_processors(**config)

        for name, endpoint, topic, msg in fedmsg.tail_messages():
            log.debug("received topic: {topic}".format(topic=topic))
            if not topic in self.topics:
                continue

            log.debug("match topic {topic}=>{data}".format(topic=topic,
                                                           data=msg['msg']))
            pargs = [topic]
            for parg in self.topics[topic]['args']:
                if hasattr(parg, '__call__'):
                    # run this as fedmsg.meta function
                    pargs.append(parg(msg, **config))
                elif '/' in parg:
                    # this is a dpath expression
                    try:
                        path, val = dpath.util.search(msg, parg, yielded=True).next()
                        pargs.append(val)
                    except StopIteration:
                        log.warning("Path {parg} does not exist in {topic}. Substituting empty string"
                        .format(parg=parg, topic=topic))
                        pargs.append('')
                elif parg in msg:
                    pargs.append(msg[parg])
                else:
                    log.warning("Path {parg} does not exist in {topic}. Substituting empty string"
                               .format(parg=parg, topic=topic))
                    pargs.append('')

            self.__run_scripts(self.script_dir, pargs)
