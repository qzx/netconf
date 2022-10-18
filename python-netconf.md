# Python NETCONF
----
Now that we've understood somewhat how the NETCONF communications are handled, let us introduce python to help us get more robust. We'll start by creating a small library that can configure our device. We'll implement both available libraries for kicks.

## Connectivity
----
##### Python module to interact with our device
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
from ncclient import manager, xml_
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


# Set up couple of constants we might want to use
CANDIDATE = "urn:ietf:params:netconf:capability:candidate:1.0"
RUNNING = "urn:ietf:params:netconf:capability:writable-running:1.0"

# scrapli_netconf doesn't implement the save-config RPC
# We'll need to send the following string as a raw RPC call
save_rpc = '<save-config xmlns="http://cisco.com/yang/cisco-ia"/>'
def scrapli_save():
	scrapli_conn.open()
	print(scrapli_conn.rpc(filter_=save_rpc).result)
	scrapli_conn.close()

# ncclient adds the save_config function when we declare our deice as iosxe
def ncc_save():
	with manager.connect(**c8000v_ncclient) as m:
		m.save_config()

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
	if CANDIDATE in scrapli_conn.server_capabilities:
		print(scrapli_conn.lock(target="candidate").result)
		for cfg in cfgs:
			config = stringconfig(cfg)
			print('sending config: {config}'.format(config=config))
			print(scrapli_conn.edit_config(
				config=config,
				target="candidate").result)
				
		print(scrapli_conn.commit().result)
		print(scrapli_conn.unlock(target="candidate").result)
		
	elif RUNNING in scrapli_conn.server_capabilities:
		print(scrapli_conn.lock(target="running").result)
		for cfg in cfgs:
			config = stringconfig(cfg)
			print('sending config: {config}'.format(config=config))
			print(scrapli_conn.edit_config(
				config=config,
				target="running").result)
		print(scrapli_conn.unlock(target="running").result)
	scrapli_conn.close()



# Implement the ncclient to configure our device
def ncclient_configure(cfgs):
	with manager.connect(**c8000v_ncclient) as m:
		# In order to avoid headaches, we'll just add logic to select config
		if ":candidate" in m.server_capabilities:
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
		# Using an elif here also breaks us out if the device has neither ability
		elif ":writable-running" in m.server_capabilities:
			with m.locked(target="running"):
				for cfg in cfgs:
					config = stringconfig(cfg)
					edit = m.edit_config(target="running", config=config)
					if "<ok />" not in edit.xml:
						print(edit.xml)
					else:
						print("<ok />")


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

now that we're set up to send configuration blocks to our device and save the config when we're done, lets start building some configs. 

## Creating new config
To make our life easy, we'll start by writing another small script that can fetch configuration for us based on a XPath filter. We're going to mostly explore the IOS-XE Native YANG model, so we'll just take care of that part of the path in our script as well. (We'll explore openconfig and ietf later)
```shell
# Shell script to get config under /native/ xpath
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

Now we can grab small chunks of config, let's grab the hostname and ip settings:
##### Getting configs based on XPath
```shell
$ python get_native_config.py ip/http
<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="101">
  <data>
    <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
      <ip>
        <http xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-http">
          <server>false</server>
          <secure-server>false</secure-server>
        </http>
      </ip>
    </native>
  </data>
</rpc-reply>

$ python get_native_config.py hostname
<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="101">
  <data>
    <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
      <hostname>8000v</hostname>
    </native>
  </data>
</rpc-reply>
```

Oh, look at that, http secure server isn't enabled... lets enable that by creating a config request.
The configuration request needs to be wrapped in a config block and declare the netconf ns
##### Configuration request wrapper
```xml
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
	<elements />
</config>
```
##### XML Datablock to send in order to change config
```xml
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
	<native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
      <ip>
        <http xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-http">
          <secure-server>true</secure-server>
        </http>
      </ip>
    </native>
</config>
```

Now that we've got our desired config change, let's use our module to send the config

##### Sending config with python
```python
# we start by importing our little library
import c8000v

# declare the config we want to send
config = """<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
	<native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
      <ip>
        <http xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-http">
          <secure-server>true</secure-server>
        </http>
      </ip>
    </native>
</config>"""

# remember that our function takes a list
configs = [config]

# configure the router
c8000v.scrapli_configure(configs)

