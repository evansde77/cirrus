cirrus
======

python library build, test and devop like things assistant


Installation as a user:
=======================
Note: Prior to doing this step, you will need to have added your public key to GitHub so that you can clone the cirrus repo. See [this howto](https://help.github.com/articles/generating-ssh-keys) for details.


```bash
curl -O https://raw.githubusercontent.com/evansde77/cirrus/develop/installer.sh
bash installer.sh
```

The installer script will set up an install of cirrus for you in your home directory 
and prompt for some info so that it can set up some parameters in your .gitconfig 



Installation for Development:
=============================

_Note_: This package uses GitFlow, any development work should be done off the develop branches and 
pull requests made against develop, not master. 

```bash
git clone https://github.com/evansde77/cirrus.git 
git cirrus build
```


User Configuration File:
========================

As cirrus works as a git extension, it will use your gitconfig file. The installer will create a cirrus section in this file and create the following settings:

1. *github-user* - Your Github Username
1. *github-token* - A github access token
1. *pypi-user* - Username of your pypi server
1. *pypi-token* - Token/password to access your pypi server
1. *pypi-ssh-key* - SSH key used for scp-like uploads to your pypi server (if HTTP upload isnt supported)


Package Configuration Files:
============================

The per package controls used by cirrus live in a cirrus.conf file in the top level of the repo you use with cirrus. 
This file, coupled with the cirrus setup.py template and command line tools dictate the behaviour of the cirrus commands within the package. Details for the cirrus config are in the (TBA) Configuration.MD file


Cirrus Commands:
================ 

