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

override_attributes(
    nsq: {
        nsqadmin: {
            lookupd_tcp_address: ['172.28.128.3']
        }
    }
)
