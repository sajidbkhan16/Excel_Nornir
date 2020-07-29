# convert list of dictionaries into string config from template
def jinja_config_int(list_config, template_int):

    interface_configs = ''
    for interface in list_config:
        if 'Node Interface' in interface.keys():
            interface_config = template_int.render(
                            interface = interface['Node Interface'],
                            description = interface['Node Description'],
                            vrf = interface['Node VRF'],
                            ip = interface['Node IP'],
                            mask = interface['Node Mask']
                        )
            
        interface_configs += interface_config
                            
    return interface_configs

def jinja_config_vrf(list_config, template_vrf):

    vrf_configs = ''
    for vrf in list_config:
        if 'Node Name' in vrf.keys():
            vrf_config = template_vrf.render(
                            vrf = vrf['VRF Name'],
                            rd = vrf['RD'],
                            rt_import = vrf['import RT'],
                            rt_export = vrf['export RT']
                        )
            
        vrf_configs += vrf_config
    
    return vrf_configs

def jinja_config_routing(list_config, template_routing):

    routing_configs = ''
    for routing in list_config:
        if 'Node Name' in routing.keys():
            routing_config = template_routing.render(
                                Next_hop_Interface = routing['Next-hop Interface'],
                                Destination_IP = routing['Destination IP'],
                                Mask = routing['Mask'],
                                Next_hop_IP = routing['Next-hop IP'],
                                vrf = routing['vrf']
                            )
        
        routing_configs += routing_config
                                
    return routing_configs
            
        
    
    

