from jinja2 import Environment, FileSystemLoader

environment = Environment(loader=FileSystemLoader("templates/"))
template = environment.get_template("ios-xe-native-ntp.xml.j2")

config = template.render(
	servers=["162.159.200.1", "185.181.223.169"]
)
print(config)
#import c8000v
#c8000v.ncclient_configure([config])
