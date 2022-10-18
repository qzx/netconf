# IOS XE NetConf documentation
----
## SEE ALSO:
[IOS XE Interfaces](https://github.com/qzx/netconf/blob/main/interfaces.md)  
[IOS XE Static Routes](https://github.com/qzx/netconf/blob/main/static-routes.md)  
[IOS XE Access Lists](https://github.com/qzx/netconf/blob/main/access-lists.md)  

There's additionally a template
[IOS XE YANG DOC Template](https://github.com/qzx/netconf/blob/main/doc_template.md)

### Some notes on NETCONF automation  

We'll be using two libraries to communicate with our devices, and two methods of generating XML configs with python. 
* [Scrapli Netconf](https://scrapli.github.io/scrapli_netconf/)
* [NCClient](https://ncclient.readthedocs.io/en/latest/)

scrapli_netconf is a little bit more forgiving with the namespace declaration in the \<config\> block. That is to say ncclient doesn't really work if the namespace isn't declared:

```xml
<!-- This will work on both ncclient and scrapli_netconf with a c8000v -->
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
	<elements />
</config>

<!-- This will only work with scrapli_netconf NetconfDriver -->
<config>
	<elements />
</config>
```

This might be the results of the following code in ncclient doing something silly when it's absent:
```python
# This function is called on all top level objects.
# This piece of code is also why ncclient will never work with 
#  older IOS 15.x devices, as they only support old RFC4741 NETCONF 
#  and that doesn't tolerate overly verbose namespace headers.
qualify = lambda tag, ns=BASE_NS_1_0: tag if ns is None else "{%s}%s" % (ns, tag)

"""Qualify a *tag* name with a *namespace*, in :mod:`~xml.etree.ElementTree` fashion i.e. *{namespace}tagname*."""
```

The main messages that are used are the hello at the start of any transaction, the get-config rpc
and the edit-config rpc. There are others to explore, and we will do that in a future update to these docs. 
##### Hello
```xml
<!--
	Keep in mind that the end sequence for the hello message is ONLY there for 
	the hello message in modern versions of NETCONF. The end sequence ]]>]]> 
	which was mandated in the original NETCONF spec as the end sequence to
	all message has been removed for that purpose. It only exists in the hello
	message in order to keep backwards compatability
-->

<?xml version="1.0" encoding="utf-8"?>
    <hello xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
        <capabilities>
            <capability>urn:ietf:params:netconf:base:1.0</capability>
        </capabilities>
</hello>]]>]]>

<?xml version="1.0" encoding="utf-8"?>
    <hello xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
        <capabilities>
            <capability>urn:ietf:params:netconf:base:1.1</capability>
        </capabilities>
</hello>]]>]]> 
```
##### Get-Config | source is candidate or running
```xml
<get-config><source><{source}/></source></get-config>
```
##### Edit-Config | target is the config to edit (output from our functions/tmplts)
```xml
<edit-config><target><{target}/></target></edit-config>
```
##### Delete-Config | target is which config block to delete
```xml
<edit-config><target><{target}/></target></edit-config>
```
##### Lock | target is the config source, candidate or running
```xml
<lock><target><{target}/></target></lock>
```
##### Unlock | same target as above
```xml
<unlock><target><{target}/></target></unlock>
```
##### Commit
```xml
<commit/>
```
##### Pure RPC | Message ID must be present, and in sequence
```xml
<rpc xmlns='urn:ietf:params:xml:ns:netconf:base:1.0' message-id='{message_id}'></rpc>
```
##### Validate | source is the config you've written to to validate
```xml
<validate><source><{source}/></source></validate>
```
##### Filter (subtree) | filter type
```xml
<filter type='subtree'></filter>
```
##### Filter (XPath) | xpath is the XPath filter to use
```xml
<filter type='xpath' select='{xpath}'></filter>
```

----
### Python device module
To start with we're going to write a little module for our device to perform actions on our 8000V router. Some things to keep in mind when working with NETCONF and the various clients.

```shell
# c8000v.py is a python library that contains simple functions to interact
# with the device over netconf. We'll implement scrapli_netconf for now
# we're goingt to make a function that takes a list of YANG XML configs til 
# deploy to the router, we'll add an optional bool flag to print everyting 
# We'll also attempt to implement ncclient, both of these should work the same
vim c8000v.py
```
```python
from scrapli_netconf import NetconfDriver
from ncclient import manager
from lxml import etree

# We're also going to import logging for the ncclient cause it's terrible
#import logging
#logger = logging.getLogger('ncclient')
#logger.setLevel(logging.DEBUG)
#ch = logging.StreamHandler()
#ch.setLevel(logging.DEBUG)
#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#ch.setFormatter(formatter)
#logger.addHandler(ch)


# ncclient and scrapli_netconf use slightly different config blocks
c8000v_scrapli = {
    "host": "8000v",
    "auth_username": "cisco",
    "auth_password": "cisco",
    "auth_strict_key": False,
    "port": 830
}

c8000v_ncclient = {
    "host": "8000v",
    "username": "cisco",
    "password": "cisco",
    "hostkey_verify": False,
    "port": 830,
    "timeout": 30,
    "device_params": {"name": "iosxe"}
}

scrapli_conn = NetconfDriver(**c8000v_scrapli)

def scrapli_configure(cfgs):
	scrapli_conn.open()
	print(scrapli_conn.lock(target="candidate").result)
	for cfg in cfgs:
		config = stringconfig(cfg)
		print('sending config: {config}'.format(config=config))
		print(scrapli_conn.edit_config(config=config, target="candidate").result)
	print(scrapli_conn.commit().result)
	print(scrapli_conn.unlock(target="candidate").result)
	scrapli_conn.close()

def ncclient_configure(cfgs):
	with manager.connect(**c8000v_ncclient) as m:
		assert(":candidate" in m.server_capabilities)
		with m.locked(target="candidate"):
			m.discard_changes()
			for cfg in cfgs:
				config = stringconfig(cfg)
				edit = m.edit_config(target="candidate", config=config)
				if "<ok />" not in edit.xml:
					print(edit.xml)
				else:
					print("<ok />")
			m.commit()


# stringconf is here to check if we're sending config directly from a 
# rendered template (so string on return from the function) or a etree
# function, which returns xml.etree elements, but we don't want to 
# unpack them before the function returns, so we can pretty print
# the contents if we desire in our client code
def stringconfig(cfg):
	if type(cfg) == str:
		return cfg
	else:
		return etree.tostring(cfg).decode()
```

### Python script to get config
```shell
# The following python script can be used to get the XML config block
# for a desired xpath
# the script starts from /config/native as we'll only be working with said model
# Examples:
# # Get all static routes
# $> get_config.py ip/route 
# # Get specific interface
# $> get_config.py interface/GigabitEthernet[name=1]
vim get_native_config.py
```
```python
from scrapli_netconf import NetconfDriver
import argparse
import sys

c8000v = {
    "host": "8000v",
    "auth_username": "cisco",
    "auth_password": "cisco",
    "auth_strict_key": False,
    "port": 830
}

conn = NetconfDriver(**c8000v)

def getconfig(xpath):
    conn.open()
    #print(conn.get_config(source="running").result)
    print(conn.get_config(filter_=xpath, filter_type="xpath").result)
    conn.close()

def main():
    """Main method to configure a subinterface."""
    parser = argparse.ArgumentParser()
    parser.add_argument('filter',
	    help="""XPath filter to get IOS XE Native config
Note: The path is already prefixed with /native/
Examples:
	python get_config.py vrf/definition[name=\"mgmt\"]
	python get_config.py ntp
	python get_config.py router/bgp
	""",
	    type=str
	)
    args = parser.parse_args()

    # check for valid VLAN ID
    if len(args.filter) < 2:
        parser.print_usage()
        print("""Invalid filter: {filter}
        
	Note: The filter path is already prepended with /native/
	This means the input path does not start with a /
	so in order to get ip route info the filter is:
		ip/route
	likewise, in order to get a specific interface
		interface/GigabitEthernet[name=1]
        
        """.format(filter=args.filter))
        sys.exit()
        
    getconfig('/native/{filter}'.format(filter=args.filter))

if __name__ == '__main__':
    sys.exit(main())
```
----
## NETCONF Snippets

### Python Preparation Snippets
See individual object configurations for implementations
##### Build config with lxml.etree
```python
from lxml import etree

def setInterfaceIPConfig(intf_type, name, desc, addr, mask):
	# build xml
	config_e = etree.Element("config",
		nsmap = {None: 'urn:ietf:params:xml:ns:netconf:base:1.0'}
	)
	# <native><interfaces><GigabitEthernet>
	configuration = etree.SubElement(config_e, "native",
		nsmap = {None: 'http://cisco.com/ns/yang/Cisco-IOS-XE-native'}
	)
	interface_cfg = etree.SubElement(configuration, "interface")
	giginterface_cfg = etree.SubElement(interface_cfg, intf_type)
	# Configure name and description
	etree.SubElement(giginterface_cfg, "name").text = name	
	etree.SubElement(giginterface_cfg, "description").text  = desc
	# <ip><address><primary>
	ip = etree.SubElement(giginterface_cfg,"ip")
	address = etree.SubElement(ip, "address")
	primary = etree.SubElement(address, "primary")
	# configure address and mask
	etree.SubElement(primary, "address").text = addr
	etree.SubElement(primary, "mask").text = mask
	return config_e
	

def setInterfaceNatDirection(intf_type, name, nat_direction):
	config_e = etree.Element("config",
		nsmap = {None: 'urn:ietf:params:xml:ns:netconf:base:1.0'}
	)
	# <native><interfaces><GigabitEthernet>
	configuration = etree.SubElement(config_e, "native",
		nsmap = {None: 'http://cisco.com/ns/yang/Cisco-IOS-XE-native'}
	)
	interface_cfg = etree.SubElement(configuration, "interface")
	giginterface_cfg = etree.SubElement(interface_cfg, intf_type)
	# name is required to select the right interface 
	etree.SubElement(giginterface_cfg, "name").text = name	
	# <ip><nat>
	ip = etree.SubElement(giginterface_cfg,"ip")
	nat = etree.SubElement(ip, "nat",
		nsmap = {None: 'http://cisco.com/ns/yang/Cisco-IOS-XE-nat'}
	)
	# configure nat direction
	etree.SubElement(nat, nat_direction)
	return config_e
```

###### Python Class to Generate Configs
```python
from lxml import etree

class iosXENative():
    def __init__(self):
        self.config = etree.Element("config",
			nsmap = {None: 'urn:ietf:params:xml:ns:netconf:base:1.0'}
		)
        self.native = etree.SubElement(self.config, "native",
            nsmap = {None: 'http://cisco.com/ns/yang/Cisco-IOS-XE-native'}
        )
        self.interfaces = etree.SubElement(self.native, "interface")
        self.interface_config = {}
        self.intf_ip_is_enabled = {}

    def __str__(self):
        return etree.tostring(self.config, pretty_print=True).decode()

    def __repr__(self):
        return etree.tostring(self.config).decode()

    def newInterfaceConfig(self, intf_type, name, desc="default desc"):
        interface_id = "{intf_type}{name}".format(
	        intf_type=intf_type,
	        name=name)
	        
        self.interface_config[interface_id] = etree.SubElement(
	        self.interfaces,
	        intf_type)
	        
        etree.SubElement(
	        self.interface_config[interface_id],
	        "name").text = name
	        
        etree.SubElement(
	        self.interface_config[interface_id],
		    "description").text  = desc
		    
        return interface_id

    def setInterfaceNat(self, interface_id, nat_direction=None):
        self._intf_ip_enabled(interface_id)
        
        if nat_direction is None:
            etree.SubElement(
	            self.intf_ip_is_enabled[interface_id],
	            "nat",
	            operation="remove",
                nsmap = {None: 'http://cisco.com/ns/yang/Cisco-IOS-XE-nat'}
            )
        else:
            nat = etree.SubElement(
	            self.intf_ip_is_enabled[interface_id],
	            "nat",
                nsmap = {None: 'http://cisco.com/ns/yang/Cisco-IOS-XE-nat'}
            )
            etree.SubElement(nat, nat_direction)

    def setInterfaceIP(self, interface_id, addr, mask):
        self._intf_ip_enabled(interface_id)
        
        address = etree.SubElement(
	        self.intf_ip_is_enabled[interface_id],
	        "address")
	        
        primary = etree.SubElement(address, "primary")
        # configure address and mask
        etree.SubElement(primary, "address").text = addr
        etree.SubElement(primary, "mask").text = mask

    def _intf_ip_enabled(self, ip_id):
        if ip_id in self.intf_ip_is_enabled:
            return
        else:
            self.intf_ip_is_enabled[ip_id] = etree.SubElement(
	            self.interface_config[ip_id],
	            "ip")
            return
```

### Device Configuration
----
There are two main ways of configuring an interface on an IOS-XE utilizing YANG datamodels. The choices are NETCONF and RESTCONF. We will explore each object we need to manage based on each of these criteria:

### Basic System Configuration
----
##### Create VLAN (id)
```xml
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
	<native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
	    <vlan>
		    <vlan-list xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-vlan">
			    <id>{{ id }}</id>
			</vlan-list>
		</vlan>
	</native>
</config>
```

##### Delete VLAN (id)
```xml
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
	<native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
	    <vlan>
			<vlan-list xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-vlan" operation="remove">
		        <id>{{ id }}</id>
		    </vlan-list>
	    </vlan>
	</native>
</config>
```

##### Configure NTP (Set)
```xml
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
	<native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
		<ntp>
			<server xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-ntp">
				<server-list>
					<ip-address>{{ ip_address }}</ip-address>
				</server-list>
			</server>
		</ntp>
	</native>
</config>
```

##### Configure NTP (Delete)
```xml
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
	<native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
		<ntp>
			<server xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-ntp">
				<server-list operation="remove">
					<ip-address>{{ ip_address }}</ip-address>
				</server-list>
			</server>
		</ntp>
	</native>
</config>
```


