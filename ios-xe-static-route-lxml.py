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
