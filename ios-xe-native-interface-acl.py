from jinja2 import Environment, FileSystemLoader

environment = Environment(loader=FileSystemLoader("templates/"))
template = environment.get_template("ios-xe-native-interface-acl.xml.j2")

config = template.render(
	intf_type="GigabitEthernet", 
	name="4",
	acl_name="foo"
)

print(config)
#import c8000v.py
#c8000v.scrapli_configure([config])
