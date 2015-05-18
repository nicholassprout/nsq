name 'nsqlookupd'
description 'nsqlookupd'
run_list(
    'recipe[nsq::nsqlookupd]'
)

default_attributes(
    nsq: {
        version: '0.3.5',
        go_version: 'go1.4.2'
    }
)
