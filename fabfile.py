# -*- coding: utf-8 -*-
"""
fabfile.py used to to run nsq benchmarks
 copyright:  2015, (c) sproutsocial.com
 author:   Nicholas Flink <nicholas@sproutsocial.com>
"""
import datetime
import fabric
import time

BENCH_DURATION=10
BENCH_MSG_SIZE=600
DEADLINE_FMT = '%Y-%m-%d %H:%M:%S'

def _set_defaults_values(start, end, num_hosts):
    overhead = (end - start) / num_hosts
    deadline = end + overhead
    fabric.api.env['writer_args'] = [
        '-batch-size', str(200),
        '-deadline', "'"+deadline.strftime(DEADLINE_FMT)+"'",
        '-nsqd-tcp-address', fabric.api.env.roledefs['nsq']['hosts'][0]+":4150",
        '-runfor', str(BENCH_DURATION)+'s',
        '-size', str(BENCH_MSG_SIZE),
        '-topic', "sub_bench",
    ]
    fabric.api.env['reader_args'] = [
        '-runfor', str(BENCH_DURATION)+'s',
        '-nsqd-tcp-address', fabric.api.env.roledefs['nsq']['hosts'][0]+":4150",
        '-size', str(BENCH_MSG_SIZE),
        '-topic', "sub_bench",
        '-channel', "ch",
        '-deadline', "'"+deadline.strftime(DEADLINE_FMT)+"'",
        '-rdy', str(2500),
    ]
    fabric.api.env['collate_args'] = {
        'wait_until': deadline,
        'wait_duration': datetime.timedelta(seconds=BENCH_DURATION+overhead.total_seconds()),
    }


def rackspace(user, nsqdHosts):
    fabric.api.env.user = user
    fabric.api.env.roledefs = {'pub': {'hosts': [], 'key_filename': "~/.ssh/id_rsa.pub"},
                               'sub': {'hosts': [], 'key_filename': "~/.ssh/id_rsa.pub"},
                               'nsq': {'hosts': nsqdHosts.split(":"), 'key_filename': "~/.ssh/id_rsa.pub"}}
    count = 0
    for host in fabric.api.env.hosts:
        if count % 2 == 0:
            fabric.api.env.roledefs['pub']['hosts'].append(host)
        else:
            fabric.api.env.roledefs['sub']['hosts'].append(host)
        count += 1
    fabric.api.env.user = user
    start = datetime.datetime.utcnow()
    fabric.contrib.project.rsync_project(remote_dir='~/', local_dir='bench')
    fabric.api.run("cd ~/bench/bench_reader/ && go build; cd ~/bench/bench_writer/ && go build")
    end = datetime.datetime.utcnow()
    _set_defaults_values(start, end, 2)


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
    # start at one to avoid div by zero and add grace period
    num_valid_hosts = 1
    for vhost in vms:
        ssh_command = "ifconfig eth1; cd ~/bench/bench_reader/ && go build; cd ~/bench/bench_writer/ && go build"
        roledef = None
        if vhost.startswith("pub"):
            roledef = 'pub'
        if vhost.startswith("sub"):
            roledef = 'sub'
        if vhost.startswith("nsq"):
            roledef = 'nsq'
            ssh_command = "ifconfig eth1"
        if roledef is not None:
            num_valid_hosts += 1
            vhost_addr = None
            ssh_command = "ifconfig eth1"
            ip_result = fabric.api.local('vagrant ssh '+vhost+' -c "'+ssh_command+'"', capture=True)
            for line in ip_result.split("\n"):
                if line.strip().startswith("inet addr"):
                    vhost_addr = line.strip()[len("inet addr:"):].split()[0]
                    id_result = fabric.api.local('vagrant ssh-config '+vhost+'| grep IdentityFile', capture=True)
                    id_file = id_result.split()[1]
                    if vhost_addr is not None:
                        fabric.api.env.roledefs[roledef]['hosts'].append(vhost_addr)
                        fabric.api.env.roledefs[roledef]['key_filename'].append(id_file)
                    break
    end = datetime.datetime.utcnow()
    _set_defaults_values(start, end, num_valid_hosts)


@fabric.decorators.roles('sub')
def build_sub():
    fabric.api.env.hosts = fabric.api.env.roledefs['pub']['hosts'] + fabric.api.env.roledefs['sub']['hosts']
    fabric.contrib.project.rsync_project(remote_dir='~/bench', local_dir='bench')
    fabric.api.run("nohup /nsq/bench/bench_writer/bench_writer "+args+" &> /tmp/bench.txt < /dev/null &", pty=False)


@fabric.api.parallel
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
    fabric.api.run("nohup ~/bench/bench_writer/bench_writer "+args+" &> /tmp/bench.txt < /dev/null &", pty=False)


@fabric.decorators.parallel
@fabric.decorators.roles('sub')
def reader():
    fabric.api.env.hosts = fabric.api.env.roledefs['sub']['hosts']
    fabric.api.env.key_filename = fabric.api.env.roledefs['sub']['key_filename']
    args = " ".join(fabric.api.env['reader_args'])
    fabric.api.run("nohup ~/bench/bench_reader/bench_reader "+args+" &> /tmp/bench.txt < /dev/null &", pty=False)


@fabric.decorators.runs_once
@fabric.decorators.roles('pub', 'sub')
def wait():
    now = datetime.datetime.utcnow()
    wait_until = fabric.api.env['collate_args']['wait_until']
    wait_duration = fabric.api.env['collate_args']['wait_duration']
    if now < wait_until:
        wait_duration += (wait_until - now)
    wait_seconds = wait_duration.total_seconds()
    print "waiting duration time of %d seconds for nohup process to complete." % wait_seconds
    time.sleep(wait_seconds)


@fabric.decorators.roles('pub', 'sub')
def collate():
    fabric.api.env.hosts = fabric.api.env.roledefs['pub']['hosts'] + fabric.api.env.roledefs['sub']['hosts']
    fabric.api.env.key_filename = fabric.api.env.roledefs['pub']['key_filename'] + fabric.api.env.roledefs['sub']['key_filename']
    fabric.api.run("cat /tmp/bench.txt")
