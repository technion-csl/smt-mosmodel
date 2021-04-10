#! /bin/bash

sudo modprobe kvm kvm_intel
sudo systemctl enable --now /lib/systemd/system/libvirt-bin.service
kvm-ok

libvirt_groups=kvm,libvirtd
my_groups=$(groups)
if [[ $my_groups == *"kvm"* ]] && [[ $my_groups == *"libvirtd"* ]]; then
    echo "The user $USER belongs to the $libvirt_groups groups"
else
    echo "The user $USER does not belong to the $libvirt_groups groups"
    echo "Adding it via:"
    sudo usermod -a -G $libvirt_groups $USER
    echo "Please logout and login to belong to the new groups"
    exit -1 # stop the script
fi

