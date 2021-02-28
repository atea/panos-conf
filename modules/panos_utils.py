#!/usr/bin/env python3

import panos
import panos.firewall
import panos.objects
import panos.policies

class PanosUtils:
  def __init__(self, **kwargs):
    if not kwargs == None:
      for key, value in kwargs.items():
        setattr(self, key, value)
    
  def connect_to_fw(self, hostname, args=None):
    try:
      fw = panos.firewall.Firewall(
        hostname = hostname,
        api_key = self.utils.get_api_key(args)
      )
    except:
      self.utils.log.error("Could not connect to firewall.")
      return None
    else:
      return fw

  def get_yaml_conf(self, force_overwrite):
    fw_configs = self.get_configs_from_all_firewalls()

    for hostname in fw_configs:
      for config_type in fw_configs[hostname]['config']:
        for config_child in fw_configs[hostname]['config'][config_type]:
          file_params = {
            "filename": config_type + '_' + config_child,
            "force_overwrite": force_overwrite,
            "hostname": hostname
          }
          data = fw_configs[hostname]['config'][config_type][config_child]
          self.utils.write_config_file(data, file_params)

  def get_configs_from_all_firewalls(self, return_object=False):
    fw_configs = {}
    for hostname, args in self.utils.config['panos']['hosts'].items():
      conn = {
        "args": args,
        "add": False,
        "return_object": return_object
      }
      fw = self.connect_to_fw(hostname, conn['args'])
      if fw is None:
        continue
      conn['fw'] = fw
      conn['rulebase'] = panos.policies.Rulebase()
      conn['fw'].add(conn['rulebase'])

      fw_config = self.get_config_types_from_firewall(conn)
      fw_configs[hostname] = {}
      fw_configs[hostname]['conn'] = conn
      fw_configs[hostname]['config'] = fw_config
    return fw_configs

  def get_config_types_from_firewall(self, conn):
    config_types = self.utils.api_params
    fw_config = {}
    for config_type in config_types:
      fw_config[config_type] = self.get_config_children_from_firewall(
          conn, config_types[config_type])
    return fw_config
  
  def get_config_children_from_firewall(self, conn, config_type):
    fw_config = {}
    for config_child in config_type:
      if config_type[config_child]['skip']:
        continue

      config_info = config_type[config_child]
      config_class = self.utils.class_for_name(config_info['module'],
                                               config_info['class'])
      data = self.get_config_class_from_firewall(conn, config_info, 
                                                 config_class)
      fw_config[config_child] = data
    return fw_config
      
  def get_config_class_from_firewall(self, conn, config_info, config_class):
    class_config = config_class.refreshall(conn[config_info['parent']],
                                           conn['add'])
    
    if conn['return_object']:
      return class_config
    else:
      data = []
      for obj in class_config:
        obj_info = {}
        for param in config_info['params']:
          obj_param = getattr(obj, param)
          if (obj_param is not None or
              not self.utils.config['settings']['skip_null_param']):
            obj_info[param] = obj_param
        data.append(dict(obj_info))
      
      if config_info['sort_param'] is None:
        # we don't sort these, as order matters
        return data
      else:
        return sorted(data, key=lambda k: k[config_info['sort_param']])
