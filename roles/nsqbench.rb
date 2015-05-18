name 'nsqbench'
description 'nsqbench'
run_list(
    'recipe[golang::packages]'
)
default_attributes(
    go: {
      packages: [
        "github.com/BurntSushi/toml",
        "github.com/bitly/nsq/internal/app",
        "github.com/bitly/nsq/internal/version",
        "github.com/bitly/nsq/nsqd",
        "github.com/mreiferson/go-options",
      ],
    }
)