# finally write to startup-config
c8000v.scrapli_save()
```

Great, we're now set up to build our router config with YANG and NETCONF. Let's create a short dev cycle to explore configuration elements, create templates and configure our devices.

## Python NETCONF Development cycle
----
We'll start by configuring two dummy ntp servers so we can see what the config looks like. We don't care about most features at this time, but if we wanted to deal with VRFs for instance, we'd want to configure that on box too before getting the config.

### Get the relevant config block from device
```shell
# We want to configure NTP, but we're not sure where it is
# our script already prefixes /native/ to our filter string
$ python get_native_config.py ntp
<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="101">
  <data>
    <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
      <ntp>
        <server xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-ntp">
          <server-list>
            <ip-address>1.1.1.1</ip-address>
          </server-list>
          <server-list>
            <ip-address>1.1.1.2</ip-address>
          </server-list>
        </server>
      </ntp>
    </native>
  </data>
</rpc-reply>
```

We can now translate this into a template. We just need to identify our variables and loops. Our variables here are the IP addresses of the given NTP servers, and our looping point is on the  server-list object.

### Create a jinja2 template
```shell
# Then we can create a shell script to render the template
vim templates/ios-xe-native-ntp.xml.j2
```
```jinja2
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
    <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
      <ntp>
        <server xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-ntp">
          {%- for addr in servers %}
          <server-list>
            <ip-address>{{ addr }}</ip-address>
          </server-list>
          {%- endfor %}
        </server>
      </ntp>
    </native>
</config>
```

Ok, that was relatively painless, we just had to replace the rpc-reply and data tags with the config tag and introduce loops and variables. Our template will take a list called servers which should contain IP addresses

### Use jinja2 template to configure device
```shell
# Then we can create a shell script to render the template
vim ios-xe-native-ntp.py
```
```python
from jinja2 import Environment, FileSystemLoader

environment = Environment(loader=FileSystemLoader("templates/"))
template = environment.get_template("ios-xe-native-ntp.xml.j2")

config = template.render(
	servers=["162.159.200.1", "185.181.223.169"]
)
print(config)
#import c8000v
#c8000v.ncclient_configure([config])
```

We can run the script as is to see that we're generating the config block we want. We could then wrap this with the RPC tag and send it to the device over the raw SSH connection we explored earlier, or just send it with the python module we built.

##### Template config output
```shell
$ python ios-xe-native-ntp.py
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
    <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
      <ntp>
        <server xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-ntp">
          <server-list>
            <ip-address>162.159.200.1</ip-address>
          </server-list>
          <server-list>
            <ip-address>185.181.223.169</ip-address>
          </server-list>
        </server>
      </ntp>
    </native>
</config>
```

Looks good... but if we don't want templates to keep track of and prefer to do things all in code, could we do that?... Sure can, introducing lxml.etree. Not my favorite library, but it can get the job done for us here. 

Small note on using lxml.etree, scrapli_netconf takes strings as input, where ncclient can take either strings or lxml.etree elements. To make life easier for us, we've added a function in our module to cast lxml.etree elements as strings prior to sending to our device.

### Explore lxml.etree as alternative to templates
```shell
# The above template and render is equivalent to the following python script
vim ios-xe-native-ntp-lxml.py
```
```python
from lxml import etree
def iosXEntp(servers=[]):
	config = etree.Element("config",
		nsmap = {None: 'urn:ietf:params:xml:ns:netconf:base:1.0'}
	)
	# <native><interfaces><GigabitEthernet>
	native = etree.SubElement(config, "native",
		nsmap = {None: 'http://cisco.com/ns/yang/Cisco-IOS-XE-native'}
	)

	# Create the ntp and server children
	ntp = etree.SubElement(native, "ntp")
	server = etree.SubElement(ntp, "server",
		nsmap = {None: 'http://cisco.com/ns/yang/Cisco-IOS-XE-ntp'}
	)

	# Loop in the same place and assign our variable to the ip-address field
	for addr in servers:
		entry = etree.SubElement(server, "server-list")
		etree.SubElement(entry, "ip-address").text = addr
	
	return config
	
config = iosXEntp(
	servers=["162.159.200.1", "185.181.223.169"]
)

