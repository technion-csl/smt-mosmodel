#! /bin/bash

if (( "$#" < 1 )); then
    echo "Usage: $0 LIST_OF_PACKAGES"
    exit -1
fi

packages="$@"
for package in $packages; do
    status=$(dpkg-query --show --showformat='${Status}' $package)
    if [[ $status == "install ok installed" ]]; then
        echo "The package $package is installed."
    else
        echo "The package $package is not currently installed."
        echo "Going to install it via:"
        sudo apt-get install -y $package
    fi
done

