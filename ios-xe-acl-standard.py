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
#import c8000v
#c8000v.ncclient_configure([config])
