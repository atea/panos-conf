#!/usr/bin/env python3

import panos
import panos.device
import panos.firewall
import panos.objects
import panos.policies

class PanosUtils:
  def __init__(self, **kwargs):
    if not kwargs == None:
      for key, value in kwargs.items():
        setattr(self, key, value)
    
  def connect_to_fw(self, hostname, vsys=None, args=None):
    try:
      fw = panos.firewall.Firewall(
        hostname = hostname,
        api_key = self.utils.get_api_key(args),
        vsys = vsys
      )
    except:
      self.utils.log.error("Could not connect to firewall.")
      return None
    else:
      return fw

  def get_yaml_conf(self, force_overwrite):
    fw_configs = self.get_configs_from_all_firewalls()

    for hostname in fw_configs:
      for vsys in fw_configs[hostname]:
        modules = fw_configs[hostname][vsys]['config_modules']
        for module in modules:
          for object_type in modules[module]:
            file_params = {
              "conf_dir": f"{ hostname }/{ vsys }",
              "filename": f"/{ module }_{ object_type }",
              "force_overwrite": force_overwrite
            }
            data = modules[module][object_type]
            if len(data) > 0:
              # don't write blank configs
              self.utils.write_config_file(data, file_params)

  def get_configs_from_all_firewalls(self, return_object=False):
    fw_configs = {}
    for host in self.utils.config['hosts']:
      vsys_list = self.utils.get_hostname_vsys(host['hostname'])
      for vsys in vsys_list:
        conn = {
          "hostname": host['hostname'],
          "host_args": host,
          "add": False,
          "return_object": return_object
        }
        if (len(vsys_list) < 2) and (vsys == 'vsys1'):
          # on device that only has one vsys
          conn_vsys = None
        else:
          conn_vsys = vsys
        
        vsys_conn = self.connect_to_fw(host['hostname'], conn_vsys, 
                                       conn['host_args'])
        if vsys_conn is None:
          continue
        conn['vsys'] = vsys_conn
        conn['rulebase'] = panos.policies.Rulebase()
        conn['vsys'].add(conn['rulebase'])

        fw_config = self.get_modules_from_firewall(conn)
        fw_configs[host['hostname']] = {}
        fw_configs[host['hostname']][vsys] = {}
        fw_configs[host['hostname']][vsys]['conn'] = conn
        fw_configs[host['hostname']][vsys]['config_modules'] = fw_config
    return fw_configs

  def get_modules_from_firewall(self, conn):
    modules = self.utils.api_params['modules']
    modules_config = {}
    for module in modules:
      modules_config[module] = self.get_objects_from_firewall(conn, 
                                                              modules[module])
    return modules_config
  
  def get_objects_from_firewall(self, conn, module):
    objects_config = {}
    for object_type in module:
      if module[object_type]['skip']:
        continue

      object_info = module[object_type]
      object_class = self.utils.class_for_name(object_info['module'],
                                               object_info['class'])
      object_data = self.get_object_from_firewall(conn, object_info, 
                                                  object_class)
      objects_config[object_type] = object_data
    return objects_config
      
  def get_object_from_firewall(self, conn, object_info, object_class):
    object_data = object_class.refreshall(conn[object_info['parent']],
                                          conn['add'])
    
    if conn['return_object']:
      return object_data
    else:
      # we convert to dictionary
      return self.parse_object_from_firewall(object_data, object_info)
      
  def parse_object_from_firewall(self, object_data, object_info):
    object_list = []
    for obj in object_data:
      obj_info = self.get_object_attributes(obj, object_info['params'])
      if self.object_has_children(obj, object_info):
        obj_info['children'] = self.get_object_children(obj, object_info)
      object_list.append(dict(obj_info))

    return self.utils.return_sorted_list(object_list, 
                                         object_info['sort_param'])

  def get_object_attributes(self, obj, params):
    obj_info = {}
    for param in params:
      param_value = getattr(obj, param, None)
      if (param_value is not None or
          not self.utils.config['settings']['skip_null_param']):
        obj_info[param] = param_value
    return obj_info

  def object_has_children(self, obj, object_info):
    children = getattr(obj, 'children', False)
    if children and object_info.get('children', False):
      if len(children) > 0:
        return True
    return False

  def get_object_children(self, obj, object_info):
    children_dict = {}
    children = getattr(obj, 'children', [])
    for child_obj in children:
      for child_conf in object_info['children']:
        child_name = child_conf['name']
        child_conf_info = self.utils.api_params['children'][child_name]
        child_conf_class = self.utils.class_for_name(
          child_conf_info['module'],
          child_conf_info['class']
        )

        if isinstance(child_obj, child_conf_class):
          child_dict = self.get_object_attributes(
              child_obj, child_conf_info['params'])

          if self.object_has_children(child_obj, child_conf):
            child_dict['children'] = self.get_object_children(child_obj,
                                                              child_conf)
          
          if child_conf['name'] not in children_dict:
            children_dict[child_conf['name']] = []
          children_dict[child_conf['name']].append(child_dict)
          children_dict[child_conf['name']] = self.utils.return_sorted_list(
              children_dict[child_conf['name']], child_conf_info['sort_param'])

    return children_dict
