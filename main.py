from helper_func import * 
import os
import json
import pandas as pd
from jinja2 import Template
from nornir import InitNornir
from nornir.plugins.tasks import commands
from nornir.plugins.tasks.networking import netmiko_send_command, netmiko_send_config
from nornir.plugins.functions.text import print_result

# define the path of configuration file stored in excel format
excel_path = os.path.join(os.getcwd(), r'Excel_folder\configurations\config.xlsx')

# candidate config path
candidate_path = os.path.join(os.getcwd(), r'candidate_config')

# jinja2 template interface config
interface_jinja2_file = r'jinja2-templates\interfaces.j2'
interface_jinja2_path = os.path.join(os.getcwd(), interface_jinja2_file)

# jinja2 template vrf config
vrf_jinja2_file = r'jinja2-templates\vrf.j2'
vrf_jinja2_path =  os.path.join(os.getcwd(), vrf_jinja2_file)

# jinja2 template routing config
routing_jinja2_file = r'jinja2-templates\routing.j2'
routing_jinja2_path =  os.path.join(os.getcwd(), routing_jinja2_file)

# Columns Node A and Node B
columns_A = ['Node A Name', 'Node A Interface', 'Node A Description', 'Node A VRF', 'Node A IP', 'Node A Mask']
columns_B = ['Node B Name', 'Node B Interface', 'Node B Description', 'Node B VRF', 'Node B IP', 'Node B Mask']
columns = ['Node Name', 'Node Interface', 'Node Description', 'Node VRF', 'Node IP', 'Node Mask']

# import excel file and convert to list of dicts from 'P2P' sheet
df_int = pd.read_excel(excel_path, sheet_name='P2P')
df_NodeA = pd.DataFrame(df_int, columns = columns_A)
df_NodeB = pd.DataFrame(df_int, columns = columns_B)

# convert nodeA and nodeB config into list of dict format
df_listA = df_NodeA.to_dict('records')
df_listB = df_NodeB.to_dict('records')

# import excel file and convert to list of dicts from 'vrf' sheet
df_vrf = pd.read_excel(excel_path, sheet_name='vrf')
df_list_vrf = df_vrf.to_dict('records')

# import excel file and convert to list of dicts from 'routing' sheet
df_routing = pd.read_excel(excel_path, sheet_name='routing')
df_list_routing = df_routing.to_dict('records')

# capture unique Node names so that config can be prepared per node basis in subsequent steps
NodeSetP2P = set()    # Unique P2P Node Set
for Dict in df_listA:
    NodeSetP2P.add(Dict['Node A Name'])

for Dict in df_listB:
    NodeSetP2P.add(Dict['Node B Name'])

NodeSetRouting = set()    # Unique P2P Node Set
for Dict in df_list_routing:
    NodeSetRouting.add(Dict['Node Name'])

NodeSetFinal = NodeSetRouting.union(NodeSetP2P)

# replace the old key values with new one. For example, 'Node A Name' with 'Node Name' 
for dict_a in df_listA:
    for new, old in zip(columns, columns_A): 
        dict_a[new] = dict_a.pop(old)
# replace the old key values with new one. For example, 'Node B Name' with 'Node Name' 
for dict_b in df_listB:
    for new, old in zip(columns, columns_B): 
        dict_b[new] = dict_b.pop(old)

# merge the list of dict prepared above for NodeA and NodeB. After this step complete P2P config is ready to use
df_list_p2p = df_listA + df_listB     # complete list of dict config for P2P


# initialize config list for each unique p2p host
Dict_config_p2p = dict()
for i in NodeSetP2P:
    Dict_config_p2p[i] = []

# fill config list for each 'p2p' host initialized in above step. Key is Node Name and value is config in list data type
for i in df_list_p2p:
    for j in NodeSetP2P:
        if j == i['Node Name']:
            Dict_config_p2p[j].append(i)

# initialize config list for each unique 'vrf' host
Dict_config_vrf =dict()
for i in df_list_vrf:
    Dict_config_vrf[i['Node Name']] = []

# fill config list for each vrf host initialized in above step. Key is Node Name and value is config in list data type
for i in df_list_vrf:
    Dict_config_vrf[i['Node Name']].append(i)

# initialize config list for each unique 'routing' host
Dict_config_routing = dict()
for i in NodeSetRouting:
    Dict_config_routing[i] = []

# fill config list for each 'routing' host initialized in above step. Key is Node Name and value is config in list data type
for i in df_list_routing:
    for j in NodeSetRouting:
        if j == i['Node Name']:
            Dict_config_routing[j].append(i)


# load interface template
with open(interface_jinja2_path) as f:
    interface_template = Template(f.read(), keep_trailing_newline=True)

# load vrf template
with open(vrf_jinja2_path) as f:
    vrf_template = Template(f.read(), keep_trailing_newline=True)

# load routing template
with open(routing_jinja2_path) as f:
    routing_template = Template(f.read(), keep_trailing_newline=True)


for key, list_config in Dict_config_vrf.items():
    Dict_config_vrf[key] = jinja_config_vrf(list_config, vrf_template)

for key, list_config in Dict_config_p2p.items():
    Dict_config_p2p[key] = jinja_config_int(list_config, interface_template)

for key, list_config in Dict_config_routing.items():
    Dict_config_routing[key] = jinja_config_routing(list_config, routing_template)

#for key, value in Dict_config_routing.items():
 #   print(key, value)

Dict_config_final = dict()

for Node in NodeSetFinal:
    
    try:
        vrf = Dict_config_vrf[Node]
    except:
        vrf = ''
    try:
        p2p = Dict_config_p2p[Node]
    except:
        p2p = ''
    try:
        routing = Dict_config_routing[Node]
    except:
        routing = ''
   
    Dict_config_final[Node] =  (vrf + '\n' + p2p + '\n' + routing).strip('\n')


for hostname, config in Dict_config_final.items():
    with open(os.path.join(candidate_path, '{}.txt'.format(hostname)), mode='w') as f:
        f.write(config)

#hosts = ['host1']
nr = InitNornir(config_file="config.yaml")

for H in NodeSetFinal:
    node = nr.filter(node=H) 
    #print(node.inventory.hosts.keys())
    print(H)
    config_set = Dict_config_final[H]
    config_set = config_set.strip('\n')
   
    result = node.run(task=netmiko_send_config,
                    config_commands=config_set
                    )

print_result(result)

