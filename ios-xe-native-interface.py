from jinja2 import Environment, FileSystemLoader

environment = Environment(loader=FileSystemLoader("templates/"))
template = environment.get_template("ios-xe-native-interface.xml.j2")

config = template.render(
	intf_type="GigabitEthernet", 
	name="4",
	addr="10.10.10.1",
	mask="255.255.255.0",
	desc="Yanging around",
	shutdown=False
)
print(config)
#import c8000v.py
#c8000v.scrapli_configure([config])
