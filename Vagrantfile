# coding: utf-8
# -*- mode: ruby -*-
# vi: set ft=ruby :

# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"
Vagrant.require_version ">=1.7.0"

$bootstrap_fedora = <<SCRIPT
#dnf -y update ||:  ; # save your time. "vagrant box update" is your friend
dnf -y install git time python3 pipenv dos2unix htop
cd /vagrant
pipenv install
SCRIPT

$update_data = <<SCRIPT
cd /vagrant
bash -x ./update.sh
SCRIPT

Vagrant.configure(2) do |config|

    vm_memory = ENV['VM_MEMORY'] || '4096'
    vm_cpus = ENV['VM_CPUS'] || '4'

    config.vm.hostname = "covidUpdate"
    config.vm.box = "fedora/32-cloud-base"
    config.vm.box_check_update = false

    config.vm.synced_folder "#{ENV['PWD']}", "/vagrant", disabled: false, type: "sshfs"
    # Optional: Uncomment line above and comment out the line below if you have
    # the vagrant sshfs plugin and would like to mount the directory using sshfs.
    # config.vm.synced_folder ".", "/vagrant", type: "rsync"

    config.vm.provision "bootstrap_fedora", type: "shell", inline: $bootstrap_fedora
    config.vm.provision "update_data", type: "shell", inline: $update_data, run: "always"

    config.vm.provider 'libvirt' do |lb|
        lb.nested = true
        lb.memory = vm_memory
        lb.cpus = vm_cpus
        lb.suspend_mode = 'managedsave'
    end
    config.vm.provider "virtualbox" do |vb|
       vb.memory = vm_memory
       vb.cpus = vm_cpus
       vb.customize ["modifyvm", :id, "--nested-hw-virt", "on"]
       vb.customize ["modifyvm", :id, "--nictype1", "virtio"]
       vb.customize [
           "guestproperty", "set", :id,
           "/VirtualBox/GuestAdd/VBoxService/--timesync-set-threshold", 10000
          ]
    end
end
