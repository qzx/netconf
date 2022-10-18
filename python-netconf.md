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

# neither client implements cisco's save-config RPC
# We'll need to send the following string as a raw RPC call
save_rpc = '<save-config xmlns="http://cisco.com/yang/cisco-ia"/>'
def scrapli_save():
	scrapli_conn.open()
	print(scrapli_conn.rpc(filter_=save_rpc).result)
	scrapli_conn.close()

def ncc_save():
	with manager.connect(**c8000v_ncclient) as m:
		m.dispatch(xml_.to_ele(save_rpc))

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
