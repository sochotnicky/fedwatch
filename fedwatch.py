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
__version__='0.5'

import errno
import os
import logging
import stat
import subprocess

import fedmsg
import fedmsg.meta
import fedmsg.config
log = logging.getLogger()

CONFIG_FILE_EXTS = ['ini', 'conf', 'cfg', 'yml']

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
                    if os.path.splitext(fpath)[-1] not in CONFIG_FILE_EXTS:
                        log.warn("Non-executable file in script dir: {fpath}"
                                .format(fpath=fpath))
                    continue

                procarg=[fpath]
                procarg.extend([str(parg) for parg in pargs])
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
            
            def slop_dicter(msg, parg):
                l = parg.split('/')
                i = len(l)
                if i == 2:
                    return parg, msg[l[0]][l[1]]
                elif i == 3:
                    return parg, msg[l[0]][l[1]][l[2]]
                elif i == 4:
                    return parg, msg[l[0]][l[1]][l[2]][l[3]]
                elif i == 5:
                    return parg, msg[l[0]][l[1]][l[2]][l[3]][l[4]]
                else:
                    log.warning("Message depth of {depth} not supported".format(depth=i))

                
            for parg in self.topics[topic]['args']:
                if hasattr(parg, '__call__'):
                    # run this as fedmsg.meta function
                    pargs.append(parg(msg, **config))
                elif '/' in parg:
                    try:
                        path, val = slop_dicter(msg, parg)
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
