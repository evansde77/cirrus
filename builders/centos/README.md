# CI Containers

Example/base docker container for installing and running cirrus in 
a docker container for CI builds etc. 
The image is based off centos:latest and you can customise it to 
add extra packages via yum for dependencies as well 
as ssh configuration and keys for connecting to repos.

Cirrus is installed in a virtualenv for the cirrus user in /home/cirrus and a basic set of config files including gitconfig, pip and pypirc files are added. 

## Building Image

The build command will accept a version of python (supported via pyenv) and defaults to 3.6.6. 

Building with py3.6:

```bash
docker build -t cirrus-centos-py36:latest 
```

Building with py3.7:

```bash
docker build -t cirrus-centos-py37:latest --build-arg PYTHON_VERSION=3.7.2  .
```

### Extending the image 

#### yum repos & packages
To extend the image with custom yum dependencies, create a Dockerfile that extends the base python version
and add yum repo files in /etc/yum.repos.d and then yum update/install in that dockerfile as needed. 

#### ssh configuration 

To add SSH keys etc, add them to the ssh dir and modify the config file in there as needed before building. 


## Running the image

To run a cirrus command on a repo with the container, you will need to run the container and mount the repository as /repo 
then pass the cirrus command and options:

Eg, to run git cirrus hello in a repo in the current dir:

```
docker run -ti -v `pwd`:/repo cirrus-centos-py36:latest  hello 
```


To run a git cirrus build:

```
docker run -ti -v `pwd`:/repo cirrus-centos-py36:latest build  
```

