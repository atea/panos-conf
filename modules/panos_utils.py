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
        "force_overwrite": force_overwrite
      }
      fw = self.connect_to_fw(conn)
      if fw is None:
        continue

      conn['fw'] = fw
      self.get_objects(conn)
  
  def get_objects(self, conn):
    object_types = self.utils.config['api_parameters']['objects']
    for obj_type in object_types:
      if object_types[obj_type]['skip']:
        continue

      obj_type_info = object_types[obj_type]
      obj_type_class = self.utils.class_for_name('panos.objects', 
                                                 obj_type_info['class'])
      data = self.get_objects_from_fw(conn, obj_type_info, obj_type_class)
      file_params = {
        "data": data,
        "filename": 'objects_' + obj_type,
        "force_overwrite": conn['force_overwrite'],
        "hostname": conn['hostname']
      }
      self.utils.write_config_file(file_params)
      
  def get_objects_from_fw(self, conn, obj_type_info, obj_type_class):
    fw_objects = obj_type_class.refreshall(conn['fw'], add=False)
    
    objects = []
    for obj in fw_objects:
      obj_info = {}
      for param in obj_type_info['params']:
        obj_param = getattr(obj, param)
        if (obj_param is not None or
            not self.utils.config['settings']['skip_null_param']):
          obj_info[param] = obj_param
      objects.append(dict(obj_info))
    return sorted(objects, key=lambda k: k['name'])
