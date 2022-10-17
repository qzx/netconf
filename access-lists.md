# IOS XE access-lists
----
##### Jinja template
```shell
# We can create a template for standard ACL creation
# This is in Jinja2 syntax to render XML
vim templates/ios-xe-acl-standard.xml.j2
```
```jinja2
<config>
  <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
    <ip>
  	  <access-list>
	    <standard xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-acl">
		  <name>{{ name }}</name>
		  {%- for entry in entries %}
		  <access-list-seq-rule>
		    <sequence>{{ loop.index*10 }}</sequence>
		    <{{ entry.action }}>
			  <std-ace>
			    {%- if entry.addr == "any" %}
				  <any/>
			    {%- else %}
			    <ipv4-address-prefix>{{ entry.addr }}</ipv4-address-prefix>
			    <ipv4-prefix>{{ entry.addr }}</ipv4-prefix>
			    {%- if entry.mask %}
			    <mask>{{ entry.mask }}</mask>
			    {%- endif %}
			    {%- endif %}
			  </std-ace>
		    </{{ entry.action }}>
		  </access-list-seq-rule>
		  {%- endfor %}
	    </standard>
	  </access-list>
    </ip>
  </native>
</config>
```
```shell
# We can create a template for extended ACL creation
# This is in Jinja2 syntax to render XML
vim templates/ios-xe-acl-extended.xml.j2
```
```jinja2
<config>
  <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
    <ip>
	  <access-list>
	    <extended xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-acl">
		  <name>{{ name }}</name>
		  {%- for entry in entries %}
		  <access-list-seq-rule>
		    <sequence>{{ loop.index*10 }}</sequence>
		    <ace-rule>
			  <action>{{ entry.action }}</action>
			  <protocol>{{ entry.proto }}</protocol>
			  {%- if entry.src_addr == "any" %}
			    <any/>
			  {%- else %}
			    <ipv4-address>{{ entry.src_addr }}</ipv4-address>
			    <mask>{{ entry.src_mask }}</mask>
			  {%- endif %}
			  {%- if entry.dst_addr == "any" %}
			    <dst-any/>
			  {%- else %}
			    <dest-ipv4-address>{{ entry.dst_addr }}</dest-ipv4-address>
			    <dest-mask>{{ entry.dst_mask }}</dest-mask>
			  {%- endif %}
			  {%- if entry.port %}
			    <dst-eq>{{ entry.port }}</dst-eq>
			  {%- endif %}
			  {%- if entry.range %}
			  <dst-range1>{{ entry.range[0] }}</dst-range1>
	          <dst-range2>{{ entry.range[1] }}</dst-range2>
			  {%- endif %}
		    </ace-rule>
		  </access-list-seq-rule>
		  {%- endfor %}
	    </extended>
	  </access-list>
    </native>
  </ip>
</config>
```
##### Python scripts
```shell
# Create a script to render the standard ACL
vim ios-xe-acl-standard.py
```
```python
from jinja2 import Environment, FileSystemLoader

environment = Environment(loader=FileSystemLoader("templates/"))
template = environment.get_template("ios-xe-acl-standard.xml.j2")

config = template.render(
	name="10",
	entries=[
		{
			"action": "permit",
			"addr": "10.10.10.0",
			"mask": "0.0.0.255",
		},
		{
			"action": "deny",
			"addr": "10.10.20.0",
			"mask": "0.0.0.255",
		}
	]
)
print(config)
```
```shell
# Create a script to render the extended ACL
vim ios-xe-acl-extended.py
```
```python
from jinja2 import Environment, FileSystemLoader

environment = Environment(loader=FileSystemLoader("templates/"))
template = environment.get_template("ios-xe-acl-extended.xml.j2")

config = template.render(
	name="foo",
	entries=[
		{
			"action": "permit",
			"proto": "tcp",
			"src_addr": "10.10.10.0",
			"src_mask": "0.0.0.255",
			"dst_addr": "10.10.20.0",
			"dst_mask": "0.0.0.255",
			"port": "22"
		},
		{
			"action": "permit",
			"proto": "ip",
			"src_addr": "10.10.30.0",
			"src_mask": "0.0.0.255",
			"dst_addr": "10.10.40.0",
			"dst_mask": "0.0.0.255",
		},
		{
			"action": "permit",
			"proto": "ip",
			"src_addr": "10.10.50.0",
			"src_mask": "0.0.0.255",
			"dst_addr": "any",
		},
		{
			"action": "permit",
			"proto": "tcp",
			"src_addr": "any",
			"dst_addr": "10.10.60.0",
			"dst_mask": "0.0.0.255",
			"port": "22"
		}
	]
)
print(config)
```
##### lxml etree to build config
```shell
# The above template and render is equivalent to the following python script
vim ios-xe-native-acl-standard-lxml.py
```
```python
from lxml import etree
def iosXEStandardAcl(name, entries=[]):
	config = etree.Element("config")
	# <native><interfaces><GigabitEthernet>
	native = etree.SubElement(config, "native",
		nsmap = {None: 'http://cisco.com/ns/yang/Cisco-IOS-XE-native'}
	)
	ip = etree.SubElement(native, "ip")
	acl = etree.SubElement(ip, "access-list")
	standard_acl = etree.SubElement(acl, "standard",
		nsmap = {None: 'http://cisco.com/ns/yang/Cisco-IOS-XE-acl'}
	)
	# Configure name and description
	etree.SubElement(standard_acl, "name").text = name
	if len(entries) > 0:
		for entry in entries:
			acl_seq = "{seq}".format(seq=10*entries.index(entry)+10)
			rule = etree.SubElement(standard_acl, "access-list-seq-rule")
			etree.SubElement(rule, "sequence").text = acl_seq
			action = etree.SubElement(rule, entry['action'])
			line = etree.SubElement(action, "std-ace")
			if entry['addr'] == 'any':
				etree.SubElement(line, "any")
			else:
				etree.SubElement(
					line,
					"ipv4-address-prefix").text = entry['addr']
				etree.SubElement(line, "ipv4-prefix").text = entry['addr']
				if 'mask' in entry:
					etree.SubElement(line, "mask").text = entry['mask']
			
	return config
	
config = iosXEStandardAcl(
	name = "10",
	entries=[
		{
			"action": "permit",
			"addr": "10.10.10.0",
			"mask": "0.0.0.255",
		},
		{
			"action": "permit",
			"addr": "10.10.20.5",
		},
		{
			"action": "deny",
			"addr": "any",
		},
	]
)

print(etree.tostring(config, pretty_print=True).decode())
```
```shell
# The above template and render is equivalent to the following python script
vim ios-xe-native-acl-extended-lxml.py
```
```python
from lxml import etree
def iosXEExtendedAcl(name, entries=[]):
	config = etree.Element("config")
	# <native><interfaces><GigabitEthernet>
	native = etree.SubElement(config, "native",
		nsmap = {None: 'http://cisco.com/ns/yang/Cisco-IOS-XE-native'}
	)
	ip = etree.SubElement(native, "ip")
	acl = etree.SubElement(ip, "access-list")
	extended_acl = etree.SubElement(acl, "extended",
		nsmap = {None: 'http://cisco.com/ns/yang/Cisco-IOS-XE-acl'}
	)
	# Configure name and description
	etree.SubElement(extended_acl, "name").text = name
	if len(entries) > 0:
		for entry in entries:
			acl_seq = "{seq}".format(seq=10*entries.index(entry)+10)
			rule = etree.SubElement(extended_acl, "access-list-seq-rule")
			etree.SubElement(rule, "sequence").text = acl_seq
			line = etree.SubElement(rule, "ace-rule")
			etree.SubElement(line, "action").text = entry['action']
			etree.SubElement(line, "protocol").text = entry['proto']
			if entry['src_addr'] == 'any':
				etree.SubElement(line, "any")
			else:
				etree.SubElement(line, "ipv4-address").text = entry['src_addr']
				if 'src_mask' in entry:
					etree.SubElement(line, "mask").text = entry['src_mask']
			if entry['dst_addr'] == 'any':
				etree.SubElement(line, "dst-any")
			else:
				etree.SubElement(line, "dest-ipv4-address").text = entry['dst_addr']
				if 'dst_mask' in entry:
					etree.SubElement(line, "dest-mask").text = entry['dst_mask']
			if 'port' in entry:
				etree.SubElement(line, "dst-eq").text = entry['port']
	return config
	
config = iosXEExtendedAcl(
	name = "foo",
	entries=[
		{
			"action": "permit",
			"proto": "tcp",
			"src_addr": "10.10.10.0",
			"src_mask": "0.0.0.255",
			"dst_addr": "10.10.20.0",
			"dst_mask": "0.0.0.255",
			"port": "22"
		},
		{
			"action": "permit",
			"proto": "ip",
			"src_addr": "10.10.30.0",
			"src_mask": "0.0.0.255",
			"dst_addr": "10.10.40.0",
			"dst_mask": "0.0.0.255",
		},
		{
			"action": "permit",
			"proto": "ip",
			"src_addr": "10.10.50.0",
			"src_mask": "0.0.0.255",
			"dst_addr": "any",
		},
		{
			"action": "permit",
			"proto": "tcp",
			"src_addr": "any",
			"dst_addr": "10.10.60.0",
			"dst_mask": "0.0.0.255",
			"port": "22"
		}
	]
)

config_string = etree.tostring(config).decode()
print(etree.tostring(config, pretty_print=True).decode())
#import c8000v
#c8000v.configure(config_string)
```
##### XML Output - Both methods produce the same output
```xml
<config>
  <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
	<access-list>
	  <standard xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-acl">
		<name>10</name>
		<access-list-seq-rule>
		  <sequence>10</sequence>
		  <permit>
			<std-ace>
			  <ipv4-address-prefix>10.10.10.0</ipv4-address-prefix>
			  <ipv4-prefix>10.10.10.0</ipv4-prefix>
			  <mask>0.0.0.255</mask>
			</std-ace>
		  </permit>
		</access-list-seq-rule>
		<access-list-seq-rule>
		  <sequence>20</sequence>
		  <deny>
			<std-ace>
			  <ipv4-address-prefix>10.10.20.0</ipv4-address-prefix>
			  <ipv4-prefix>10.10.20.0</ipv4-prefix>
			  <mask>0.0.0.255</mask>
			</std-ace>
		  </deny>
		</access-list-seq-rule>
	  </standard>
	</access-list>
  </native>
</config>
```
```xml
<config>
  <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
	<access-list>
	  <extended xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-acl">
		<name>foo</name>
		<access-list-seq-rule>
		  <sequence>10</sequence>
		  <ace-rule>
			<action>permit</action>
			<protocol>tcp</protocol>
			  <ipv4-address>10.10.10.0</ipv4-address>
			  <mask>0.0.0.255</mask>
			  <dest-ipv4-address>10.10.20.0</dest-ipv4-address>
			  <dest-mask>0.0.0.255</dest-mask>
			  <dst-eq>22</dst-eq>
		  </ace-rule>
		</access-list-seq-rule>
		<access-list-seq-rule>
		  <sequence>20</sequence>
		  <ace-rule>
			<action>permit</action>
			<protocol>ip</protocol>
			  <ipv4-address>10.10.30.0</ipv4-address>
			  <mask>0.0.0.255</mask>
			  <dest-ipv4-address>10.10.40.0</dest-ipv4-address>
			  <dest-mask>0.0.0.255</dest-mask>
		  </ace-rule>
		</access-list-seq-rule>
		<access-list-seq-rule>
		  <sequence>30</sequence>
		  <ace-rule>
			<action>permit</action>
			<protocol>ip</protocol>
			  <ipv4-address>10.10.50.0</ipv4-address>
			  <mask>0.0.0.255</mask>
			  <dst-any/>
		  </ace-rule>
		</access-list-seq-rule>
		<access-list-seq-rule>
		  <sequence>40</sequence>
		  <ace-rule>
			<action>permit</action>
			<protocol>tcp</protocol>
			  <any/>
			  <dest-ipv4-address>10.10.60.0</dest-ipv4-address>
			  <dest-mask>0.0.0.255</dest-mask>
			  <dst-eq>22</dst-eq>
		  </ace-rule>
		</access-list-seq-rule>
	  </extended>
	</access-list>
  </native>
</config>
```
