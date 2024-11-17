#
# CLI dictionary
# cliDict.py
#
BVLANs = [str(4051), str(4052)]
IstVLANrange = [4050, 4000] # Try for VLAN 4050, and decrement to 4000 if not available
IstMLTrange = [512,500]
VistIPbase = ('192.168.255.0', '255.255.255.252') #/30

# Regexes:
# Port (VOSS):\d+/\d+(?:/\d+)?
# Port (EXOS):\d+(?::\d+)?
# MAC :[\da-f:]+
# IPv4:\d+\.\d+\.\d+\.\d+
CLI_Dict = {
    'FIGW': {
        'check_vm_running'           : 'bool://show version||[\d\.]+$',
        'create_ipsec_respdr_tunnel' : # {0} = Tunnel id, {1} = Tunnel name, {2} = FE Tunnel dest IP, {3} = IPsec auth key
                                       '''
                                       set ipsec {0} tunnel-name {1}
                                       set ipsec {0} responder-only true
                                       set ipsec {0} fe-tunnel-dest-ip {2}
                                       set ipsec {0} auth-key {3}
                                       set ipsec {0} fragment-before-encrypt enable
                                       set ipsec {0} esp aes256gcm16-sha256
                                       set ipsec {0} admin-state enable
                                       ''',
        'create_ipsec_tunnel'        : # {0} = Tunnel id, {1} = Tunnel name, {2} = IPsec Tunnel dest IP, {3} = FE Tunnel dest IP, {4} = IPsec auth key
                                       '''
                                       set ipsec {0} tunnel-name {1}
                                       set ipsec {0} ipsec-dest-ip {2}
                                       set ipsec {0} fe-tunnel-dest-ip {3}
                                       set ipsec {0} auth-key {4}
                                       set ipsec {0} fragment-before-encrypt enable
                                       set ipsec {0} esp aes256gcm16-sha256
                                       set ipsec {0} admin-state enable
                                       ''',
        'disable_fe_tunnel'          : 'delete ipsec {} admin-state enable', # Tunnel id
        'get_figw_config'            : 'str-nwlnjoin://show running-config||^(set.+)$',
        'get_ip_interfaces'          : 'dict://show running-config||set global (lan-intf-ip|ipsec-tunnel-src-ip|fe-tunnel-src-ip) (\d+\.\d+\.\d+\.\d+)',
        'get_version'                : 'str://show version||([\d\.]+)$',
        'global_config'              : # {0} = FIGW internal VLAN, {2} = FIGW Internal IP, {4} = VSP Internal IP, {6} = Internal VLAN Mask
                                       # {1} = FIGW external VLAN, {3} = FIGW External IP, {5} = WAN External IP, {7} = Internal VLAN Mask, {8} = FE Tunnel Src Ip
                                       '''
                                       set global lan-intf-vlan {0}
                                       set global lan-intf-ip {2}/{6}
                                       set global lan-intf-gw-ip {4}
                                       set global ipsec-tunnel-src-vlan {1}
                                       set global ipsec-tunnel-src-ip {3}/{7}
                                       set global wan-intf-gw-ip {5}
                                       set global fe-tunnel-src-ip {8}
                                       set global mtu 1500
                                       ''',
        'list_fe_tunnels'            : 'list://show running-config||set (?:ipsec|logical-intf-tunnel) (\d+) (?:fe-tunnel-dest-ip (\d+\.\d+\.\d+\.\d+)|tunnel-name (\S+))',
        'save_config'                : 'save config -y',
        'show_version'               : 'show version',
        'show_version_bad'           : 'show bersion', # for testing error message detection
    },
    'VSP Series': {
        'disable_more_paging'        : 'terminal more disable',
        'enable_context'             : 'enable',
        'config_context'             : 'config term',
        'vrf_config_context'         : 'router vrf {}', # VRF name
        'port_config_context'        : 'interface gigabitEthernet {}', # Port list
        'mlt_config_context'         : 'interface mlt {}', # MLT id
        'vlan_config_context'        : 'interface vlan {}', # VLAN id
        'isis_config_context'        : 'router isis',
        'exit_config_context'        : 'exit',
        'end_config'                 : 'end',
        'end_save_config'            : 'end; save config',
        'save_config'                : 'save config',
        'software_commit'            : 'software commit',
        'figw_cli'                   : 'virtual-service figw figw-cli "{}"', # FIGW command (requires config context)

        'apply_ipvpn_unicast'        : 'isis apply redistribute direct vrf {}', # VRF name
        'apply_isis_accept'          : 'isis apply accept vrf {}', # VRF name
        'apply_ist_routemap'         : 'isis apply redistribute direct',

        'disable_ftp'                : 'no boot config flags ftpd',
        'enable_ftp'                 : 'boot config flags ftpd',

        'backup_config'              : 'backup configure {}', # Backup tgz archive name

        'change_isis_system_id'      : 'system-id {}', # system-id
        'change_lacp_smlt_mac'       : 'lacp smlt-sys-id {}', # mac
        'change_smlt_virt_peer_id'   : 'spbm 1 smlt-peer-system-id {}; spbm 1 smlt-virtual-bmac {}', # SMLT Peer sys-id, SMLT Virt BMAC
        'change_spbm_nickname'       : 'spbm 1 nick-name {}', # nickname
        'change_sys_name'            : # Sys-name
                                       '''
                                       snmp-server name {0}
                                       router isis
                                          sys-name {0}
                                       exit
                                       ''',

        'check_autosense'            : 'bool://show vlan basic||^4048  onboarding-vlan  private',
        'check_autosense_enabled'    : 'bool://show auto-sense onboarding||^15999999 +4048',
        'check_autosense_nni_up'     : 'bool://show interfaces gigabitEthernet auto-sense||NNI-ISIS-UP',
        'check_cvlan_exists'         : 'bool://show vlan basic {0}||^{0}\s', # VLAN id
        'check_fe_tunnel_exists'     : 'bool://show isis logical-interface|| {} ',
        'check_figw_dir_exists'      : 'bool://ls {}||^Listing Directory', # Path
        'check_ftp_daemon'           : 'bool://show boot config flags||^flags ftpd true',
        'check_iah_insight_port'     : 'bool://show interfaces gigabitEthernet interface {0}||^{0} ', # Insight port
        'check_isis_adjacencies'     : 'bool://show isis adjacencies||^\S+ +1 UP',
        'check_mgmt_clip_exists'     : 'bool://show mgmt interface||^\d +Mgmt-clip +CLIP', # VRF name
        'check_redist_exists'        : 'bool://show ip isis redistribute vrf {}||^LOC',
        'check_software_commit'      : 'bool://show software||Remaining time until software auto-commit',
        'check_ssd_module_present'   : 'bool://show sys-info ssd||Serial Num',
        'check_vrf_exists'           : 'bool://show ip vrf||^{} ', # VRF name
        'check_users_connected'      : 'bool://show users||^(?:Telnet|SSH).+\d *$',

        'clear_autosense_voice'      : 'no auto-sense voice',
        'clear_autosense_data'       : 'no auto-sense data i-sid',
        'clear_autosense_wap'        : 'no auto-sense fa wap-type1 i-sid',
        'clear_cvlan_isid'           : 'no vlan i-sid {}', # VLAN id
        'clear_lacp_smlt_mac'        : 'lacp smlt-sys-id 00:00:00:00:00:00',
        'clear_spbm_bvids'           : 'no spbm 1 b-vid {0}-{1}', # Bvid#1, Bvid#2
        'clear_spbm_smlt_peer'       : 'no spbm 1 smlt-peer-system-id',
        'clear_spbm_smlt_virt_bmac'  : 'no spbm 1 smlt-virtual-bmac',

        'convert_mgmt_isid'          : # I-SID, IP, Mask, Gateway, Rollback secs
                                       '''
                                       mgmt vlan
                                       convert i-sid {} ip {} {} gateway {} rollback {}\ny
                                       ''',
        'convert_mgmt_vlan'          : # VLAN id, IP, Mask, Gateway, Rollback secs
                                       '''
                                       mgmt vlan
                                       convert vlan {} ip {} {} gateway {} rollback {}\ny
                                       ''',
        'convert_mgmt_vlan_isid'     : # VLAN id, I-SID, IP, Mask, Gateway, Rollback secs
                                       '''
                                       mgmt vlan
                                       convert vlan {} i-sid {} ip {} {} gateway {} rollback {}\ny
                                       ''',
        'convert_mgmt_commit'        : 'mgmt convert-commit',

        'copy_file_from_vm'          : 'virtual-service copy-file {0}:{1}/{2} {3}/{2}', # VM name, VM path, Filename, Local path
        'copy_file_to_vm'            : 'virtual-service copy-file {3}/{2} {0}:{1}/{2}', # VM name, VM path, Filename, Local path

        'create_cvlan'               : 'vlan create {} type port-mstprstp 0', # VLAN id
        'create_cvlan_dhcp_server'   : # {0} = DHCP IP
                                       '''
                                       ip dhcp-relay fwd-path {0} mode dhcp
                                       ip dhcp-relay fwd-path {0} enable
                                       ''',
        'create_cvlan_dvr'           : # {0} = DVR-GW IP
                                       '''
                                       dvr gw-ipv4 {0}
                                       dvr enable
                                       ''',
        'create_cvlan_ip'            : 'vrf {0}; ip address {1}/{2}', # {0} = VRF name, {1} = VLAN IP, {2} = IP Mask
        'create_cvlan_isid'          : 'vlan i-sid {0} {1}', # {0} = VLAN id, {1} = L2 I-SID
        'create_cvlan_mlt_uni'       : 'vlan mlt {} {}', # VLAN id, MLT id
        'create_cvlan_uni'           : { # {0} = VLAN id; {1} = port-list
            'tag'                    : 'interface gigabitEthernet {1}; encapsulation dot1q; exit; vlan members add {0} {1}',
            'untag'                  : 'interface gigabitEthernet {1}; no encapsulation dot1q; exit; vlan members add {0} {1}',
                                       },
        'create_cvlan_rsmlt'         : 'ip rsmlt; ip rsmlt holdup-timer 9999',
        'create_cvlan_vrrp'          : # {0} = VRRP VRID, {1} = VRRP IP, {2} = VRRP Priority
                                       '''
                                       ip vrrp version 3
                                       ip vrrp address {0} {1}
                                       ip vrrp {0} priority {2}
                                       ip vrrp {0} backup-master enable
                                       ip vrrp {0} enable
                                       ''',
        'create_directory'           : 'mkdir {}', # Path
        'create_dvr_inband_mgmt'     : 'router isis; inband-mgmt-ip {}; exit', # IP address
        'create_dvr_leaf'            : 'dvr leaf {}', # DVR domain
        'create_dvr_leaf_vist'       : 'dvr leaf virtual-ist {0}/30 peer-ip {1} cluster-id {2}', # {0} = IST IP, {1} = IST Peer IP, {3} = Cluster id
        'create_fe_global_config'    : # {0} = VRF Name, {1} = VRF id, {2} VLAN id, {3} = VLAN Name, {4} = FE Source IP, {5} = FE IP Mask, {6} = Default Gateway
                                       '''
                                       ip vrf {0} vrfid {1}
                                       vlan create {2} name {3} type port-mstprstp 0
                                       interface vlan {2}
                                          vrf {0}
                                          ip address {4}/{5}
                                       exit
                                       router vrf {0}
                                          ip route 0.0.0.0 0.0.0.0 {6} weight 10
                                       exit
                                       router isis
                                          ip-tunnel-source-address {4} vrf {0}
                                       exit
                                       ''',
        'create_fe_isis'             : # Tunnel metric
                                       '''
                                          isis
                                          isis spbm 1
                                          isis spbm 1 l1-metric {}
                                          isis enable
                                       ''',
        'create_fe_isis_remote'      : # Tunnel metric
                                       '''
                                          isis remote
                                          isis remote spbm 1
                                          isis remote spbm 1 l1-metric {}
                                          isis remote enable
                                       ''',
        'create_fe_src_vrf_clip'     : # {0} = VRF name, {1} = VRF id, {2} = Loopback id, {3} = IP address
                                       '''
                                       ip vrf {0} vrfid {1}
                                       interface loopback {2}
                                          ip address {3}/32 vrf {0}
                                       exit
                                       ''',
        'create_fe_tunnel'           : # {0} = FE Tunnel id, {1} = FE Tunnel dest IP, {2} = FE Tunnel name
                                       '''
                                       logical-intf isis {0} dest-ip {1} name {2}
                                          isis
                                          isis spbm 1
                                          isis enable
                                       exit
                                       ''',
        'create_fe_tunnel'           : # {0} = FE Tunnel id, {1} = FE Tunnel dest IP, {2} = FE Tunnel name, {3} = Tunnel metric
                                       '''
                                       logical-intf isis {0} dest-ip {1} name {2}
                                          isis
                                          isis spbm 1
                                          isis spbm 1 l1-metric {3}
                                          isis enable
                                       exit
                                       ''',
        'create_fe_tunnel'           : # {0} = FE Tunnel id, {1} = FE Tunnel dest IP, {2} = FE Tunnel name, {3} = Tunnel metric, {4} = VSP FE VRF, {5} = FIGW Internal IP
                                       '''
                                       logical-intf isis {0} dest-ip {1} name {2}
                                          isis
                                          isis spbm 1
                                          isis spbm 1 l1-metric {3}
                                          isis enable
                                       exit
                                       router vrf {4}
                                          ip route {1} 255.255.255.255 {5} weight 1
                                       exit
                                       ''',
        'create_fe_tunnel'           : # {0} = FE Tunnel id, {1} = FE Tunnel dest IP, {2} = FE Tunnel name
                                       '''
                                       logical-intf isis {0} dest-ip {1} name {2}
                                       ''',
        'create_fe_tunnel_src_vrf'   : # {0} = FE Tunnel id, {1} = FE Tunnel dest IP, {2} = FE Tunnel name, {3} = FE Tunnel src IP, (4) = FE Tunnel src VRF
                                       '''
                                       logical-intf isis {0} dest-ip {1} src-ip {3} vrf {4} name {2}
                                       ''',
        'create_fe_tunnel_src_vrf'   : # {0} = FE Tunnel id, {1} = FE Tunnel dest IP, {2} = FE Tunnel name, {3} = Tunnel metric, {4} = VSP FE VRF, {5} = FIGW Internal IP
                                       # {6} = FE Tunnel src IP, (8) = FE Tunnel src VRF
                                       '''
                                       logical-intf isis {0} dest-ip {1} src-ip {6} vrf {7} name {2}
                                          isis
                                          isis spbm 1
                                          isis spbm 1 l1-metric {3}
                                          isis enable
                                       exit
                                       router vrf {4}
                                          ip route {1} 255.255.255.255 {5} weight 1
                                       exit
                                       ''',
        'create_fe_tunnel_remote'    : # {0} = FE Tunnel id, {1} = FE Tunnel dest IP, {2} = FE Tunnel name, {3} = Tunnel metric
                                       '''
                                       logical-intf isis {0} dest-ip {1} name {2}
                                          isis remote
                                          isis remote spbm 1
                                          isis remote spbm 1 l1-metric {3}
                                          isis remote enable
                                       exit
                                       ''',
        'create_fe_static_route'     : 'ip route {} 255.255.255.255 {} weight 1', # FE Tunnel dest IP, FIGW Internal IP
        'create_fe_tnl_static_route' : 'ip route {} 255.255.255.255 {} weight 1', # FE Tunnel dest IP, FE Tunnel nexthop IP
        'create_figw_vlans'          : # {0} = FIGW internal VLAN, {2} = Insight port,  {4} = VSP FE VRF,      {6} = Internal VLAN Mask
                                       # {1} = FIGW external VLAN, {3} = Internet port, {5} = VSP Internal IP
                                       '''
                                       vlan create {0} name FIGW-internal type port-mstprstp 0
                                       vlan members {0} {2}
                                       interface vlan {0}
                                          vrf {4}
                                          ip address {5}/{6}
                                       exit
                                       vlan create {1} name FIGW-external type port-mstprstp 0
                                       interface gigabitEthernet {3}
                                          no auto-sense enable
                                       exit
                                       vlan members {1} {2},{3}
                                       interface gigabitEthernet {3}
                                          no encapsulation dot1q
                                          no spanning-tree mstp\ny
                                          no shutdown
                                       exit
                                       ''',
        'create_flex_uni'            : 'vlan members remove 1 {0}; interface gigabitEthernet {0}; flex-uni enable; no shutdown; exit', # Port
        'create_grt_redistribution'  : '''
                                       router isis
                                          redistribute direct
                                       exit
                                       ''',
        'create_ip_loopback'         : 'interface loopback {0}; ip address {1}/32; exit', # Loopback id, IP address
        'create_ipvpn'               : # {0} = L3 I-SID
                                       '''
                                       ipvpn
                                       i-sid {0}
                                       ipvpn enable
                                       ''',
        'create_isis_accept'         : 'isis accept i-sid {} enable', # shared I-SID
        'create_isis_area'           : 'manual-area {}', # Area
        'create_isis_interface'      : 'isis; isis spbm 1; isis enable',
        'create_isis_manual_area'    : # Area
                                       '''
                                       router isis
                                          manual-area {}
                                       exit
                                       ''',
        'create_ist_routemap'        : # {0} = IST subnet
                                       '''
                                       ip prefix-list "IST" {0}/30
                                       route-map "Suppress-IST" 1
                                          no permit
                                          enable
                                          match network "IST"
                                       exit
                                       route-map "Suppress-IST" 2
                                          permit
                                          enable
                                       exit
                                       router isis
                                          redistribute direct route-map "Suppress-IST"
                                       exit
                                       ''',
        'create_mgmt_clip'           : # VRF name, IP address
                                       '''
                                       mgmt clip vrf {0}
                                          ip address {1}/32
                                          enable
                                       exit
                                       ''',
        'create_mlt'                 : 'mlt {0}; mlt {0} member {1}', # MLT id, Port list
        'create_mlt'                 : 'mlt {} enable {}', # MLT id, 'name "name"'
        'create_mlt_flex_uni'        : 'interface mlt {0}; flex-uni enable; exit', # MLT id
        'create_mlt_switched_uni'    : { # {0} = i-sid; {1} = VLAN id; {2} = MLT-id
            'tag'                    : 'i-sid {0}; c-vid {1} mlt {2}; exit',
            'untag'                  : 'i-sid {0}; untagged-traffic mlt {2}; exit',
                                       },
        'create_ntp_server'          : 'ntp server {} enable', # IP
        'create_radius_server'       : # {0} = Radius Server IP, {1} = Radius secret, {2} = Source IP
                                       '''
                                       radius server host {0} key "{1}" used-by endpoint-tracking source-ip {2}
                                       radius sourceip-flag
                                       radius dynamic-server client {0} secret {1} enable
                                       ''',
        'create_radius_server_lns'   : # {0} = Radius Server IP, {1} = Radius secret
                                       '''
                                       radius server host {0} key {1} used-by endpoint-tracking
                                       radius dynamic-server client {0} secret {1} enable
                                       ''',
        'create_radius_server'       : 'radius server host {} key "{}" used-by {} priority {} acct-enable', # Radius Server IP, Radius secret, Use, Priority
        'create_dyn_radius_server'   : 'radius dynamic-server client {} secret "{}" enable', # Radius Server IP, Radius secret
        'create_spbm'                : 'spbm 1',
        'create_spbm_platform_bvlans': 'vlan create {0} name "Primary-BVLAN" type spbm-bvlan; vlan create {1} name "Secondary-BVLAN" type spbm-bvlan', # Bvid#1, Bvid#2
        'create_switched_uni'        : { # {0} = i-sid; {1} = VLAN id; {2} = port-list
            'tag'                    : 'i-sid {0}; c-vid {1} port {2}; exit',
            'untag'                  : 'i-sid {0}; untagged-traffic port {2}; exit',
                                       },
        'create_switched_isid'       : 'i-sid {0}; exit', # {0} = i-sid
        'create_vist'                : # {0} = IST VLAN, {1} = IST ISID, {2} = IST IP, {3} = IST Peer IP
                                       '''
                                       vlan create {0} name "IST-VLAN" type port-mstprstp 0
                                       vlan i-sid {0} {1}
                                       interface Vlan {0}
                                          ip address {2}/30
                                       exit
                                       virtual-ist peer-ip {3} vlan {0}
                                       ''',
        'create_vlan'                : 'vlan create {} type port-mstprstp 0', # VLAN id
        'create_vlan_ip'             : # {0} = VLAN id, {1} = VRF Name, {2} = IP addr, {3} = Mask
                                       '''
                                       interface vlan {0}
                                          vrf {1}
                                          ip address {2}/{3}
                                          ip rsmlt
                                          ip rsmlt holdup-timer 9999 
                                       exit
                                       ''',
        'create_vlan_isid'           : 'vlan i-sid {0} {1}', # {0} = VLAN id; {1} = i-sid '
        'create_vrf'                 : 'ip vrf {}', # VRF name
        'create_vrf_with_id'         : 'ip vrf {0} vrfid {1}', # VRF name, VRF id

        'default_vlan_name'          : 'vlan name {0} VLAN-{0}', # VLAN id

        'delete_as_isis_key_file'    : 'delete /intflash/.auto_sense_key.txt -y',
        'delete_cvlan'               : 'vlan delete {}', # VLAN id
        'delete_cvlan_uni'           : 'vlan members remove {0} {1}', # {0} = VLAN id; {1} = port-list
        'delete_dvr_leaf'            : 'no dvr leaf',
        'delete_dvr_leaf_vist'       : 'no dvr leaf virtual-ist',
        'delete_dvr_controller'      : 'no dvr controller',
        'delete_ept'                 : 'no endpoint-tracking',
        'delete_fe_static_route'     : 'no ip route {} 255.255.255.255 {}', # FE Tunnel dest IP, Next hop
        'delete_fe_tunnel'           : 'no logical-intf isis {0}', # FE Tunnel id
        'delete_file'                : 'delete {}/{} -y', # Path, Filename
        'delete_isis_area'           : 'no manual-area {}', # Area
        'delete_isis_source_ip'      : 'router isis; no spbm 1 ip enable; no ip-source-address; exit; interface loopback {}; no ip address {}; exit', # Clip-id, IP address
        'delete_ist_routemap'        : '''
                                       no route-map "Suppress-IST" 1
                                       no route-map "Suppress-IST" 2
                                       no ip prefix-list "IST"
                                       ''',
        'delete_ist_vlan'            : 'vlan delete {0}', # IST VLAN
        'delete_mgmt_clip'           : 'no mgmt clip\ny',
        'delete_mgmt_vlan'           : 'no mgmt vlan\ny',
        'delete_mlt'                 : 'no mlt {}', # MLT id
        'delete_mlt_switched_uni'    : { # {0} = i-sid; {1} = VLAN id; {2} = MLT id
            'tag'                    : 'i-sid {0}; no c-vid {1} mlt {2}; exit',
            'untag'                  : 'i-sid {0}; no untagged-traffic mlt {2}; exit',
            'transparent'            : 'i-sid {0}; no mlt {2}; exit'
                                       },
        'delete_ntp_server'          : 'no ntp server {}', # IP
        'delete_radius_client'       : 'no radius dynamic-server client {}', # IP
        'delete_radius_server'       : 'no radius server host {} used-by endpoint-tracking', # IP
        'delete_spbm_platform_bvlans': 'vlan delete {0}; vlan delete {1}', # Bvid#1, Bvid#2
        'delete_switched_isid'       : 'no i-sid {}', # Isid
        'delete_switched_uni'        : { # {0} = i-sid; {1} = VLAN id; {2} = port-list
            'tag'                    : 'i-sid {0}; no c-vid {1} port {2}; exit',
            'untag'                  : 'i-sid {0}; no untagged-traffic port {2}; exit',
            'transparent'            : 'i-sid {0}; no port {2}; exit'
                                       },
        'delete_vist'                : 'no virtual-ist peer-ip',
        'delete_vlan'                : 'vlan delete {}', # VLAN id
        'delete_vrf'                 : 'no ip vrf {}\ny', # VRF name

        'disable_autosense'          : 'interface gigabitEthernet {0}; no auto-sense enable; exit', # Port
        'disable_autosense_conv2cfg' : 'interface gigabitEthernet {0}; no auto-sense enable convert-to-config; exit', # Port
        'disable_cfm_spbm'           : 'no cfm spbm enable',
        'disable_dvr_leaf_boot_flag' : 'no boot config flags dvr-leaf-mode',
        'disable_ept'                : 'no endpoint-tracking enable',
        'disable_fa_message_auth'    : 'no fa message-authentication',
        'disable_ip_shortcuts'       : 'router isis; no spbm 1 ip enable; exit',
        'disable_ipvpn_multicast'    : 'no mvpn enable',
        'disable_ipvpn_unicast'      : 'no isis redistribute direct',
        'disable_isis'               : 'no router isis enable\ny',
        'disable_isis_hello_padding' : 'router isis; no hello-padding; exit',
        'disable_lacp'               : 'no lacp enable',
        'disable_radius_accounting'  : 'no radius accounting enable',
        'disable_slpp_packet_rx'     : 'no slpp packet-rx; default slpp packet-rx-threshold',
        'disable_vlan_slpp'           : 'no slpp vid {}', # VLAN id

        'empty_directory'            : 'delete {}* -y\ny', # Path

        'enable_cvlan_dhcp_relay'    : 'ip dhcp-relay',
        'enable_cfm_spbm'            : 'cfm spbm enable',
        'enable_dvr_leaf_boot_flag'  : 'boot config flags dvr-leaf-mode\ny',
        'enable_ept'                 : 'endpoint-tracking enable',
        'enable_endpoint_tracking'   : 'endpoint-tracking enable',
        'enable_fabric_attach'       : 'fa; fa enable',
        'enable_ipvpn_multicast'     : 'mvpn enable',
        'enable_ipvpn_unicast'       : '''
                                       isis redistribute direct
                                       isis redistribute direct enable
                                       ''',
        'enable_ip_shortcuts'        : 'router isis; spbm 1 ip enable; exit',
        'enable_isis'                : 'router isis enable',
        'enable_lacp'                : 'lacp enable',
        'enable_mlt_flex_uni'        : 'flex-uni enable',
        'enable_mlt_tagging'         : 'mlt {} encapsulation dot1q', # MLT id
        'enable_ntp'                 : 'ntp',
        'enable_radius'              : 'radius enable',
        'enable_radius_accounting'   : 'radius accounting enable',
        'enable_rsmlt_edge'          : 'ip rsmlt edge-support',
        'enable_slpp_packet_rx'      : 'slpp packet-rx; slpp packet-rx-threshold {}', # SLPP threshold
        'enable_smlt'                : 'smlt',
        'enable_spb_multicast'       : 'ip spb-multicast enable',
        'enable_spbm'                : 'spbm',
        'enable_vlacp'               : 'vlacp enable',
        'enable_vlan_slpp'           : 'slpp vid {}', # VLAN id

        'get_auto_sense_state'       : 'str://show interfaces gigabitEthernet auto-sense {0}||^{0} +\S+ +(\S+)', # Port
        'get_auto_sense_states'      : 'dict://show interfaces gigabitEthernet auto-sense {}||^(\d+/\d+(?:/\d+)?) +\S+ +(\S+)', # Port(s)
        'get_autosense_data_isid'    : 'str://show auto-sense data||^(\d+)',
        'get_autosense_voice_isid'   : 'str://show auto-sense voice||(?:^|E +)(\d+) +[\du]',
        'get_autosense_sdwan_vrf'   : 'bool://show auto-sense sd-wan||globalrouter',
        'get_autosense_wap_isid'     : 'str://show auto-sense fa||^wap-type1 +\S+ +(\d+)',
        'get_cfm_settings'           : 'tuple://show cfm spbm||^\d +(enable|disable) +(\d+)',
        'get_chassis_mac'            : 'str://show sys-info||BaseMacAddr +: +(\S+)',
        'get_cvlan_isid'             : 'str://show vlan {0} fabric attach assignments & show fabric attach vlan {0} assignments||^\s+{0}\s+\S+\s+(?:Static|Dynamic)\s+(\d+)', # VLAN id
        'get_cvlan_ip_data'          : 'tuple://show interfaces vlan ip {0}||^{0} +(\S+) +([\d\.]+) +([\d\.]+)',
        'get_cvlan_name'             : 'str://show vlan basic {0}||^{0} +(\S+)\s', # VLAN id
        'get_directory_file_sizes'   : 'dict-reverse://ls {}||(\d\d\d\d\d+) +\S+ +\S+ +\S+ +(\S+) *$', # Path
        'get_dvr_type'               : 'str-lower://show dvr||^Role +: +(Leaf|Controller)',
        'get_fe_tunnel_src_ip_vrf'   : 'dict-diagonal://show isis||(?:ip tunnel (source)-address : (\d+\.\d+\.\d+\.\d+)|Tunnel (vrf) :(?: +(\w+))?)',
        'get_figw_image_file_size'   : 'str://ls {1}{0}||(\d\d\d\d\d+) +\S+ +\S+ +\S+ +{0} *$', # Filename, Path
        'get_figw_save_files'        : 'list://virtual-service {} exec-command "ls {}"||^(\S+)$', # FIGW VM name, FIGW local file system path
        'get_flex_uni'               : 'dict://show interfaces gigabitEthernet config {}||^(\d+/\d+(?:/\d+)?) +\S+ +\S+ +\S+ +\S+ +\S+ +(Enable|Disable)', # Port
        'get_mgmt_ip_mask'           : 'int://show mgmt ip||{}/(\d\d?) ', # IP address
        'get_mgmt_default_gateway'   : 'str://show mgmt ip route||^0\.0\.0\.0/0 +(\d+\.\d+\.\d+\.\d+) ',
        'get_mgmt_gateway_mac'       : 'str://show mgmt ip arp||^{} +\S+ +([\da-f:]+) ', # Gateway IP
        'get_mgmt_gateway_port'      : 'str://show vlan mac-address-entry {0} mac {1}||{0} +\S+ +{1} +(?:u:|Port-)(\d+/\d+(?:/\d+)?) ', # VLAN id, MAC addr
        'get_mgmt_vlan'              : 'str://show mgmt interface||^\d +Mgmt-vlan +VLAN +enable +(\d+)',
        'get_mlt_data'               : 'list://show mlt||^(?:(\d+) +\d+.+?(?:access|trunk) +(norm|smlt) +(?:norm|smlt) *(\S+)?|(\d+) +\d+ +(?:[\d\/]+|null) +(enable|disable)|(\d+) +\d+ +\S+ +\S+ +\S+ +\S+ +\S+ +(enable|disable))',
        'get_mlt_tagging'            : 'dict://show mlt||^(\d+) +\d+.+?(access|trunk)',
        'get_mlt_type'               : 'dict://show mlt||^(\d+) +\d+.+?(?:access|trunk) +(norm|smlt)',
        'get_mlt_flex_uni'           : 'dict://show mlt||^(\d+) +\d+ +\S+ +\S+ +\S+ +\S+ +\S+ +(enable|disable)',
        'get_iah_cpu_mem_resources'  : 'dict-diagonal://show virtual-service statistics||(?:Number of (Cores) Remaining: +(\d+)|Total (Memory) Remaining\(M\): +(\d+))',
        'get_in_use_spbm_nicknames'  : 'list://show isis spbm nick-name||^\w+\.\w+\.\w+\.\d\d-\d\d +\d+ +({}[0-9a-f]\.[0-9a-f][0-9a-f]) ', # seems wrong..
        'get_in_use_fabric_ids'      : 'list://show isis spbm nick-name {}||^(\w+\.\w+\.\w+)\.\d\d-\d\d +\d+ +(\w\.\w\w\.\w\w) +(\w\w:\w\w:\w\w:\w\w:\w\w:\w\w) ', # home|remote
        'get_isid_cvlan'             : 'str://show vlan i-sid||^(\d+) +{0}', # Isid
        'get_isid_type'              : 'str://show i-sid {0}||^{0} +(\S+)\s', # Isid
        'get_isid_uni_data'          : 'show running-config module i-sid',
        'get_isis_directs_redist'    : 'tuple://show ip isis redistribute||^(LOC) +\d+ +\S+ +\S+ +\S+ +\S+\s*(\S+)?',
        'get_isis_global_settings'   : 'dict-diagonal://show isis||(?:(AdminState) : (enabled|disabled)|  (System ID) : ?([\da-f]{4}\.[\da-f]{4}\.[\da-f]{4})?|(Router Name) : ?(\S+)?|ip (source-address) : ?(\d+\.\d+\.\d+\.\d+)?|(inband-mgmt-ip) : ?(\d+\.\d+\.\d+\.\d+)?)',
        'get_isis_interfaces'        : 'list://show isis interface||^(\S+) +pt-pt',
        'get_isis_manual_area'       : 'str://show isis manual-area||^([\da-fA-F\.]+)',
#        'get_isis_area'              : 'str://show isis area||^([\da-fA-F\.]+)',
        'get_isis_area'              : 'dict://show isis area||^([\da-fA-F\.]+) +(?:\S+ +(HOME|REMOTE))?',
        'get_isis_ip_clip'           : 'str://show interfaces loopback||^(\d+) +{}\s', # ISIS Source IP
        'get_l3vsn_vrf_name_pre83'   : 'str://show ip ipvpn||^\s+VRF Name\s+: (\S+)\n(?:\s+(?:Ipv[46] )?Ipvpn-state\s+: \w+\n)*\s+I-sid\s+: {}', # L3 I-SID
        'get_l3vsn_vrf_name'         : 'str://show ip ipvpn||^(\S+) +\d+ +\S+ +(?:\S+ +)?{}', # L3 I-SID
        'get_lacp_smlt_mac'          : 'str://show lacp||SmltSystemId: +(\w\w:\w\w:\w\w:\w\w:\w\w:\w\w)',
        'get_mac_address'            : 'str://show sys-info||BaseMacAddr +: +(\S+)',
        'get_4k_brouter_vlans'       : 'list://show brouter||^\s*\d+/\d+(?:/\d+)? +(4\d{3})',
        'get_4k_platform_vlans'      : 'list://show vlan basic||^(4\d{3})\s',
        'get_platform_vlans'         : 'list://show vlan basic||^(\d+) ',
        'get_platform_vlans_names'   : 'dict://show vlan basic||^(\d+) +(\S.+\S) +\S+ +\d+ +\S',
        'get_platform_vlan_types'    : 'dict://show vlan basic||^(\d+) +.+? +(\S+) +\d+ ',
        'get_sdwan'                  : 'bool://show interfaces gigabitEthernet auto-sense||SD-WAN',
        'get_smlt_role'              : 'str://show virtual-ist||(Slave|Master)',
        'get_spbm_platform_bvlans'   : 'list://show vlan basic||^(\d+) +.+? +spbm-bvlan',
        'get_spbm_global_settings'   : 'list://show isis spbm||(?:(B-VID) +PRIMARY +(NICK) +LSDB +(IP)(?: +(IPV6))?(?: +(MULTICAST))?|^\d+ +(?:(\d+)-(\d+) +\d+ +)?(?:([\da-f]\.[\da-f]{2}\.[\da-f]{2}) +)?(?:disable|enable) +(disable|enable)(?: +(disable|enable))?(?: +(disable|enable))?|^\d+ +(?:primary|secondary) +([\da-f:]+)(?: +([\da-f\.]+))?)',
        'get_static_route_next_hop'  : 'str://show ip route vrf {}||^{} +255.255.255.255 +(\d+\.\d+\.\d+\.\d+) ', # VRF name, Host Route
        'get_virtual_ist_data'       : 'list://show virtual-ist||^(?:\d+\.\d+\.\d+\.\d+ +(\d+) +\S+ +(up|down)|\S+ +\S+ +(Master|Slave))',
        'get_vlan_isids'             : 'dict-both://show vlan i-sid||^(\d+)  (?: +(\d+))?',
        'get_vlan_mac_table'         : 'dict://show vlan mac-address-entry {0}||^{0} +learned +([\da-f:]+) +(?:u:|Port-)(\d+/\d+(?:/\d+)?) ', #VLAN id
        'get_vlan_name'              : 'str://show vlan name {0}||^{0} +\d+ +(\S.*?) *$', # VLAN id
        'get_vlan_names'             : 'dict-reverse://show vlan name||^(\d+) +\d+ +(\S.*?) *$',
        'get_vlan_port_members'      : 'str-join://show vlan members {0}||^(?:{0})? +[\d\/,-]+ +([\d\/,-]+)', # VLAN id
        'get_vm_config'              : 'list://show running-config | include "virtual-service|in progress"||(?: (try the command later)|^(virtual-service {} .+$))', # VM name
        'get_vm_install_status'      : 'str://show virtual-service install {}||Status: *(\S.+\S) *$', # VM name
        'get_vm_names'               : 'dict-sequence://show virtual-service config||(?:Package: +(\S+) *$|Package App Name: +(\S+))',
        'get_vrf_name_by_id'         : 'str://show ip vrf vrfids {0}||(\S+) +{0} +(?:FALSE|TRUE)', # VRF id

        'install_vm_package'         : 'virtual-service {} install package {}{}', # VM name, VM image file path, VM image file name (run from privExec)

        'list_accept_l3isids'        : 'list://show ip isis accept vrf {0}||^- +(\d+) +- +TRUE', # VRF name
        'list_brouter_ips'           : 'list://show ip interface||^Port\S+ +(\d+\.\d+\.\d+\.\d+)',
        'list_brouter_ports'         : 'list://show brouter||^\s*(\d+/\d+(?:/\d+)?) +\d+',
        'list_cli_sessions'          : 'list://show users||^(Telnet|SSH)(\d+) +\S+ +\S+ +[\d\.\:]+ *$',
        'list_disabled_ports'        : 'list://show interfaces gigabitEthernet interface||^(\d+/\d+(?:/\d+)?).+?down +down',
        'list_fa_elements'           : 'list://show fa elements||^(?:(\d+/\d+(?:/\d+)?) +(\S+) +\d+ +\w / \w +((?:[\da-f]{2}:){5}[\da-f]{2}):((?:[\da-f]{2}:){3}[\da-f]{2}) +(\S+)|(\d+/\d+(?:/\d+)?) +(\S+) +\D)',
        'list_fa_interfaces'         : 'list://show fa interface||^(?:Mlt|Port)(\d+(?:/\d+(?:/\d+)?)?) +(enabled|disabled) +(\d+) +(\d+) +(enabled|disabled)',
        'list_fa_mlts'               : 'list://show fa interface||^Mlt(\d+)',
        'list_fabric_bmacs'          : 'list://show isis spbm unicast-fib vlan {0}||^(\S+) +{0}'.format(BVLANs[0]),
        'list_fe_tunnels_dest'       : 'dict://show isis logical-interface||^(\d+) +\S.*\S +IP +-- +-- +(\d+\.\d+\.\d+\.\d+) ',
#        'list_fe_tunnels_name'       : 'dict://show isis logical-interface name||^(\d+) +(\S.*\S)',
        'list_fe_tunnels_name'       : 'dict-reverse://show isis logical-interface name||^(\d+) +(\S.*\S)',
        'list_isis_areas'            : 'dict-reverse://show isis area||^([\da-f]+(?:\.[\da-f]+)+) +\S+ +(HOME|REMOTE)',
        'list_l3vsn_vrf_names_pre83' : 'dict-both://show ip ipvpn||^\s+VRF Name\s+: (\S+)\n(?:\s+(?:Ipv[46] )?Ipvpn-state\s+: \w+\n)*\s+I-sid\s+: (\S+)',
        'list_l3vsn_vrf_names'       : 'dict-both://show ip ipvpn||^(\S+) +\d+ +\S+ +(?:\S+ +)?(\d+)',
        'list_lacp_up_ports'         : 'list://show lacp actor-oper interface gigabitethernet {}||^(\d+/\d+(?:/\d+)?) +\d+ +\d+ +\d+ +\S+ +\S+ +short +indi +sync +col +dis', # Port list
        'list_link_up_ports'         : 'list://show interfaces gigabitEthernet interface {}||^(\d+/\d+(?:/\d+)?).+?up +up', # Ports
        'list_lldp_neighbours'       : 'dict://show lldp neighbor summary||^(\d+/\d+(?:/\d+)?) +LLDP +\S+ +\S+ +\S+ +\S+ +(.+)$',
        'list_loopbacks'             : 'dict://show interfaces loopback||^(\d+) +(\d+\.\d+\.\d+\.\d+)',
        'list_mgmt_arp_cache_macs'   : 'str://show mgmt ip arp||^\d+\.\d+\.\d+\.\d+ +\S+ +([\da-f:]+) ',
        'list_mgmt_interfaces'       : 'list://show mgmt interface||^\d +\S+ +([A-Z]+) ',
        'list_mgmt_ips'              : 'dict://show mgmt ip||^\d +(\S+) +(\d+\.\d+\.\d+\.\d+)/\d',
        'list_mlt_lacp_key'          : 'dict://show lacp interface mlt||^(\d+) +\d+ +\d+ +\S+ +\d+ +(\d+)',
        'list_ntp_servers'           : 'list://show ntp server ||^(\d+\.\d+\.\d+\.\d+)',
        'list_oob_mgmt_ips'          : 'list://show ip interface vrfids 512||^(?:Portmgm\d?|MgmtVirtIp|mgmt-oob) +(\d+\.\d+\.\d+\.\d+)',
        'list_port_lacp_key'         : 'dict://show lacp actor-oper interface||^(\d+/\d+(?:/\d+)?) +(\d+)',
        'list_port_up_speed'         : 'dict://show interfaces gigabitEthernet name {}||^(\d+/\d+(?:/\d+)?).+?up +full +(\d+) +\S+$', # Port list
        'list_port_voss_neighbours'  : 'dict://show lldp neighbor summary port {}||^(\d+/\d+(?:/\d+)?) +LLDP +\S+ +(\S+) +\S+ +\S+ +(?:VSP|XA)', # Port list
        'list_radius_ept_servers'    : 'list://show radius-server ||^(\d+\.\d+\.\d+\.\d+) +endpoint-tracking',
        'list_slpp_ports'            : 'list://show slpp interface gigabitEthernet||^(\d+/\d+(?:/\d+)?) +enabled',
        'list_software'              : 'dict://show software ||^(\w\S+)(?: +\((Primary|Backup|Next Boot) \S+\))?(?: +\((?:Signed|Unsigned) \S+\))? *$',
        'list_vlacp_ports'           : 'dict://show vlacp interface gigabitethernet {}||^(\d+/\d+(?:/\d+)?) +(true|false) +(?:true|false)', # Port list
        'list_vlan_default_ports'    : 'list://show interfaces gigabitEthernet vlan||^(\d+/\d+(?:/\d+)?) +disable +false +false +(?:1 +1|0 +0) +normal +disable',
        'list_port_vlans'            : 'list://show interfaces gigabitEthernet vlan {}||^(\d+/\d+(?:/\d+)?) +enable +false +\S+ +(\d+) +([\d,]+) +normal +(enable|disable)', # Ports
        'list_vlans'                 : 'list://show vlan basic||^(\d+) ',
        'list_vms'                   : 'list://show virtual-service config||Package: +(\S+) *$',
        'list_voss_neighbour_macs'   : 'dict-reverse://show lldp neighbor summary||^(\d+/\d+(?:/\d+)?) +LLDP +\S+ +([\da-f:]+)',
        'list_vrf_ip_interfaces'     : 'dict://show ip interface {}||^\S+ +(\d+\.\d+\.\d+\.\d+) +(\d+\.\d+\.\d+\.\d+)', # 'vrf <VRF-name>'
        'list_vrf_vlans'             : 'list://show ip interface vrf {}||^Vlan(\d+)\s', # VRF name
        'list_vrf_clip_ips'          : 'list://show ip interface vrf {}||^Clip\d+ +(\d+\.\d+\.\d+\.\d+)', # VRF name
        'list_vrfs'                  : 'dict-reverse://show ip vrf||(\S+) +(\d+) +\d+ +\d+ +[TF]',

        'log_message'                : 'logging write "{}"', # Message

        'measure_l2ping_rtt'         : 'tuple://l2 ping vlan {} routernodename {} burst-count {}||min/max/ave/stdv = +\d+/\d+/(\d+\.\d+)/ *(\d+\.\d+)', # BVLAN, Sysname, Burst

        'port_add_vlan'              : 'vlan members add {} {}', # VLAN id, Ports
        'port_disable'               : 'shutdown',
        'port_disable_lacp'          : 'no lacp enable; no lacp aggregation enable; default lacp',
        'port_disable_poe'           : 'interface gigabitEthernet {}; poe poe-shutdown', # Port list
        'port_disable_slpp_guard'    : 'no slpp-guard enable',
        'port_disable_spoof_detect'  : 'no spoof-detect',
        'port_disable_tagging'       : 'no encapsulation dot1q',
        'port_disable_vlacp'         : 'default vlacp',
        'port_disable_with_stp'      : 'interface gigabitEthernet {}; shutdown; spanning-tree mstp force-port-state enable; exit', # Port list
        'port_enable'                : 'no shutdown',
        'port_enable_lacp'           : 'lacp key {} aggregation enable timeout-time short; lacp enable', # LACP key
        'port_enable_lacp_indi'      : 'lacp timeout-time short; lacp enable',
        'port_enable_no_stp'         : 'interface gigabitEthernet {}; no spanning-tree mstp\ny; no shutdown; exit', # Port list
        'port_enable_poe'            : 'interface gigabitEthernet {}; no poe-shutdown', # Port list
        'port_enable_slpp_guard'     : 'slpp-guard enable',
        'port_enable_spoof_detect'   : 'spoof-detect',
        'port_enable_vlacp'          : 'vlacp fast-periodic-time 500 timeout short timeout-scale 5 funcmac-addr 01:80:c2:00:00:0f; vlacp enable',
        'port_enable_tagging'        : 'encapsulation dot1q',
        'port_fa_detection_enable'   : # Port list
                                       '''
                                       interface gigabitEthernet {}
                                          no spanning-tree mstp\ny
                                          fa
                                          fa enable
                                          lacp enable timeout-time short
                                          vlacp fast-periodic-time 500 timeout short funcmac-addr 01:80:c2:00:00:0f
                                          vlacp enable
                                          no shutdown
                                       exit
                                       ''',
        'port_fa_detection_disable'  : # Port list
                                       '''
                                       interface gigabitEthernet {}
                                          shutdown
                                          no fa
                                          no lacp enable
                                          lacp timeout-time long
                                          no encapsulation dot1q
                                          spanning-tree mstp force-port-state enable
                                       exit
                                       ''',
        'port_remove_vlan1'          : 'vlan members remove 1 {}', # Port list
        'port_readd_vlan1'           : 'vlan members add 1 {}', # Port list
        'port_config_isis'           : 'isis; isis spbm 1; isis enable',
        'port_config_isis_auth'      : { # ISIS Auth key
            'HMAC-MD5'               : 'isis hello-auth type hmac-md5 key {}',
            'HMAC-SHA2'              : 'isis hello-auth type hmac-sha-256 key {}',
                                       },
        'port_config_isis_metric'    : 'interface gigabitEthernet {0}; isis spbm 1 l1-metric {1}', # Port list, Metric

        'ports_delete_ept'           : 'interface gigabitEthernet {0}; no endpoint-tracking; exit', # Port
        'ports_disable_ept'          : 'interface gigabitEthernet {0}; no endpoint-tracking enable; exit', # Port
        'ports_enable'               : 'interface gigabitEthernet {0}; no shutdown; exit', # Port
        'ports_enable_ept'           : 'interface gigabitEthernet {0}; endpoint-tracking enable; exit', # Port

        'reboot_switch'              : 'reset -y',

        'relocate_mgmt_vlan_ip'      : # {0} = VLAN id, {1} = Mgmt IP, {2} = Mgmt Mask, {3} = Gateway IP, {4} = Port
                                       '''
                                       no mgmt vlan\ny
                                       mgmt vlan {0}
                                          ip address {1}/{2}
                                          ip route 0.0.0.0/0 next-hop {3} weight 200
                                          enable
                                       exit
                                       vlan members add {0} {4}
                                       ''',

        'rename_fe_tunnel'           : # {0} = FE Tunnel id, {1} = FE Tunnel dest IP, {2} = FE Tunnel name
                                       '''
                                       logical-intf isis {0} dest-ip {1} name {2}
                                       exit
                                       ''',

        'set_autosense_data'         : # {0} = I-SID
                                       '''
                                       auto-sense data i-sid {0}
                                       i-sid name {0} "Auto-sense Data"
                                       ''',
        'set_autosense_wap'          : # {0} = I-SID
                                       '''
                                       auto-sense fa wap-type1 i-sid {0}
                                       i-sid name {0} "Auto-sense WapType1"
                                       ''',
        'set_autosense_fa_auth'      : 'auto-sense fa message-authentication; auto-sense fa authentication-key {}', # Auth key
        'set_autosense_isis_auth'    : 'auto-sense isis hello-auth type hmac-sha-256 key {}', # Auth key
        'set_autosense_voice_tag'    : # {0} = I-SID, {1} = VLAN id
                                       '''
                                       auto-sense voice i-sid {0} c-vid {1}
                                       i-sid name {0} "Auto-sense Voice"
                                       ''',
        'set_autosense_voice_untag'  : # {0} = I-SID
                                       '''
                                       auto-sense voice i-sid {0} untagged
                                       i-sid name {0} "Auto-sense Voice"
                                       ''',
        'set_autosense_sdwan_vrf'    : 'auto-sense sd-wan vrf {}', # VRF name / GlobalRouter
        'set_autosense_wait_interval': 'auto-sense wait-interval {}', # Wait Interval
        'set_cfm_spbm_mepid'         : 'cfm spbm mepid {}', # Mep id
        'set_cvlan_isid'             : 'vlan i-sid {0} {1}', # {0} = VLAN id; {1} = i-sid 
        'set_cvlan_name'             : 'vlan name {0} {1}', # {0} = VLAN id; {1} = Name
        'set_fa_mgmt_isid'           : 'fa management i-sid {}', # I-SID
        'set_fa_mgmt_vlan_isid'      : 'fa management i-sid {} c-vid {}', # I-SID, VLAN
        'set_isid_name'              : 'i-sid name {} "{}"', # I-SID, Name
        'set_isis_if_auth'           : { # ISIS Auth key
            'HMAC-MD5'               : 'isis hello-auth type hmac-md5 key {}',
            'HMAC-SHA2'              : 'isis hello-auth type hmac-sha-256 key {}',
                                       },
        'set_lacp_smlt_sys_id'       : 'lacp smlt-sys-id {}', # SmltVirtBmac
        'set_mlt_ports'              : 'mlt {} member {}', # MLT id, Port list
        'set_isis_if_metric'         : 'isis spbm 1 l1-metric {}', # Metric
        'set_isis_spbm_ip_enable'    : 'ip-source-address {}; spbm 1 ip enable', # IP address
        'set_isis_sys_name'          : 'sys-name {}', # SysName
        'set_isis_system_id'         : 'system-id {}', # System id
        'set_mlt_lacp_key'           : 'lacp enable key {}', # LACP key
        'set_radius_reachability'    : 'radius reachability mode status-server',
        'set_spbm_bvids'             : 'spbm 1 b-vid {0}-{1} primary {0}', # Bvid#1, Bvid#2
        'set_spbm_nickname'          : 'spbm 1 nick-name {}', # Nickname
        'set_spbm_smlt_peer'         : 'spbm 1 smlt-peer-system-id {}', # SysId
        'set_spbm_smlt_virt_bmac'    : 'spbm 1 smlt-virtual-bmac {}', # Bmac
        'set_sys_name'               : 'prompt {}', # SysName
        'set_timezone'               : 'clock time-zone {} {}', # Zone
        'set_vlan_name'              : 'vlan name {0} "{1}"', # {0} = VLAN id; {1} = Name

        'start_vm'                   : # {0} = VM name, {1} = CPUs, {2} = Memory, {3} = Vport name, {4} = Vport type, {5} = Insight port
                                       '''
                                       virtual-service {0}
                                       virtual-service {0} num-cores {1}
                                       virtual-service {0} mem-size {2}
                                       virtual-service {0} vport {3} connect-type {4}
                                       virtual-service {0} vport {3} port {5}
                                       virtual-service {0} enable
                                       vlan members remove 1 {5}
                                       interface gigabitEthernet {5}
                                           encapsulation dot1q
                                           no spanning-tree mstp\ny
                                           no shutdown
                                       exit
                                       ''',
    },
    'Summit Series': {
        'disable_more_paging'        : 'disable cli paging',
        'disable_cli_prompting'      : 'disable cli prompting',
        'save_config'                : 'save configuration',

        'check_cvlan_exists'         : 'bool://show vlan||^\S+ +{0}\s', # VLAN id

        'clear_cvlan_isid'           : 'configure vlan {0} delete isid {1}', # {0} = VLAN id; {1} = i-sid 

        'create_cvlan'               : 'create vlan {}', # VLAN id
        'create_cvlan_uni'           : { # {0} = VLAN id; {1} = port-list
            'tag'                    : 'configure vlan {0} add ports {1} tagged',
            'untag'                  : 'configure vlan {0} add ports {1} untagged',
                                       },
        'create_lacp_lag'            : 'enable sharing {} grouping {} algorithm address-based L3_L4 lacp', # Port1, Port list
        'create_static_mlt'          : 'enable sharing {} grouping {} algorithm address-based L3_L4', # Port1, Port list
        'create_syslog_server'       : # {0} = IP; {1} = VR; {2} = facility
                                       '''
                                       configure syslog add {0}:514 vr {1} {2}
                                       enable log target syslog {0}:514 vr {1} {2}
                                       configure log target syslog {0}:514 vr {1} {2} filter DefaultFilter severity Debug-Data
                                       configure log target syslog {0}:514 vr {1} {2} match Any
                                       configure log target syslog {0}:514 vr {1} {2} format timestamp seconds date Mmm-dd event-name condition priority host-name tag-name
                                       ''',

        'delete_all_syslog_servers'  : 'configure syslog delete all',
        'delete_cvlan'               : 'delete vlan {}', # VLAN id
        'delete_cvlan_uni'           : 'configure vlan {0} delete ports {1}', # {0} = VLAN id; {1} = port-list
        'delete_vm_files'            : 'rm /usr/local/vm/packages/*\ny',

        'enable_igmp_on_vlan'        : 'enable igmp vlan {} IGMPv{}', # VLAN name, IGMP Version 1/2/3

        'get_chassis_mac'            : 'str://show switch | include "System MAC"||^System MAC: +(\S+)',
        'get_cvlan_isid'             : 'str://show vlan {0} fabric attach assignments||^ +{0} +\S+ +(?:Static|Dynamic) +(\d+)', # VLAN id
        'get_cvlan_name'             : 'str://show vlan||^(\S+) +{0}\s', # VLAN id
        'get_ip_vr'                  : 'str://show vlan|| {}[ /].+? (\S+) *$', # IP
        'get_isid_cvlan'             : 'str://show vlan fabric attach assignments||^ +(\d+) +\S+ +Static +{0}', # Isid
        'get_mac_address'            : 'show switch||^System MAC: +(\S+)',
        'get_mlt_data'               : 'list://show sharing||^ +(?:((?:\d+:)?\d+)(?: +(?:\d+:)?\d+)? +(LACP|Static) +\d+ +)?\w+(?: +\w+)? +((?:\d+:)?\d+)',
        'get_vm_data'                : 'list://show vm detail | include Memory|CPUs|Slot||(?:Memory size: +(\d+) MB|CPUs: +(\d)|Slot: +(\d))',

        'list_all_vlans'             : 'dict-reverse://show vlan ||^(\S+) +(\d+) ',
        'list_fa_elements'           : 'list://show fabric attach elements||^((?:[\da-f]{2}-){5}[\da-f]{2})-((?:[\da-f]{2}-){3}[\da-f]{2}) +((?:\d+:)?\d+) +(.+?) +(?:\d+|None)\s\S',

        'port_disable_poe'           : 'disable inline-power ports {}', # Port list
        'port_enable_poe'            : 'enable inline-power ports {}', # Port list

        'set_cvlan_isid'             : 'configure vlan {0} add isid {1}', # {0} = VLAN id; {1} = i-sid 
        'set_cvlan_name'             : 'configure vlan {0} name {1}', # {0} = VLAN id; {1} = Name

    },
    'ERS Series': {
        'disable_more_paging'        : 'terminal length 0',
        'enable_context'             : 'enable',
        'config_context'             : 'config term',
        'port_config_context'        : 'interface Ethernet {}', # List of ports
        'exit_config_context'        : 'exit',
        'end_config'                 : 'end',
        'save_config'                : 'copy config nvram',

        'check_cvlan_exists'         : 'bool://show vlan id {0}||^{0}\s', # VLAN id
        'check_ntp_support'          : 'show ntp', # Used to check if NTP is supported; on ERS models which do not support NTP we expect to get an error

        'clear_cvlan_isid'           : 'no i-sid {1} vlan {0}', # {0} = VLAN id; {1} = i-sid 
        'clear_fa_auth_key'          : 'configure fabric attach ports {} authentication key default', # Port list

        'config_eapol_global'        : # (do not config multihost allow-non-eap-enable; it is for switch local MAC based authentication without RADIUS)
                                       '''
                                       eapol multihost radius-non-eap-enable
                                       eapol multihost use-radius-assigned-vlan
                                       eapol multihost non-eap-use-radius-assigned-vlan
                                       eapol multihost eap-packet-mode unicast
                                       eapol multihost non-eap-reauthentication-enable
                                       no eapol multihost non-eap-pwd-fmt ip-addr
                                       no eapol multihost non-eap-pwd-fmt port-number
                                       eapol enable
                                       fa extended-logging
                                       ''',
        'config_eapol_mhsa'          : 'eapol multihost auto-non-eap-mhsa-enable',
        'config_eapol_mirroring'     : {
            'enable'                 : 'eapol allow-port-mirroring',
            'disable'                : 'no eapol allow-port-mirroring',
                                       },
        'config_eapol_multivlan'     : 'eapol multihost multivlan enable', # This command may be obsolete on recent ERS models/software
        'config_failopen_vlan'       : 'eapol multihost fail-open-vlan vid {}', # VLAN id
        'config_radius_coa_reauth'   : 'radius dynamic-server client {0} process-reauthentication-requests', # Radius server; not implemented on all ERS models
        'config_radius_primary'      : # {0} = Primary Radius Server IP, {1} = Radius secret, {2} = 'acct-enable' or ''
                                       '''
                                       no radius use-management-ip
                                       radius server host {0} key {1} {2}
                                       radius accounting interim-updates enable
                                       radius dynamic-server client {0} secret {1}
                                       radius dynamic-server client {0} process-change-of-auth-requests
                                       radius dynamic-server client {0} process-disconnect-requests
                                       radius dynamic-server client {0} enable
                                       ''',
        'config_radius_reachability' : { # {0} = Dummy username, {1} = Dummy password
            'use-icmp'               : 'radius reachability mode use-icmp',
            'use-radius'             : 'radius reachability mode use-radius username {0} password {1}',
                                       },
        'config_radius_secondary'    : # {0} = Secondary Radius Server IP, {1} = Radius secret, {2} = 'acct-enable' or ''
                                       '''
                                       radius server host {0} secondary key {1} {2}
                                       radius dynamic-server client {0} secret {1}
                                       radius dynamic-server client {0} process-change-of-auth-requests
                                       radius dynamic-server client {0} process-disconnect-requests
                                       radius dynamic-server client {0} enable
                                       ''',

        'create_cvlan'               : 'vlan create {} type port', # VLAN id
        'create_cvlan_uni'           : { # {0} = VLAN id; {1} = port-list
            'tag'                    : 'vlan ports {1} tagging tagAll; vlan members add {0} {1}',
            'untag'                  : 'vlan ports {1} tagging untagAll; vlan members add {0} {1}',
                                       },
        'create_lacp_lag'            : '''
                                       lacp key {2} mlt-id {0}
                                       mlt 1 loadbalance advance
                                       mlt 1 learning disable
                                       interface fastEthernet {1}
                                          lacp key {2}
                                          lacp aggregation enable
                                          lacp mode passive
                                       exit
                                       ''', # MLT id, Port list, Key
        'create_ntp_server'          : 'ntp server {} enable', # IP
        'create_sntp_server1'        : 'sntp server primary address {}', # IP
        'create_sntp_server2'        : 'sntp server secondary address {}', # IP
        'create_static_mlt'          : '''
                                       mlt {0} member {1} learning disable
                                       mlt {0} loadbalance advance
                                       ''', # MLT id, Port list
        'create_vlacp_mlt'           : '''
                                       mlt {0} member {1} learning disable
                                       mlt {0} loadbalance advance
                                       vlacp macaddress 01:80:c2:00:00:0f
                                       interface fastEthernet {1}
                                          vlacp timeout short
                                          vlacp timeout-scale 5
                                          vlacp enable
                                       exit
                                       ''', # MLT id, Port list

        'delete_cvlan'               : 'vlan delete {0}', # {0} = VLAN id
        'delete_cvlan_uni'           : 'vlan members remove {0} {1}', # {0} = VLAN id; {1} = port-list
        'delete_ntp_server'          : 'no ntp server {}', # IP
        'delete_radius_coa_client'   : 'no radius dynamic-server client {}', # Client IP
        'delete_sntp_servers'        : 'no sntp enable; no sntp server primary; no sntp server secondary',

        'disable_more_paging'        : 'terminal length 0',
        'disable_password_security'  : 'no password security',
        'disable_coa_replay_protect' : 'no radius dynamic-server replay-protection',
        'disable_dhcp_relay'         : 'no ip dhcp-relay', # We only do this on ERS3500, to free up resources to enable eapol
        'disable_eapol_global'       : 'eapol disable',

        'enable_coa_replay_protect'  : 'radius dynamic-server replay-protection',
        'enable_fa_auth_key'         : 'configure fabric attach ports {} authentication enable', # Port list
        'enable_failopen'            : 'eapol multihost fail-open-vlan enable',
        'enable_failopen_continuity' : 'eapol multihost fail-open-vlan continuity-mode enable',
        'enable_more_paging'         : 'terminal length {}', # Terminal length, usually 23
        'enable_ntp'                 : 'ntp; clock source ntp',
        'enable_password_security'   : 'password security',
        'enable_sntp'                : 'sntp enable; clock source sntp',

        'get_autosave'               : 'str-lower://show autosave ||(Enabled|Disabled)',
        'get_chassis_mac'            : 'str://show sys-info||^MAC Address: +(\S+)',
        'get_clock_source'           : 'str://show clock detail ||System Clock Source +: +(\S+)',
        'get_cvlan_isid'             : 'str://show vlan i-sid {0}||^{0} +(\d+)', # VLAN id
        'get_cvlan_name'             : 'str://show vlan||^{0} +(\S.+\S) +Port', # VLAN id
        'get_fabric_mode'            : 'list://show fa agent ||(?:Fabric Attach Element Type: (Server|Proxy)|Fabric Attach Provision Mode: VLAN \((Standalone)\))',
        'get_isid_cvlan'             : 'str://show vlan i-sid||^(\d+) +{0}', # Isid
        'get_mac_address'            : 'show sys-info||^MAC Address: +(\S+)',
        'get_mlt_data'               : 'list://show mlt||^(\d+) +.+?[^#]([\d\/,-]+|NONE) +(?:Single|All) +\S+ +(Enabled|Disabled)(?: +(?:Trunk|Access))? +(NONE|\d+)',
        'get_password_security'      : 'str://show password security ||(enabled|disabled)',
        'get_spanning_tree_mode'     : 'str://show spanning-tree mode ||^Current STP Operation Mode: (\w+)',
        'get_stacking_mode'          : 'str://show sys-info ||^Operation Mode: +(Switch|Stack)',
        'get_terminal_length'        : 'int://show terminal ||Terminal length: (\d+)',

        'list_faclient_ports'        : {
            'Switch'                 : 'list://show fa elements ||^1\/(\d+) +Client',
            'Stack'                  : 'list://show fa elements ||^(\d\/\d+) +Client',
                                       },
        'list_fa_elements'           : 'list://show fa elements||^(?:(\d+/\d+|MLT\d+) +(\S+) +\d+ +\w / \w +((?:[\da-f]{2}:){5}[\da-f]{2}):((?:[\da-f]{2}:){3}[\da-f]{2}) +(\S+)|(\d+/\d+|MLT\d+) +.+?((?:success|fail)\S+)\s)',
        'list_faproxy_ports'         : {
            'Switch'                 : 'list://show fa elements ||^1\/(\d+) +Proxy',
            'Stack'                  : 'list://show fa elements ||^(\d\/\d+) +Proxy',
                                       },
        'list_mirror_monitor_ports'  : 'list://show port-mirroring||^Monitor Port: +((?:\d\/)?\d+)',
        'list_mlt_ports'             : 'list://show mlt ||^\d[\d ] .{16} ([\d\/,-]+)',
        'list_no_vlan_ports'         : 'list://show vlan interface vids||^((?:\d\/)?\d+)\s*$',
        'list_ntp_servers'           : 'list://show ntp server ||^(\d+\.\d+\.\d+\.\d+)',
        'list_radius_coa_clients'    : 'list://show radius dynamic-server ||^(\d+\.\d+\.\d+\.\d+)',
        'list_sntp_servers'          : 'list://show sntp ||server address: +([1-9]\d*\.\d+\.\d+\.\d+)',
        'list_uplink_ports'          : {
            'Server'                 : 'show isis interface ||^Port: ((?:\d\/)?\d+)',
            'Proxy'                  : 'show fa elements ||^(\d\/(\d+)) +Server',
            'StandaloneProxy'        : 'show fa uplink ||^  Port - ((?:\d\/)?\d+)',
                                       },

        'port_config_eap_common'     : '''
                                       default eapol multihost
                                       eapol multihost use-radius-assigned-vlan
                                       eapol multihost eap-packet-mode unicast
                                       eapol status auto re-authentication enable
                                       eapol radius-dynamic-server enable
                                       fa port-enable
                                       ''',
        'port_config_eap_mode'       : {
            'SHSA'                   : 'eapol multihost mac-max 1',
            'MHMA'                   : '', # port_config_eap_common above covers for MHMA already
            'MHSA'                   : 'eapol multihost auto-non-eap-mhsa-enable mhsa-no-limit',
                                       },
        'port_config_eap_type'       : {
            'Both'                   : # (do not config multihost allow-non-eap-enable; it is for switch local MAC based authentication without RADIUS)
                                       '''
                                       eapol multihost radius-non-eap-enable
                                       eapol multihost non-eap-use-radius-assigned-vlan
                                       ''',
            '802X'                   : '', # port_config_eap_common above covers for 802X already
            'NEAP'                   : # (do not config multihost allow-non-eap-enable; it is for switch local MAC based authentication without RADIUS)
                                       '''
                                       eapol multihost radius-non-eap-enable
                                       eapol multihost non-eap-use-radius-assigned-vlan
                                       no eapol multihost eap-protocol-enable
                                       ''',
                                       },
        'port_config_failopen_vlan'  : 'eapol multihost fail-open-vlan enable',
        'port_config_failopen_pvid'  : 'eapol multihost fail-open-vlan enable vid port-pvid',
        'port_config_faststart'      : {
            'STPG'                   : 'spanning-tree learning fast',
            'RSTP'                   : 'spanning-tree rstp learning enable; spanning-tree rstp edge-port true',
            'MSTP'                   : 'spanning-tree mstp learning enable; spanning-tree mstp edge-port true',
                                       },
        'port_config_multihost'      : 'eapol multihost enable', # This command may be obsolete on recent ERS models/software
        'port_config_reauth_timer'   : 'eapol re-authentication-period {}', # Value
        'port_config_traffic_control': 'eapol traffic-control {}', # 'in', 'in-out'

        'port_disable_eap'           : 'default eapol; default eapol multihost fail-open-vlan',
        'port_disable_fa'            : 'no fa port-enable',
        'port_disable_poe'           : 'interface fastEthernet {}; poe poe-shutdown', # Port list
        'port_enable_fa'             : 'fa port-enable',
        'port_enable_poe'            : 'interface fastEthernet {}; no poe-shutdown', # Port list
        'port_readd_vlan1'           : 'vlan members add 1 {}', # Port list

        'set_cvlan_isid'             : 'i-sid {1} vlan {0}', # {0} = VLAN id; {1} = i-sid
        'set_cvlan_name'             : 'vlan name {0} {1}', # {0} = VLAN id; {1} = Name
        'set_fa_auth_key'            : 'configure fabric attach ports {} authentication key {}', # Port list, Auth key
        'set_radius_encap'           : 'radius-server encapsulation {}', # pap|ms-chap-v2 ; this command does not exist on lower end ERS models (3600,3500)
        'set_timezone'               : 'clock time-zone {} {} {}', # Zone, hours-offset, minutes
        'set_vlan_cfgctrl_automatic' : 'vlan configcontrol automatic',
    },
    'ISW-Series': {
        'disable_more_paging'        : 'terminal length 0',
        'config_context'             : 'config term',
        'get_mgmt_ip_vlan_and_mask'  : 'tuple://show ip interface brief ||^VLAN (\d+) +{}/(\d+) +DHCP', # IP address; returns mask bits
        'get_mgmt_ip_gateway'        : 'str://show ip route ||^0\.0\.0\.0\/0 via (\d+\.\d+\.\d+\.\d+)',
        'set_mgmt_ip_gateway'        : 'ip route 0.0.0.0 0.0.0.0 {}', # Default Gateway IP
        'set_mgmt_ip'                : 'interface vlan {}; ip address {} {}; exit', # Mgmt VLAN, IP address, IP Mask
        'modify_admin_user'          : 'username admin privilege 15 password unencrypted {}', # Admin Password
        'default_admin_user'         : 'username admin privilege 15 password none',
        'delete_admin_user'          : 'no username admin',
        'create_cli_user'            : 'username {0} privilege 15 password unencrypted {1}; enable password {1}', # Username, Password
        'delete_cli_user'            : 'no username {}', # Username
        'set_snmp_version'           : 'snmp-server version v{}', # Version
        'set_snmp_read_community'    : 'snmp-server community v2c {} ro', # Community
        'set_snmp_write_community'   : 'snmp-server community v2c {} rw', # Community
        'create_snmp_v3_user'        : { # {0} = User; {1} = AuthType; {2} = AuthPassword; {3} = PrivType; {4} = PrivPassword; {5} = ro/rw
            'NoAuthNoPriv'           : '''
                                       snmp-server user {0} engine-id 800007e5017f000001
                                       snmp-server security-to-group model v3 name {0} group default_{5}_group
                                       ''',
            'AuthNoPriv'             : '''
                                       snmp-server user {0} engine-id 800007e5017f000001 {1} {2}
                                       snmp-server security-to-group model v3 name {0} group default_{5}_group
                                       ''',
            'AuthPriv'               : '''
                                       snmp-server user {0} engine-id 800007e5017f000001 {1} {2} priv {3} {4}
                                       snmp-server security-to-group model v3 name {0} group default_{5}_group
                                       ''',
                                       },
        'delete_snmp_communities'    : 'no snmp community v3 public; no snmp community v3 private',
        'delete_snmp_v3_default_user': 'no snmp-server user default_user engine-id 800007e5017f000001',
        'port_disable_poe'           : 'interface * 1/{}; poe mode disable', # Port list
        'port_enable_poe'            : 'poe mode enable', # Port list
        'end_config'                 : 'end',
    },
    'ISW-Series-Marvell': {
        'enable_context'             : 'enable',
        'config_context'             : 'configure',
        'disable_more_paging_cfg'    : 'setenv pagefilter 0',
#        'disable_more_paging_cfg'    : 'configure; setenv pagefilter 0; exit',
        'get_mgmt_ip_vlan'           : 'str://show fa elements ||^\S+ +FA Server +(\d+)',
        'get_mgmt_ip_mask_and_gw'    : 'list-diagonal://show ip dhcp client {} ||^ +(?:IP Address +: {}\/(\d+\.\d+\.\d+\.\d+)|Default Gateway: (\d+\.\d+\.\d+\.\d+))', #Mgmt VLAN, IP Address; returns dotted mask
        'set_mgmt_ip_gateway'        : 'default-gateway {}', # Default Gateway IP
        'set_mgmt_ip'                : 'interface vlan {}; ip address {} {}; exit', # Mgmt VLAN, IP address, IP Mask
        'modify_admin_user'          : 'account modify admin password {}', # Admin Password
        'default_admin_user'         : 'account modify admin password ""',
        'delete_admin_user'          : 'account delete admin',
        'create_cli_user'            : 'account add {} password {} level superuser', # Username, Password
        'delete_cli_user'            : 'account delete {}', # Username
        'set_snmp_version'           : 'snmp version v{}', # Version / Does not support v1
        'set_snmp_read_community'    : 'snmp delete-community name public; snmp create-community ro {}', # Community
        'set_snmp_write_community'   : 'snmp create-community rw {}', # Community
        'create_snmp_v3_user'        : { # {0} = User; {1} = AuthType; {2} = AuthPassword; {3} = PrivType; {4} = PrivPassword; {5} = ro/rw
            'NoAuthNoPriv'           : 'snmp create-user {0} access {5}',
            'AuthNoPriv'             : 'snmp create-user {0} access {5} {1} {2}',
            'AuthPriv'               : 'snmp create-user {0} access {5} {1} {2} {3} {4}', # Does not support aes
                                       },
        'delete_snmp_communities'    : 'snmp delete-community name public',
        'delete_snmp_v3_default_user': 'no snmp-server user default_user engine-id 800007e5017f000001',
        'end_config'                 : 'exit',
    },
}
