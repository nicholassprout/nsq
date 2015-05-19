# -*- coding: utf-8 -*-
"""
fabfile.py used to to run nsq benchmarks
 copyright:  2015, (c) sproutsocial.com
 author:   Nicholas Flink <nicholas@sproutsocial.com>
"""
import datetime
import fabric
import time


def vagrant():
    # find hosts
    status_result = fabric.api.local('vagrant status|grep running', capture=True)
    vms = []
    fabric.api.env.roledefs = {'pub': {'hosts': [], 'key_filename': []},
                               'sub': {'hosts': [], 'key_filename': []},
                               'nsq': {'hosts': [], 'key_filename': []}}
    fabric.api.env.hosts = []
    fabric.api.env.user = "vagrant"
    fabric.api.env.key_filename = []
    for line in status_result.split("\n"):
        vhost = line.split()[0]
        vms.append(vhost)
    start = datetime.datetime.utcnow()
    for vhost in vms:
        roledef = None
        if vhost.startswith("pub"):
            roledef = 'pub'
        if vhost.startswith("sub"):
            roledef = 'sub'
        if vhost.startswith("nsq"):
            roledef = 'nsq'
        vhost_addr = None
        ip_result = fabric.api.local('vagrant ssh '+vhost+' -c "ifconfig eth1"', capture=True)
        for line in ip_result.split("\n"):
            if line.strip().startswith("inet addr"):
                vhost_addr = line.strip()[len("inet addr:"):].split()[0]
                id_result = fabric.api.local('vagrant ssh-config '+vhost+'| grep IdentityFile', capture=True)
                id_file = id_result.split()[1]
                if roledef is not None:
                    fabric.api.env.roledefs[roledef]['hosts'].append(vhost_addr)
                    fabric.api.env.roledefs[roledef]['key_filename'].append(id_file)
                break
    end = datetime.datetime.utcnow()
    duration = 10
    overhead = end - start
    deadline = end + overhead
    DEADLINE_FMT = '%Y-%m-%d %H:%M:%S'
    fabric.api.env['writer_args'] = [
        '-batch-size', str(200),
        '-deadline', "'"+deadline.strftime(DEADLINE_FMT)+"'",
        '-nsqd-tcp-address', fabric.api.env.roledefs['nsq']['hosts'][0]+":4150",
        '-runfor', str(duration)+'s',
        '-size', str(200),
        '-topic', "sub_bench",
    ]
    fabric.api.env['reader_args'] = [
        '-runfor', str(duration)+'s',
        '-nsqd-tcp-address', fabric.api.env.roledefs['nsq']['hosts'][0]+":4150",
        '-size', str(200),
        '-topic', "sub_bench",
        '-channel', "ch",
        '-deadline', "'"+deadline.strftime(DEADLINE_FMT)+"'",
        '-rdy', str(2500),
    ]
    fabric.api.env['collate_args'] = {
        'wait_until': deadline + datetime.timedelta(seconds=duration),
    }


@fabric.decorators.parallel
@fabric.decorators.roles('nsq', 'pub', 'sub')
def sync_clock():
    fabric.api.env.hosts = fabric.api.env.roledefs['nsq']['hosts'] + fabric.api.env.roledefs['pub']['hosts'] + fabric.api.env.roledefs['sub']['hosts']
    fabric.api.env.key_filename = fabric.api.env.roledefs['nsq']['key_filename'] + fabric.api.env.roledefs['pub']['key_filename'] + fabric.api.env.roledefs['sub']['key_filename']
    fabric.api.sudo("ntpdate time.nist.gov")


@fabric.decorators.parallel
@fabric.decorators.roles('pub')
def writer():
    fabric.api.env.hosts = fabric.api.env.roledefs['pub']['hosts']
    fabric.api.env.key_filename = fabric.api.env.roledefs['pub']['key_filename']
    args = " ".join(fabric.api.env['writer_args'])
    fabric.api.run("nohup /nsq/bench/bench_writer/bench_writer "+args+" &> /tmp/bench.txt < /dev/null &", pty=False)


@fabric.decorators.parallel
@fabric.decorators.roles('sub')
def reader():
    fabric.api.env.hosts = fabric.api.env.roledefs['sub']['hosts']
    fabric.api.env.key_filename = fabric.api.env.roledefs['sub']['key_filename']
    args = " ".join(fabric.api.env['reader_args'])
    fabric.api.run("nohup /nsq/bench/bench_reader/bench_reader "+args+" &> /tmp/bench.txt < /dev/null &", pty=False)


@fabric.decorators.parallel
@fabric.decorators.roles('pub', 'sub')
def wait():
    wait_until = fabric.api.env['collate_args']['wait_until']
    wait_seconds = (wait_until - datetime.datetime.utcnow()).total_seconds()
    print "waiting estimated time of %d seconds for nohup process to stop." % wait_seconds
    time.sleep(wait_seconds)


@fabric.decorators.roles('pub', 'sub')
def collate():
    fabric.api.env.hosts = fabric.api.env.roledefs['pub']['hosts'] + fabric.api.env.roledefs['sub']['hosts']
    fabric.api.env.key_filename = fabric.api.env.roledefs['pub']['key_filename'] + fabric.api.env.roledefs['sub']['key_filename']
    fabric.api.run("cat /tmp/bench.txt")
