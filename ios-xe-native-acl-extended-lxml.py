from lxml import etree
def iosXEExtendedAcl(name, entries=[]):
	config = etree.Element("config",
		nsmap = {None: 'urn:ietf:params:xml:ns:netconf:base:1.0'}
	)
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
#c8000v.ncclient_configure([config])
