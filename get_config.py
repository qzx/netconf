from scrapli_netconf import NetconfDriver
import argparse
import sys

c8000v = {
    "host": "8000v",
    "auth_username": "cisco",
    "auth_password": "cisco",
    "auth_strict_key": False,
    "port": 830
}

conn = NetconfDriver(**c8000v)

def getconfig(xpath):
    conn.open()
    #print(conn.get_config(source="running").result)
    print(conn.get_config(filter_=xpath, filter_type="xpath").result)
    conn.close()

def main():
    """Main method to configure a subinterface."""
    parser = argparse.ArgumentParser()
    parser.add_argument('filter',
	    help="""XPath filter to get IOS XE Native config
Note: The path is already prefixed with /native/
Examples:
	python get_config.py vrf/definition[name=\"mgmt\"]
	python get_config.py ntp
	python get_config.py router/bgp
	""",
	    type=str
	)
    args = parser.parse_args()

    # check for valid VLAN ID
    if len(args.filter) < 1:
        parser.print_usage()
        print("""Invalid filter: {filter}
        
	Note: The filter path is already prepended with /native/
	This means the input path does not start with a /
	so in order to get ip route info the filter is:
		ip/route
	likewise, in order to get a specific interface
		interface/GigabitEthernet[name=1]
        
        """.format(filter=args.filter))
        sys.exit()
        
    getconfig('{filter}'.format(filter=args.filter))

if __name__ == '__main__':
    sys.exit(main())
