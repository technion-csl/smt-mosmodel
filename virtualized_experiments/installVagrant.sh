#! /bin/bash

# The best method to install vagrant is "apt-get install vagrant"
# I didn't use this option because the package for Ubuntu 16.04 is vagrant 1.8.1,
# which is buggy. I therefore download and install a newer Debian package.
vagrant_package_name=vagrant
vagrant_version=2.2.15
vagrant_debfile=vagrant_${vagrant_version}_x86_64.deb
vagrant_package_url=https://releases.hashicorp.com/vagrant/${vagrant_version}/$vagrant_debfile

dpkg-query --show --showformat='${Status}' $vagrant_package_name > /dev/null 2>&1
if (( $? == 0 )); then
    echo "$vagrant_package_name is installed."
elif (( $? > 0 )); then
    echo "$vagrant_package_name is currently not installed."
    echo "going to install it via:"
    wget $vagrant_package_url
    sudo dpkg -i $vagrant_debfile
    rm -f $vagrant_debfile
fi

libvirt_plugin=vagrant-libvirt
plugin_list=$(vagrant plugin list)
if [[ $plugin_list == *"$libvirt_plugin"* ]]; then
    echo "$libvirt_plugin is installed"
else
    echo "$libvirt_plugin is currently not installed"
    echo "going to install it via:"
    # more about the plugin: https://github.com/vagrant-libvirt/vagrant-libvirt
    vagrant plugin install $libvirt_plugin
fi

