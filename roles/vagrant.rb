name "vagrant"
default_attributes(
  "unmanaged_users" => true,
  "sprout_access" => {
    "sudo_users" => [
      "vagrant"
    ],
  }
)
