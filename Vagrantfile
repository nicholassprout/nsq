# -*- mode: ruby -*-
#
##  vi: set ft=ruby :

#NSQ_NUM_DAE_HOSTS=ENV['NSQ_NUM_DAE_HOSTS']
NSQ_NUM_DAE_HOSTS=1
NSQ_NUM_PUB_HOSTS=1
NSQ_NUM_SUB_HOSTS=1
NSQ_JSON = {
  "run_list" => [
    "role[vagrant]",
    "role[nsqadmin]",
    "role[nsqd]",
    "role[nsqlookupd]",
    ]
}
PUB_JSON = {
  "run_list" => [
    "role[vagrant]",
    "role[nsqbench]",
    ]
}
SUB_JSON = PUB_JSON
VAGRANTFILE_API_VERSION = "2"
require 'json'
require 'vagrant-berkshelf'

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  (1..NSQ_NUM_DAE_HOSTS).each do |i|
    config.vm.define "nsq#{i}" do |nsqh|
      nsqh.vm.hostname = "nsq#{i}"
      nsqh.vm.box = "ubuntu/trusty64"
      #nsqh.vm.network "public_network", bridge: "en0: Wi-Fi (AirPort)", ip: "192.168.138.1-#{i}"
      nsqh.vm.network "private_network", type: "dhcp"
      config.vm.provision "chef_solo" do |chef|
        # Force chef 11
        chef.version = "11.14.2"
        config.berkshelf.enabled = true
        chef.cookbooks_path = [ "cookbooks", "berks-cookbooks" ]
        chef.roles_path = "roles"
        chef.provisioning_path = "/tmp/vagrant-chef"
        chef.json = NSQ_JSON
      end
    end
  end
  (1..NSQ_NUM_PUB_HOSTS).each do |i|
    config.vm.define "pub#{i}" do |pubh|
      pubh.vm.hostname = "pub#{i}"
      pubh.vm.box = "ubuntu/trusty64"
      pubh.vm.network "private_network", type: "dhcp"
      config.vm.synced_folder ".", "/nsq"
      config.vm.provision "chef_solo" do |chef|
        # Force chef 11
        chef.version = "11.14.2"
        config.berkshelf.enabled = true
        chef.cookbooks_path = [ "cookbooks", "berks-cookbooks" ]
        chef.roles_path = "roles"
        chef.provisioning_path = "/tmp/vagrant-chef"
        chef.json = PUB_JSON
      end
    end
  end
  (1..NSQ_NUM_SUB_HOSTS).each do |i|
    config.vm.define "sub#{i}" do |subh|
      subh.vm.hostname = "sub#{i}"
      subh.vm.box = "ubuntu/trusty64"
      subh.vm.network "private_network", type: "dhcp"
      config.vm.synced_folder ".", "/nsq"
      config.vm.provision "chef_solo" do |chef|
        # Force chef 11
        chef.version = "11.14.2"
        config.berkshelf.enabled = true
        chef.cookbooks_path = [ "cookbooks", "berks-cookbooks" ]
        chef.roles_path = "roles"
        chef.provisioning_path = "/tmp/vagrant-chef"
        chef.json = SUB_JSON
      end
    end
  end
end
