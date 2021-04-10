#! /bin/bash

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y git make gcc g++ gfortran

# install anaconda
anaconda_installer=Anaconda3-2019.07-Linux-x86_64.sh
cd /home/vagrant
if [[ ! -f $anaconda_installer ]]; then
    wget --quiet https://repo.continuum.io/archive/$anaconda_installer
fi
chmod +x $anaconda_installer
./$anaconda_installer -b -p /opt/anaconda

# complete the installation by adding anaconda before the default path
cat >> /home/vagrant/.bashrc << END
PATH=/opt/anaconda/bin:\$PATH
END

