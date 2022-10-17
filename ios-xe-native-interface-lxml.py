from lxml import etree
def iosXEInterface(intf_type, name, desc, addr, mask, shutdown=False):
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
#import c8000v.py
#c8000v.scrapli_configure([config])
