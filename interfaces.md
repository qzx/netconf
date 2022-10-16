# Interfaces
----
### Interface IP and Desc
----
##### Jinja template
```shell
# We can create a template for Interface creation
# This is in Jinja2 syntax to render XML
vim templates/ios-xe-native-interface.xml.j2
```
```jinja2
<config>
  <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
    <interface>
	  <{{intf_type}}>             
        <name>{{name}}</name>
        <description>{{desc}}</description>
        {%- if shutdown %}
        <shutdown/>
        {%- else %}
        <shutdown operation="remove"/>
        {%-endif %}
        <ip>
          <address>
            <primary>
              <address>{{addr}}</address>
              <mask>{{mask}}</mask>
            </primary>
          </address>
        </ip>
      </{{intf_type}}>
    </interface>
  </native>
</config>
```
```shell
# Then we can create a shell script to render the template
vim ios-xe-native-interface.py
```
```python
from jinja2 import Environment, FileSystemLoader

environment = Environment(loader=FileSystemLoader("templates/"))
template = environment.get_template("ios-xe-native-interface.xml.j2")

config = template.render(
	intf_type="GigabitEthernet", 
	name="4",
	addr="10.10.10.1",
	mask="255.255.255.0",
	desc="Yanging around",
	shutdown=False
)
print(config)
```
##### lxml etree to build config
```shell
# The above template and render is equivalent to the following python script
vim ios-xe-native-interface-lxml.py
```
```python
from lxml import etree
def iosXEInterface(intf_type, name, desc, addr, mask, shutdown=False):
	config = etree.Element("config")
	# <native><interfaces><GigabitEthernet>
	native = etree.SubElement(config, "native",
		nsmap = {None: 'http://cisco.com/ns/yang/Cisco-IOS-XE-native'}
	)
	interfaces = etree.SubElement(native, "interface")
	typed_intf = etree.SubElement(interfaces, intf_type)
	# Configure name and description
	etree.SubElement(typed_intf, "name").text = name	
	etree.SubElement(typed_intf, "description").text  = desc
	if shutdown == True:
		etree.SubElement(typed_intf, "shutdown")
	else:
		etree.SubElement(typed_intf, "shutdown", operation="remove")
	# <ip><address><primary>
	ip = etree.SubElement(typed_intf,"ip")
	address = etree.SubElement(ip, "address")
	primary = etree.SubElement(address, "primary")
	# configure address and mask
	etree.SubElement(primary, "address").text = addr
	etree.SubElement(primary, "mask").text = mask
	return config
	
config = iosXEInterface(
	intf_type = "GigabitEthernet",
	name = "4",
	addr = "10.10.10.1",
	mask = "255.255.255.0",
	desc = "Yanging around",
	shutdown = False
)

print(etree.tostring(config, pretty_print=True).decode())
```
##### Resulting RESTCONF XML
These produce the same output which can be used directly in a scrapli_netconf call to edit_config the NETCONF message will look like this:

```xml
<config>
  <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
    <interface>
	  <GigabitEthernet>             
        <name>4</name>
        <description>Yanging around</description>
        <shutdown operation="remove"/>
        <ip>
          <address>
            <primary>
              <address>10.10.10.1</address>
              <mask>255.255.255.0</mask>
            </primary>
          </address>
        </ip>
      </GigabitEthernet>
    </interface>
  </native>
</config>
```




### Interface access-lists
----
##### Jinja template
```shell
# We can create a template for Interface creation
# This is in Jinja2 syntax to render XML
vim templates/ios-xe-native-interface-acl.xml.j2
```
```jinja2
<config>
  <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
    <interface>
	  <{{intf_type}}>             
        <name>{{name}}</name>
        <ip>
        {%- if not acl_name or True not in [ins, out] %}
          <access-group operation="remove"/>
        {%- else %}
           <access-group>
           {%- if out %}
	          <out>
                <acl>
                  <acl-name>{{acl_name}}</acl-name>
                  <out/>
                </acl>
              </out>
            {%- endif %}
            {%- if ins %}
              <in>
                <acl>
                  <acl-name>{{acl_name}}</acl-name>
                  <in/>
                </acl>
              </in>
            {%- endif %}
            </access-group>
          {%- endif %}
        </ip>
      </{{intf_type}}>
    </interface>
  </native>
</config>
```
```shell
# Then we can create a shell script to render the template
vim ios-xe-native-interface-acl.py
```
```python
from jinja2 import Environment, FileSystemLoader

environment = Environment(loader=FileSystemLoader("templates/"))
template = environment.get_template("ios-xe-native-interface-acl.xml.j2")

config = template.render(
	intf_type="GigabitEthernet", 
	name="4",
	acl_name="foo"
)

print(config)
```
##### lxml etree to build config
```shell
# The above template and render is equivalent to the following python script
vim ios-xe-native-interface-acl-lxml.py
```
```python
from lxml import etree
def iosXEInterfaceAcl(intf_type, name, acl_name=None, out=False, ins=False):
	config = etree.Element("config")
	# <native><interfaces><GigabitEthernet>
	native = etree.SubElement(config, "native",
		nsmap = {None: 'http://cisco.com/ns/yang/Cisco-IOS-XE-native'}
	)
	interfaces = etree.SubElement(native, "interface")
	typed_intf = etree.SubElement(interfaces, intf_type)
	# Configure name and description
	etree.SubElement(typed_intf, "name").text = name	

	# <ip><address><primary>
	ip = etree.SubElement(typed_intf,"ip")
	if acl_name is None or True not in [ins, out]:
		aclgrp = etree.SubElement(ip, "access-group", operation="remove")
	else:
		aclgrp = etree.SubElement(ip, "access-group")
		if out:
			direction = etree.SubElement(aclgrp, "out")
			acl = etree.SubElement(direction, "acl")
			etree.SubElement(acl, "acl-name").text = acl_name
			etree.SubElement(acl, "out")
		if ins:
			direction = etree.SubElement(aclgrp, "in")
			acl = etree.SubElement(direction, "acl")
			etree.SubElement(acl, "acl-name").text = acl_name
			etree.SubElement(acl, "in")
		
	return config
	
config = iosXEInterfaceAcl(
	intf_type = "GigabitEthernet",
	name = "4",
	acl_name = "foo",
	ins=True
)

print(etree.tostring(config, pretty_print=True).decode())
```
##### Resulting RESTCONF XML
These produce the same output which can be used directly in a scrapli_netconf call to edit_config the NETCONF message will look like this:

```xml
<config>
  <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
    <interface>
      <GigabitEthernet>
        <name>4</name>
        <ip>
          <access-group>
            <out>
              <acl>
                <acl-name>foo</acl-name>
                <out/>
              </acl>
            </out>
          </access-group>
        </ip>
      </GigabitEthernet>
    </interface>
  </native>
</config>
```
