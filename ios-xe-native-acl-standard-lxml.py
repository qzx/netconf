from lxml import etree
import c8000v

def iosXEStandardAcl(name, entries=[]):
	config = etree.Element("config",
		nsmap = {None: 'urn:ietf:params:xml:ns:netconf:base:1.0'}
	)
	# <native><interfaces><GigabitEthernet>
	native = etree.SubElement(config, "native",
		nsmap = {None: 'http://cisco.com/ns/yang/Cisco-IOS-XE-native'}
	)
	ip = etree.SubElement(native, "ip")
	acl = etree.SubElement(ip, "access-list")
	
	if len(entries) > 0:
		standard_acl = etree.SubElement(acl, "standard",
			nsmap = {None: 'http://cisco.com/ns/yang/Cisco-IOS-XE-acl'}
		)
		# Configure name and description
		etree.SubElement(standard_acl, "name").text = name
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
	else:
		standard_acl = etree.SubElement(acl, "standard",
			nsmap = {None: 'http://cisco.com/ns/yang/Cisco-IOS-XE-acl'},
			operation="remove"
		)
		
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
#import c8000v
#c8000v.ncclient_configure([config])
