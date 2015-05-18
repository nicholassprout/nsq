name 'nsqadmin'
description 'nsqadmin'
run_list(
    'recipe[nsq::nsqadmin]'
)

default_attributes(
    nsq: {
        version: '0.3.5',
        go_version: 'go1.4.2'
    }
)

NSQ_NUM_DAE_HOSTS=1
override_attributes(
    nsq: {
        nsqadmin: {
            lookupd_tcp_address: (1..NSQ_NUM_DAE_HOSTS).map{|i| "192.168.138.1#{i}:4160" }
        }
    }
)
