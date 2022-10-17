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
