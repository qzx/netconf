from scrapli_netconf import NetconfDriver
from ncclient import manager, xml_
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


# Set up couple of constants we might want to use
CANDIDATE = "urn:ietf:params:netconf:capability:candidate:1.0"
RUNNING = "urn:ietf:params:netconf:capability:writable-running:1.0"

# neither client implements cisco's save-config RPC
# We'll need to send the following string as a raw RPC call
save_rpc = '<save-config xmlns="http://cisco.com/yang/cisco-ia"/>'
def scrapli_save():
	scrapli_conn.open()
	print(scrapli_conn.rpc(filter_=save_rpc).result)
	scrapli_conn.close()

def ncc_save():
	with manager.connect(**c8000v_ncclient) as m:
		m.dispatch(xml_.to_ele(save_rpc))

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
	if CANDIDATE in scrapli_conn.server_capabilities:
		print(scrapli_conn.lock(target="candidate").result)
		for cfg in cfgs:
			config = stringconfig(cfg)
			print('sending config: {config}'.format(config=config))
			print(scrapli_conn.edit_config(
				config=config,
				target="candidate").result)
				
		print(scrapli_conn.commit().result)
		print(scrapli_conn.unlock(target="candidate").result)
		
	elif RUNNING in scrapli_conn.server_capabilities:
		print(scrapli_conn.lock(target="running").result)
		for cfg in cfgs:
			config = stringconfig(cfg)
			print('sending config: {config}'.format(config=config))
			print(scrapli_conn.edit_config(
				config=config,
				target="running").result)
		print(scrapli_conn.unlock(target="running").result)
	scrapli_conn.close()

def ncclient_configure(cfgs):
	with manager.connect(**c8000v_ncclient) as m:
		if ":candidate" in m.server_capabilities:
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
				
		elif ":writable-running" in m.server_capabilities:
			with m.locked(target="running"):
				for cfg in cfgs:
					config = stringconfig(cfg)
					edit = m.edit_config(target="running", config=config)
					if "<ok />" not in edit.xml:
						print(edit.xml)
					else:
						print("<ok />")


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
