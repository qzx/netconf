from jinja2 import Environment, FileSystemLoader

environment = Environment(loader=FileSystemLoader("templates/"))
template = environment.get_template("ios-xe-acl-extended.xml.j2")

config = template.render(
	name="baboo",
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
#import c8000v
#c8000v.ncclient_configure([config])
