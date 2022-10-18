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

#print(etree.tostring(config, pretty_print=True).decode())
import c8000v
c8000v.ncclient_configure([config])
