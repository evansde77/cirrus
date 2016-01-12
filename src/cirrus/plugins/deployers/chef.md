### Chef Deployer Documentation

The chef deployer plugin performs the following actions:

- Given configuration pointing to attributes in roles or environments it connects to the chef server and sets those attributes to the current package version. 
- It then runs chef-client on a set of nodes specified either as a list or as a chef search query
- Optionally it also makes the environment or role change to a copy of the chef-repo so that it can be merged or PR'ed and keep the repo and server in sync. 

Much of how this plugin works is driven by configuration in the cirrus.conf or CLI options. 


#### Command Line Options 

You must specify one of role or environment and the attribute to modify. 

* --environment/-e - Envoronment to modify with the version
* --role/-r - Role to modify with the version
* --attribute/-a - Required - dot delimited attribute names to be overridden with the package version, comma separated list, will be used to modify the override_attributes section of the role or environment. 
* --chef-repo - Optional. Path to git cloned chef-repo to update if desired
* --chef-server - URL of chef server, can also be provided in cirrus.conf
* --chef-username - Username to access the chef server
* --chef-keyfile - SSH Key file to access the chef server
* --nodes-list - List of nodes to execute chef-client on 

#### cirrus.conf file options 

Config file options, added in a ```[chef]``` section of the cirrus.conf:

 * environment - Name of environment to edit
 * role - Name of role to edit
 * node_list - Comma separated list of node host names to run chef-client on 
 * query - Query to find nodes to run chef-client (eg if you want all nodes in the env), is passed to chef search. 
 * query_attribute - Query attribute to extract for each node (IE the hostname)
 * query_format_str - Optional format string to modify each query result (eg to add a common domain postfix etc) 
 * chef_repo - Optional, path to chef repo git clone
 * chef_server - Chef Server URL 
 * chef_username - user name to access chef-server
 * chef_keyfile - SSH Key file path to access chef-server
 * attributes - comma separated, dot delimited attributes under override_attributes to set to the version. 


Example:

The following config example instructs the deploy plugin to do the following:

- Edit the testing environment on the chef server
  - Set override_attributes.thing.application.version to the current package version   
- Runs a chef search for all nodes in the environment named testing
  - Extracts the *host* attribute for each returned node 
  - formats it into a *host*.cloudant.com format 
  - runs chef-client on each hostname
  
  
```ini
[chef]
query="environment:testing"
query_attribute=host
query_format_str="{}.cloudant.com"
chef_server=https://chef.my.org
chef_username=steve
chef_keyfile=/path/to/steve.pem
attributes=thing.application.version
```

### Example Usage