print(etree.tostring(config, pretty_print=True).decode())
#import c8000v
#c8000v.ncclient_configure([config])
```

When we subsequently run this script, we should have identical output to the one based on the template from before:
##### LXML created config output
```shell
$ python ios-xe-native-ntp-lxml.py
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
    <ntp>
      <server xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-ntp">
        <server-list>
          <ip-address>162.159.200.1</ip-address>
        </server-list>
        <server-list>
          <ip-address>185.181.223.169</ip-address>
        </server-list>
      </server>
    </ntp>
  </native>
</config>
```

Great! We now have two methods of creating configuration objects. Lets bring it home by applying our configuration and reading it back. We just uncomment the bottom two lines in either script to send the config to our device

##### Configure and read
```shell
$ python ios-xe-native-ntp-lxml.py
<?xml version="1.0" encoding="UTF-8"?>
<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="urn:uuid:3bbb69c4-309c-49d3-bb1f-452f05b20bfb" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0"><ok/></rpc-reply>


$ python get_native_config.py ntp
<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="101">
  <data>
    <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
      <ntp>
        <server xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-ntp">
          <server-list>
            <ip-address>1.1.1.1</ip-address>
          </server-list>
          <server-list>
            <ip-address>1.1.1.2</ip-address>
          </server-list>
          <server-list>
            <ip-address>162.159.200.1</ip-address>
          </server-list>
          <server-list>
            <ip-address>185.181.223.169</ip-address>
          </server-list>
        </server>
      </ntp>
    </native>
  </data>
</rpc-reply>
```

Oooh my... /that/ wasn't what we wanted. Turns out that by default config sent to the device will just get added, our prior config is still there as well. But we don't want that, we want our NETCONF configuration to be replace the NTP config with our own.  
This is can be done with the operation keyword. 

##### Updated template to REPLACE the config on the device
```jinja2
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
    <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
      <ntp>
        <server xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-ntp" operation="replace">
          {%- for addr in servers %}
          <server-list>
            <ip-address>{{ addr }}</ip-address>
          </server-list>
          {%- endfor %}
        </server>
      </ntp>
    </native>
</config>
```

##### Updated lxml.etree to REPLACE the config on device
```python
from lxml import etree
def iosXEntp(servers=[]):
	config = etree.Element("config",
		nsmap = {None: 'urn:ietf:params:xml:ns:netconf:base:1.0'}
	)
	# <native><interfaces><GigabitEthernet>
	native = etree.SubElement(config, "native",
		nsmap = {None: 'http://cisco.com/ns/yang/Cisco-IOS-XE-native'}
	)

	# Create the ntp and server children
	ntp = etree.SubElement(native, "ntp")
	server = etree.SubElement(ntp, "server",
		nsmap = {None: 'http://cisco.com/ns/yang/Cisco-IOS-XE-ntp'},
		operation = "replace"
	)

	# Loop in the same place and assign our variable to the ip-address field
	for addr in servers:
		entry = etree.SubElement(server, "server-list")
		etree.SubElement(entry, "ip-address").text = addr
	
	return config
	
config = iosXEntp(
	servers=["162.159.200.1", "185.181.223.169"]
)

#print(etree.tostring(config, pretty_print=True).decode())
import c8000v
c8000v.ncclient_configure([config])
```

Now when we run our script again, and then get the config, we should have what we want:

##### Sending config with operation="replace" 
```shell
$ python ios-xe-native-ntp-lxml.py
<?xml version="1.0" encoding="UTF-8"?>
<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="urn:uuid:ff8a364f-28c3-4de7-b90b-f8f6dd5de198" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0"><ok/></rpc-reply>

$ python get_native_config.py ntp
<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="101">
  <data>
    <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
      <ntp>
        <server xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-ntp">
          <server-list>
            <ip-address>162.159.200.1</ip-address>
          </server-list>
          <server-list>
            <ip-address>185.181.223.169</ip-address>
          </server-list>
        </server>
      </ntp>
    </native>
  </data>
</rpc-reply>

```

That was a lot of fun... we can now create these structures for various elements:

[IOS XE Interfaces](https://github.com/qzx/netconf/blob/main/interfaces.md)  
[IOS XE Static Routes](https://github.com/qzx/netconf/blob/main/static-routes.md)  
[IOS XE Access Lists](https://github.com/qzx/netconf/blob/main/access-lists.md) 
