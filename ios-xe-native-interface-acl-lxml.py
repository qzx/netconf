from lxml import etree
def iosXEInterface(intf_type, name, acl_name=None, out=False, ins=False):
	config = etree.Element("config",
		nsmap = {None: 'urn:ietf:params:xml:ns:netconf:base:1.0'}
	)
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
	
config = iosXEInterface(
	intf_type = "GigabitEthernet",
	name = "4",
	acl_name = "foo",
	ins=True
)

print(etree.tostring(config, pretty_print=True).decode())
#import c8000v.py
#c8000v.scrapli_configure([config])
