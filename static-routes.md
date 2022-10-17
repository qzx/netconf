# Static Route configuration
----
##### Jinja template
```shell
# We can create a template for Interface creation
# This is in Jinja2 syntax to render XML
vim templates/ios-xe-static-route.xml.j2
```
```jinja2
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
    <ip>
	  <route>
	   {%- if vrf_routes %}
	   <vrf>
	   {%- for vrf in vrf_routes %}
	    <name>{{vrf.name}}</name>
	      {%- for route in vrf.routes %}
          <ip-route-interface-forwarding-list>
            <prefix>{{route.prefix}}</prefix>
            <mask>{{route.mask}}</mask>
            <fwd-list>
              <fwd>{{route.gw}}</fwd>
            </fwd-list>
          </ip-route-interface-forwarding-list>
          {%- endfor %}
         {%- endfor %}
        </vrf>
        {%- endif %}
        {%- if routes %}
        {%- for route in routes %}
        <ip-route-interface-forwarding-list>
          <prefix>{{route.prefix}}</prefix>
          <mask>{{route.mask}}</mask>
          <fwd-list>
            <fwd>{{route.gw}}</fwd>
          </fwd-list>
        </ip-route-interface-forwarding-list>
        {%- endfor %}
        {%- endif %}
      </route>
    </ip>
  </native>
</config>
```
```shell
# Then we can create a shell script to render the template
vim ios-xe-static-route.py
```
```python
from jinja2 import Environment, FileSystemLoader

environment = Environment(loader=FileSystemLoader("templates/"))
template = environment.get_template("ios-xe-static-route.xml.j2")

config = template.render(
	routes = [
		{"prefix":"10.10.10.0", "mask":"255.255.255.0", "gw":"192.168.255.1"},
		{"prefix":"10.10.20.0", "mask":"255.255.255.0", "gw":"192.168.255.1"}
	],
	vrf_routes = [{
		"name": "mgmt",
		"routes": [
		{"prefix":"10.10.30.0", "mask":"255.255.255.0", "gw":"192.168.255.1"},
		{"prefix":"10.10.40.0", "mask":"255.255.255.0", "gw":"192.168.255.1"}
		]
	}
	],
)
print(config)
#import c8000v.py
#c8000v.scrapli_configure([config])
```
##### lxml etree to build config
```shell
# The above template and render is equivalent to the following python script
vim ios-xe-static-route-lxml.py
```
```python
from lxml import etree
def iosXEStaticRoutes(routes=[], vrf_routes=[]):
	config = etree.Element("config",
		nsmap = {None: 'urn:ietf:params:xml:ns:netconf:base:1.0'}
	)
	# <native><interfaces><GigabitEthernet>
	native = etree.SubElement(config, "native",
		nsmap = {None: 'http://cisco.com/ns/yang/Cisco-IOS-XE-native'}
	)
	if len(routes) == 0 and len(vrf_routes) == 0:
		return config
		
	ip = etree.SubElement(native, "ip")
	route_e = etree.SubElement(ip, "route")
	for vrf in vrf_routes:
		vrf_e = etree.SubElement(route_e, "vrf")
		etree.SubElement(vrf_e, "name").text = vrf['name']
		for route in vrf['routes']:
			entry = etree.SubElement(vrf_e, "ip-route-interface-forwarding-list")
			etree.SubElement(entry, "prefix").text = route['prefix']
			etree.SubElement(entry, "mask").text = route['mask']
			etree.SubElement(entry, "gw").text = route['gw']
	for route in routes:
		entry = etree.SubElement(route_e, "ip-route-interface-forwarding-list")
		etree.SubElement(entry, "prefix").text = route['prefix']
		etree.SubElement(entry, "mask").text = route['mask']
		etree.SubElement(entry, "gw").text = route['gw']
	return config
	
config = iosXEStaticRoutes(
	routes = [
		{"prefix":"10.10.10.0", "mask":"255.255.255.0", "gw":"192.168.255.1"},
		{"prefix":"10.10.20.0", "mask":"255.255.255.0", "gw":"192.168.255.1"}
	],
	vrf_routes = [{
		"name": "mgmt",
		"routes": [
		{"prefix":"10.10.30.0", "mask":"255.255.255.0", "gw":"192.168.255.1"},
		{"prefix":"10.10.40.0", "mask":"255.255.255.0", "gw":"192.168.255.1"}
		]
	}
	],
)

print(etree.tostring(config, pretty_print=True).decode())
#import c8000v.py
#c8000v.scrapli_configure([config])
```
##### Resulting RESTCONF XML
These produce the same output which can be used directly in a scrapli_netconf call to edit_config the NETCONF message will look like this:

```xml
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
    <ip>
      <route>
        <vrf>
          <name>mgmt</name>
          <ip-route-interface-forwarding-list>
            <prefix>10.10.30.0</prefix>
            <mask>255.255.255.0</mask>
            <gw>192.168.255.1</gw>
          </ip-route-interface-forwarding-list>
          <ip-route-interface-forwarding-list>
            <prefix>10.10.40.0</prefix>
            <mask>255.255.255.0</mask>
            <gw>192.168.255.1</gw>
          </ip-route-interface-forwarding-list>
        </vrf>
        <ip-route-interface-forwarding-list>
          <prefix>10.10.10.0</prefix>
          <mask>255.255.255.0</mask>
          <gw>192.168.255.1</gw>
        </ip-route-interface-forwarding-list>
        <ip-route-interface-forwarding-list>
          <prefix>10.10.20.0</prefix>
          <mask>255.255.255.0</mask>
          <gw>192.168.255.1</gw>
        </ip-route-interface-forwarding-list>
      </route>
    </ip>
  </native>
</config>
```


##### Delete a route  (in VRF)
```xml
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
    <ip>
      <route>
        <vrf>
          <name>mgmt</name>
          <ip-route-interface-forwarding-list operation="remove">
            <prefix>10.10.30.0</prefix>
            <mask>255.255.255.0</mask>
            <gw>192.168.255.1</gw>
          </ip-route-interface-forwarding-list>
        </vrf>
      </route>
    </ip>
  </native>
</config>
```

##### Delete a route  (from default table)
```xml
<config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
    <ip>
      <route>
        <ip-route-interface-forwarding-list operation="remove">
          <prefix>10.10.10.0</prefix>
          <mask>255.255.255.0</mask>
          <gw>192.168.255.1</gw>
        </ip-route-interface-forwarding-list>
      </route>
    </ip>
  </native>
</config>


