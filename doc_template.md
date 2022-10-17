----
Generic Object config template
----
##### Jinja template
```shell
# We can create a template for object creation
# This is in Jinja2 syntax to render XML
vim templates/ios-xe----SOME-YANG----.xml.j2
```
```jinja2
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
    
  </native>
</config>
```
```shell
# Then we can create a shell script to render the template
vim ios-xe----SOME-YANG-----.py
```
```python
from jinja2 import Environment, FileSystemLoader

environment = Environment(loader=FileSystemLoader("templates/"))
template = environment.get_template("ios-xe-static----SOME-YANG----.xml.j2")

config = template.render(
	param="FOO",
)
print(config)
#import c8000v
#c8000v.ncclient_configure([config])
```
##### lxml etree to build config
```shell
# The above template and render is equivalent to the following python script
vim ios-xe----SOME-YANG----lxml.py
```
```python
from lxml import etree
def iosXE___FUNCTION___():
	config = etree.Element("config",
		nsmap = {None: 'urn:ietf:params:xml:ns:netconf:base:1.0'}
	)
	# <native><interfaces><GigabitEthernet>
	native = etree.SubElement(config, "native",
		nsmap = {None: 'http://cisco.com/ns/yang/Cisco-IOS-XE-native'}
	)
	
	return config
	
config = iosXE___FUNCTION___(
	param="FOO",
)

print(etree.tostring(config, pretty_print=True).decode())
#import c8000v
#c8000v.ncclient_configure([config])
```
##### Resulting RESTCONF XML
These produce the same output which can be used directly in a scrapli_netconf call to edit_config the NETCONF message will look like this:

```xml
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
    <!-- actual configuration goes here -->
  </native>
</config>
```


##### Delete object 
```xml
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
	    <!-- put operation="remove" into the parent block you want to clear -->
  </native>
</config>
```
