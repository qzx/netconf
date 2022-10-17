from scrapli_netconf import NetconfDriver
from ncclient import manager
from lxml import etree

# We're also going to import logging for the ncclient cause it's terrible
#import logging
#logger = logging.getLogger('ncclient')
#logger.setLevel(logging.DEBUG)
#ch = logging.StreamHandler()
#ch.setLevel(logging.DEBUG)
#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#ch.setFormatter(formatter)
#logger.addHandler(ch)


# ncclient and scrapli_netconf use slightly different config blocks
c8000v_scrapli = {
    "host": "8000v",
    "auth_username": "cisco",
    "auth_password": "cisco",
    "auth_strict_key": False,
    "port": 830
}

c8000v_ncclient = {
    "host": "8000v",
    "username": "cisco",
    "password": "cisco",
    "hostkey_verify": False,
    "port": 830,
    "timeout": 30,
    "device_params": {"name": "iosxe"}
}

scrapli_conn = NetconfDriver(**c8000v_scrapli)

def scrapli_configure(cfgs):
	scrapli_conn.open()
	print(scrapli_conn.lock(target="candidate").result)
	for cfg in cfgs:
		config = stringconfig(cfg)
		print('sending config: {config}'.format(config=config))
		print(scrapli_conn.edit_config(config=config, target="candidate").result)
	print(scrapli_conn.commit().result)
	print(scrapli_conn.unlock(target="candidate").result)
	scrapli_conn.close()

def ncclient_configure(cfgs):
	with manager.connect(**c8000v_ncclient) as m:
		assert(":candidate" in m.server_capabilities)
		with m.locked(target="candidate"):
			m.discard_changes()
			for cfg in cfgs:
				config = stringconfig(cfg)
				edit = m.edit_config(target="candidate", config=config)
				if "<ok />" not in edit.xml:
					print(edit.xml)
				else:
					print("<ok />")
			m.commit()


# stringconf is here to check if we're sending config directly from a 
# rendered template (so string on return from the function) or a etree
# function, which returns xml.etree elements, but we don't want to 
# unpack them before the function returns, so we can pretty print
# the contents if we desire in our client code
def stringconfig(cfg):
	if type(cfg) == str:
		return cfg
	else:
		return etree.tostring(cfg).decode()
