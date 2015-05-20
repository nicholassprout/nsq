name 'nsqd'
description 'nsqd'
run_list(
    'recipe[nsq::nsqd]'
)

override_attributes(
    nsq: {
        nsqd: {
            lookupd_tcp_address: ['172.28.128.3']
        }
    }
)

