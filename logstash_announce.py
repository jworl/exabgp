#!/usr/bin/env python

from __future__ import print_function
from sys import stdout
from time import sleep
from contextlib import closing
from elasticsearch import Elasticsearch

import socket
import salt.client

last_time = None
whoami = socket.gethostname()
vip_list = [ "10.9.9.254" ] #shared loopback between servers
alert = salt.client.Caller()

def _elastic_check():
    es = Elasticsearch([{'host': '127.0.0.1', 'port': 9200}])
    if es.ping():
        return True
    else:
        return False

def _socket_check():
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        if s.connect_ex(('127.0.0.1', 5044)) == 0:
            return True
        else:
            return False

def _send_alert(M):
    alert.sminion.functions['event.send'](
            'salt/{}/slack'.format(whoami),
            {
                "message": M,
            }
    )

def announce_vip():
    for vip in vip_list:
        s = _socket_check()
        e = _elastic_check()
        if e and s:
            both = True
            action = 'announce'
        else:
            both = False
            action = 'withdraw'

        if both != last_time:
            message = '{} route {} next-hop self \n'.format(action, vip)
            _send_alert(message)
            stdout.write(message)
            stdout.flush()
            sleep(1)

        return both

while True:
    last_time = announce_vip()
    sleep(1)
