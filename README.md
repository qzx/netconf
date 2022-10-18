# Getting started with NETCONF
----

So, we've decided to use NETCONF to configure our devices. In this repository we'll explore the YANG messages we need to communicate with our device, perform RAW NETCONF operations on a Cisco 8000v router and establish a workflow.

Then we'll explore the two clients that are available and options for structuring code to utilize NETCONF.

## SEE ALSO:
[IOS XE Interfaces](https://github.com/qzx/netconf/blob/main/interfaces.md)  
[IOS XE Static Routes](https://github.com/qzx/netconf/blob/main/static-routes.md)  
[IOS XE Access Lists](https://github.com/qzx/netconf/blob/main/access-lists.md)  
[Snippets and blocks](https://github.com/qzx/netconf/blob/main/snippets.md)

## Configuration
----
```c
# First we need to configure our cisco router with an IP address
# username, login local and netconf-yang
conf t
hostname c8000v
!
aaa new-model
aaa session-id common
!
aaa authentication login default local
aaa authorization exec default local
!
username cisco privilege 15 secret 0 cisco
!
netconf-yang
netconf-yang feature candidate-datastore
!
interface GigabitEthernet1
 ip address 192.168.255.72 255.255.255.0
 no shutdown
 exit
!
line vty 0 4
 transport input ssh
 end
wr
```

Now we can connect to our router with SSH
```shell
$ ssh cisco@8000v
Password: 

8000v#
```
Likewise we can connect to the netconf subsystem with ssh
```shell
$ ssh cisco@8000v -p 830 -s netconf
cisco@8000v's password: 
<?xml version="1.0" encoding="UTF-8"?>
<hello xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
<capabilities>
<capability>urn:ietf:params:netconf:base:1.0</capability>
<capability>urn:ietf:params:netconf:base:1.1</capability>
<capability>urn:ietf:params:netconf:capability:writable-running:1.0</capability>
<capability>urn:ietf:params:netconf:capability:rollback-on-error:1.0</capability>
<capability>urn:ietf:params:netconf:capability:validate:1.0</capability>
<capability>urn:ietf:params:netconf:capability:validate:1.1</capability>
<capability>urn:ietf:params:netconf:capability:xpath:1.0</capability>
<capability>urn:ietf:params:netconf:capability:notification:1.0</capability>
<capability>urn:ietf:params:netconf:capability:interleave:1.0</capability>
<capability>urn:ietf:params:netconf:capability:with-defaults:1.0?basic-mode=explicit&amp;also-supported=report-all-tagged,report-all</capability>
<capability>urn:ietf:params:netconf:capability:yang-library:1.0?revision=2016-06-21&amp;module-set-id=62fce412ef7ae70741dbc9b96d64dda6</capability>
.
.
.
<capability>
        urn:ietf:params:netconf:capability:notification:1.1
      </capability>
</capabilities>
<session-id>26</session-id></hello>]]>]]>
```
NOTE: The end of the hello message ']]>]]>' this character sequence comes at the end of each message to indicate the message is over.

### RESTCONF RPC communication
----
Now we're ready to interact with our device with NETCONF. The connection needs to start with a hello message (just like the one we received from the device) where we indicate our capabilities.
##### Hello messages
```xml
<?xml version="1.0" encoding="utf-8"?>
    <hello xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
        <capabilities>
            <capability>urn:ietf:params:netconf:base:1.0</capability>
        </capabilities>
</hello>]]>]]>

<!-- This message indicates netconf 1.1 capabilities-->
<?xml version="1.0" encoding="utf-8"?>
    <hello xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
        <capabilities>
            <capability>urn:ietf:params:netconf:base:1.1</capability>
        </capabilities>
</hello>]]>]]> 
```
Once we've been polite and said hello, we can start asking the device to do things for us. Each message we send needs to have a message ID which increments sequencially and wrapped in a RPC message:
##### Pure RPC | Message ID must be present, and in sequence
```xml
<rpc xmlns='urn:ietf:params:xml:ns:netconf:base:1.0' message-id='{message_id}'></rpc>
```
We'll use this to wrap our get config request
##### Get-Config | source is candidate or running
```xml
<get-config><source><{source}/></source></get-config>
```
Our request to get the running config will therefor look like this:
```xml
<rpc xmlns='urn:ietf:params:xml:ns:netconf:base:1.0' message-id='102'>
  <get-config>
    <source>
      <running/>
    </source>
  </get-config>
</rpc>
```

##### Getting config from router with SSH NETCONF CLI
```shell
$ ssh cisco@8000v -p 830 -s netconf
cisco@8000v's password:
```
**ROUTER SENDS:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<hello xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <capabilities>
  ...
  </capabilities>
</hello>]]>]]>
```
**WE SEND:**
```xml
<?xml version="1.0" encoding="utf-8"?>
    <hello xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
        <capabilities>
            <capability>urn:ietf:params:netconf:base:1.0</capability>
        </capabilities>
</hello>]]>]]>
<rpc xmlns='urn:ietf:params:xml:ns:netconf:base:1.0' message-id='102'>
  <get-config>
    <source>
      <running/>
    </source>
  </get-config>
</rpc>]]>]]>
```
**ROUTER SENDS:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="102">
  <data>
    <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
    ... Router configuration comes here
	</native>
  </data>
</rpc-reply>]]>]]>
```

