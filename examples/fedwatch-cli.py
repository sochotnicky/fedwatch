#!/usr/bin/python
import logging
from logging.handlers import SysLogHandler
import os
import signal

import argparse
import fedmsg

import fedwatch

log = logging.getLogger()

def configure_logger():
    formatter = logging.Formatter('%(asctime)s - %(module)s - %(levelname)s - %(message)s')
    cl = logging.StreamHandler()
    cl.setFormatter(formatter)
    formatter = logging.Formatter('%(module)s - %(levelname)s - %(message)s')
    sl = SysLogHandler('/dev/log', facility=SysLogHandler.LOG_USER)
    sl.setFormatter(formatter)

    log.addHandler(cl)
    log.addHandler(sl)
    return log

def getinfo(name):
    def g(msg, **config):
        return msg['msg']['commit'][name]
    return g

def termhandler(signum, frame):
    log.info("received SIGTERM. Closing shop.")
    raise SystemExit("received SIGTERM. Closing shop")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run tasks on fedmsg changes',
				     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--script-dir', default='/etc/fedwatch.d',
                        help='Directory with scripts to run for fedmsg messages')
    parser.add_argument('--debug', action='store_true',
                        help='Run with debug output')

    args = parser.parse_args()
    configure_logger()
    if args.debug:
        log.setLevel(logging.DEBUG)
    if not os.path.isdir(args.script_dir):
        parser.error("Script directory {d} is missing".format(d=args.script_dir))
    log.info("started")
    signal.signal(signal.SIGTERM, termhandler)
    try:
        fw = fedwatch.FedWatch({
            'org.fedoraproject.prod.git.receive':[
                getinfo('username'),
                getinfo('repo'),
                getinfo('branch'),
                getinfo('rev'),
                getinfo('summary'),
                fedmsg.meta.msg2link],
            'org.fedoraproject.prod.buildsys.repo.done':[
                'tag',
                'instance',
                fedmsg.meta.msg2link]},
            args.script_dir)
        fw.watch()
    except KeyboardInterrupt:
        log.info("finishing up")
    except Exception, e:
        log.error("runtime exception: {e}".format(e=e))
