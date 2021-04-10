#! /bin/bash

# this script should be called from inside the guest VM
# when the current working directory is the NFS directory of the git repository

original_repo=$PWD
new_repo=~/mosalloc
git clone $original_repo $new_repo