#### Adding filters to our requests
----
Ok well, that was neat... but that's a lot of configuration. Can we filter it somehow? Sure can! We even have to types of filters we can use:

##### Filter (subtree) | filter type
```xml
<filter type='subtree'></filter>
```
##### Filter (XPath) | xpath is the XPath filter to use
```xml
<filter type='xpath' select='{xpath}'></filter>
```
Let's start by getting something simple like the software version. This is located right at the top of the native configuration. That makes for the following request. We can send the hello and our first message in one go:
**WE SEND:**
```xml
<?xml version="1.0" encoding="utf-8"?>
    <hello xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
        <capabilities>
            <capability>urn:ietf:params:netconf:base:1.0</capability>
        </capabilities>
</hello>]]>]]>
<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="101">
  <get-config>
   <filter type="xpath" select="/native/version"></filter>
    <source>
      <running/>
    </source>
  </get-config>
</rpc>]]>]]>
```
**DEVICE SENDS:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="101">
  <data>
    <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
      <version>17.5</version>
    </native>
  </data>
</rpc-reply>]]>]]>
```
**WE SEND:**
```xml
<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="102">
  <get-config>
   <filter type="xpath" select="/native/ip"></filter>
    <source>
      <running/>
    </source>
  </get-config>
</rpc>]]>]]>
```
**DEVICE SENDS:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="104">
  <data>
    <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
      <ip>
        <forward-protocol>
          <protocol>nd</protocol>
        </forward-protocol>
        <ftp><passive/></ftp>
        <multicast>
          <route-limit xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-multicast">2147483647</route-limit>
        </multicast>
        <http xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-http">
          <server>false</server>
          <secure-server>true</secure-server>
        </http>
        <nbar xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-nbar">
          <classification>
            <dns>
              <classify-by-domain/>
            </dns>
          </classification>
        </nbar>
      </ip>
    </native>
  </data>
</rpc-reply>]]>]]>
```

OK Great! We can communicate with our device over NETCONF and retreive the configuration blocks we want. Now we're ready to configure our router. 

### Configuring device with NETCONF
----
We're now going modify our device, lets start by changing the hostname, then we'll try something a bit more involved. First we'll have to look at the capabilities the router has, as enabling candidate datastore will remove writable-running. Looking at the initial response from our router:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<hello xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
<capabilities>
<capability>urn:ietf:params:netconf:base:1.0</capability>
<capability>urn:ietf:params:netconf:base:1.1</capability>
<capability>urn:ietf:params:netconf:capability:writable-running:1.0</capability>
```
We can see writable-running:1.0 there in the list, this means we can target the running config directly over NETCONF. This line goes away once we enable *netconf-yang feature candidadate-datastore* and instead we get this:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<hello xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
<capabilities>
<capability>urn:ietf:params:netconf:base:1.0</capability>
<capability>urn:ietf:params:netconf:base:1.1</capability>
<capability>urn:ietf:params:netconf:capability:confirmed-commit:1.1</capability>
<capability>urn:ietf:params:netconf:capability:confirmed-commit:1.0</capability>
<capability>urn:ietf:params:netconf:capability:candidate:1.0</capability>
```
This means we have to hit the candidate datastore and commit our changes if we want to configure our device. We can handle for both options in our python code later on. For now lets start by changing our running configuration directly.


#### Change hostname in running config with RAW NETCONF
----
Let's start by writing down all the messages we're going to be sending. Our target is the 'running' configuration. Each RFC message after the hello needs to be wrapped and sequenced
##### Say hello
```xml
<?xml version="1.0" encoding="utf-8"?>
    <hello xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
        <capabilities>
            <capability>urn:ietf:params:netconf:base:1.0</capability>
        </capabilities>
</hello>]]>]]>
```
##### Lock the configuration
```xml
<rpc xmlns='urn:ietf:params:xml:ns:netconf:base:1.0' message-id='101'>
  <lock>
    <target>
      <running/>
    </target>
  </lock>
</rpc>]]>]]>
```
##### Send the proposed configuration block
```xml
<rpc xmlns='urn:ietf:params:xml:ns:netconf:base:1.0' message-id='102'>
  <edit-config>
    <target>
      <running/>
    </target>
      <config xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
	    <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
          <hostname>router</hostname>
        </native>
      </config>
  </edit-config>
</rpc>]]>]]>
```
##### Unlock the configuration
```xml
<rpc xmlns='urn:ietf:params:xml:ns:netconf:base:1.0' message-id='103'>
  <unlock>
    <target>
      <running/>
    </target>
  </unlock>
</rpc>]]>]]>
```
##### Get configuration to confirm
```xml
<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="104">
  <get-config>
   <filter type="xpath" select="/native/hostname"></filter>
    <source>
      <running/>
    </source>
  </get-config>
</rpc>]]>]]>
```

Whoah.. neat! We just changed our running config. Each time we send a message we should get the following reply if things are going well:
```xml
<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="104">
  <ok/>
</rpc-reply>]]>]]>
```

And for our final message we should get our new config data back:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<rpc-reply xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="104">
  <data>
    <native xmlns="http://cisco.com/ns/yang/Cisco-IOS-XE-native">
      <hostname>router</hostname>
    </native>
  </data>
</rpc-reply>]]>]]>
```

Let's finish up by validating the configuration:
##### Validate configuration
```xml
<rpc xmlns="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="106">
  <validate>
    <source>
      <running/>
    </source>
  </validate>
</rpc>]]>]]>
```



