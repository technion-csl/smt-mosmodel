MODULE_NAME := virtualized_experiments
SUBMODULES := #general_metrics
SUBMODULES := $(addprefix $(MODULE_NAME)/,$(SUBMODULES))

export NUMBER_OF_SOCKETS := $(shell ls -d /sys/devices/system/node/node*/ | wc -w)
export NUMBER_OF_CORES_PER_SOCKET := $(shell ls -d /sys/devices/system/node/node0/cpu*/ | wc -w)
export MEMORY_PER_SOCKET_KB := $(shell cat /sys/devices/system/node/node0/meminfo | \grep MemTotal | cut -d":" -f 2 | tr -d "[ kB]")
export MEMORY_PER_SOCKET_MB := $(shell echo $$(( $(MEMORY_PER_SOCKET_KB) / 1024 )) )

dummy:
	echo num-sockets = $(NUMBER_OF_SOCKETS)
	echo num-cores-per-socket = $(NUMBER_OF_CORES_PER_SOCKET)
	echo memory-per-socket-mb = $(MEMORY_PER_SOCKET_MB)

# we change the directory where Vagrant stores global state because it is set to ~/.vagrant.d
# by default, and this causes conflicts between servers as the ~ directory is mounted on NFS.
export VAGRANT_HOME := $(ROOT_DIR)/$(MODULE_NAME)/.vagrant.d
VAGRANT_STORE := $(ROOT_DIR)/$(MODULE_NAME)/.vagrant
VAGRANT_FILE := $(MODULE_NAME)/Vagrantfile
CLONE_REPOSITORY_SCRIPT := $(ROOT_DIR)/$(MODULE_NAME)/cloneRepository.sh
REPOSITORY_IS_CLONED := $(ROOT_DIR)/$(MODULE_NAME)/repository_is_cloned

$(MODULE_NAME): $(REPOSITORY_IS_CLONED)
	cd $@
	vagrant up --provider=libvirt
	vagrant ssh
	vagrant halt

vagrant-ubuntu1804:
	mkdir vagrant
	cd vagrant
	vagrant init generic/ubuntu1804
	vagrant up
	vagrant halt

$(REPOSITORY_IS_CLONED): $(VAGRANT_FILE) | vagrant
	# The Vagrantfile defines the configuration of the VM that resides in the current directory.
	# Fresh Vagrantfile can be created through: vagrant init generic/ubuntu1604
	# where generic/ubuntu1604 is the box name (all boxes are at: https://app.vagrantup.com/boxes/search)
	cd $(dir $@)
	vagrant up --provider=libvirt
	vagrant ssh -c "cd $(ROOT_DIR) && $(CLONE_REPOSITORY_SCRIPT)"
	vagrant ssh -c "touch $@"
	vagrant halt

$(MODULE_NAME)/clean: | vagrant
	cd $(dir $@)
	virsh list --all
	vagrant destroy --force
	virsh list --all
	# in case vagrant destroy doesn't work, try using virsh directly:
	# virsh undefine virtualized_experiments_$(HOST_NAME)
	rm -f $(REPOSITORY_IS_CLONED)

##### recipes and rules for prerequisites

.PHONY: libvirt vagrant libvirt-uninstall vagrant-uninstall

INSTALL_VAGRANT_SCRIPT := $(MODULE_NAME)/installVagrant.sh
vagrant: | libvirt
	$(INSTALL_VAGRANT_SCRIPT)

LIBVIRT_PACKAGES := libvirt-bin libvirt-dev qemu-kvm
SETUP_LIBVIRT_SCRIPT := $(MODULE_NAME)/setupLibvirt.sh
QEMU_BINARY := /usr/bin/qemu-system-x86_64
SET_CAPABILITIES := sudo setcap cap_sys_rawio+ep
QUERY_PACKAGES_SCRIPT := $(MODULE_NAME)/queryPackages.sh
libvirt:
	$(QUERY_PACKAGES_SCRIPT) "$(LIBVIRT_PACKAGES)"
	$(SETUP_LIBVIRT_SCRIPT)
	if [[ ! -f $(QEMU_BINARY) ]]; then echo "Error: qemu not found!"; fi
	$(SET_CAPABILITIES) $(QEMU_BINARY)

# if we uninstall libvirt, there is no point in keeping vagrant
libvirt-uninstall: | vagrant-uninstall
	sudo apt-get remove -y --purge $(LIBVIRT_PACKAGES)

vagrant-uninstall:
	rm -rf $(VAGRANT_HOME) $(VAGRANT_STORE)
	sudo dpkg --purge vagrant
	sudo rm -rf /opt/vagrant /usr/bin/vagrant
	rm -rf ~/.vagrant.d

include $(ROOT_DIR)/common.mk

