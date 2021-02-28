#!/usr/bin/env python3

import panos
import panos.firewall
import panos.objects

class PanosUtils:
  def __init__(self, **kwargs):
    if not kwargs == None:
      for key, value in kwargs.items():
        setattr(self, key, value)
    
  def connect_to_fw(self, args):
    try:
      fw = panos.firewall.Firewall(
        hostname = args['hostname'],
        api_key = self.utils.get_api_key(args['args'])
      )
    except:
      self.utils.log.error("Could not connect to firewall.")
      return None
    else:
      return fw

  def get_yaml_conf(self, force_overwrite):
    for hostname, args in self.utils.config['panos']['hosts'].items():
      conn = {
        "hostname": hostname,
        "args": args,
        "add": False
      }
      fw = self.connect_to_fw(conn)
      if fw is None:
        continue
      conn['fw'] = fw

      fw_config = self.get_fw_config_all(conn)

      for config_type in fw_config:
        for subconfig in fw_config[config_type]:
          file_params = {
            "filename": config_type + '_' + subconfig,
            "force_overwrite": force_overwrite,
            "hostname": hostname
          }
          self.utils.write_config_file(fw_config[config_type][subconfig],
                                       file_params)

  def get_fw_config_all(self, conn):
    config_types = self.utils.api_params
    fw_config = {}
    for config_type in config_types:
      fw_config[config_type] = self.get_fw_config(conn,
                                                  config_types[config_type])
    return fw_config
  
  def get_fw_config(self, conn, configs):
    fw_config = {}
    for config_type in configs:
      if configs[config_type]['skip']:
        continue

      config_info = configs[config_type]
      config_class = self.utils.class_for_name(config_info['module'],
                                               config_info['class'])
      data = self.get_config_from_fw(conn, config_info, config_class)
      fw_config[config_type] = data
    return fw_config
      
  def get_config_from_fw(self, conn, config_info, config_class):
    class_config = config_class.refreshall(conn['fw'], conn['add'])
    
    data = []
    for obj in class_config:
      obj_info = {}
      for param in config_info['params']:
        obj_param = getattr(obj, param)
        if (obj_param is not None or
            not self.utils.config['settings']['skip_null_param']):
          obj_info[param] = obj_param
      data.append(dict(obj_info))
    return sorted(data, key=lambda k: k[config_info['sort_param']])
