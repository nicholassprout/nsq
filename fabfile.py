# -*- coding: utf-8 -*-
"""
fabfile.py used to to run nsq benchmarks
 copyright:  2015, (c) sproutsocial.com
 author:   Nicholas Flink <nicholas@sproutsocial.com>
"""
import fabric
import pprint
import time

def vagrant():
    # find hosts
    status_result = fabric.api.local('vagrant status|grep running', capture=True)
    vms = []
    fabric.api.env.roledefs = {'pub': {'hosts': [], 'key_filename': []},
                               'sub': {'hosts': [], 'key_filename': []},
                               'nsq': {'hosts': [], 'key_filename': []}}
    fabric.api.env.hosts = []
    fabric.api.env.user = []
    fabric.api.env.key_filename = []
    for line in status_result.split("\n"):
        vhost = line.split()[0]
        vms.append(vhost)
    start = time.time()
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
                    fabric.api.env.roledefs[roledef]['user'] = 'vagrant'
                break;
    end = time.time()
    ssh_overhead = end - start
    print "vagrant ssh overhead time:", ssh_overhead
    pprint.pprint(fabric.api.env.user)
    pprint.pprint(fabric.api.env.hosts)
    pprint.pprint(fabric.api.env.key_filename)

@fabric.decorators.roles('pub')
def writer():
    fabric.api.env.hosts = fabric.api.env.roledefs['pub']['hosts']
    fabric.api.env.key_filename = fabric.api.env.roledefs['pub']['key_filename']
    fabric.api.env.user = fabric.api.env.roledefs['pub']['user']
    nsqd_ip = fabric.api.env.roledefs['nsq']['hosts'][0] 
    # this sleep is really ugly and is not necessary in bash but the run command does not work with out it
    fabric.api.run("nohup /nsq/bench/bench_writer/bench_writer -nsqd-tcp-address="+nsqd_ip+":4150 &> /tmp/pub.txt < /dev/null & sleep 1")

@fabric.decorators.roles('sub')
def reader():
    #fabric.api.env.hosts = fabric.api.env.roledefs['sub']['hosts']
    #fabric.api.env.key_filename = fabric.api.env.roledefs['sub']['key_filename']
    fabric.api.env.hosts = fabric.api.env.roledefs['sub']['hosts']
    fabric.api.env.key_filename = fabric.api.env.roledefs['sub']['key_filename']
    fabric.api.env.user = fabric.api.env.roledefs['sub']['user']
    nsqd_ip = fabric.api.env.roledefs['nsq']['hosts'][0] 
    # this sleep is really ugly and is not necessary in bash but the run command does not work with out it
    fabric.api.run("nohup /nsq/bench/bench_reader/bench_reader -nsqd-tcp-address="+nsqd_ip+":4150 &> /tmp/sub.txt < /dev/null & sleep 1")

