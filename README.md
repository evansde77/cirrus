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
