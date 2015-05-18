name 'nsqd'
description 'nsqd'
run_list(
    'recipe[nsq::nsqd]'
)

NSQ_NUM_DAE_HOSTS=1
override_attributes(
    nsq: {
        nsqd: {
            lookupd_tcp_address: (1..NSQ_NUM_DAE_HOSTS).map{|i| "192.168.138.1#{i}:4160" }
        }
    }
)

