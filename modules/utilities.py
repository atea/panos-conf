#!/usr/bin/env python3

import base64
import importlib
import json
import keyring
import logging, logging.handlers
import os
import re
import requests
import sys
import time
import yaml
from collections import OrderedDict
from copy import deepcopy
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from datetime import datetime
from getpass import getpass

class YamlDumper(yaml.SafeDumper):
  # insert blank lines between top-level objects
  def write_line_break(self, data=None):
    super().write_line_break(data)
    if len(self.indents) == 1:
      super().write_line_break()

class Utilities:
  _config_file = 'panos-conf.yml'
  _log_file = 'panos-conf.log'
  _api_params_file = [
    'panos-api-parameters.yml',
    'panos-api-parameters.yml.dist'
  ]
  
  def __init__(self, **kwargs):
    if not kwargs == None:
      for key, value in kwargs.items():
        setattr(self, key, value)

  def init(self):
    self.start = self.datetime_now()
    self.config = self.yaml_from_file(
        self.get_filepath_config(self._config_file)
    )
    self.api_params = self.yaml_from_file(
        self.get_filepath_config(self._api_params_file)
    )
    self.log = self.create_logger()

  def get_work_dir(self):
    return self.work_dir

  def get_config_dir(self):
    return self.get_work_dir() + '/configs'

  def get_log_dir(self):
    return self.get_work_dir() + '/logs'

  def get_filepath(self, directory, files):
    if not isinstance(files, list):
      files = [files]
    
    for file in files:
      filepath = directory + '/' + file
      if os.path.exists(filepath):
        return filepath

  def get_filepath_config(self, files):
    return self.get_filepath(self.get_config_dir(), files)

  def get_filepath_log(self, files):
    return self.get_filepath(self.get_log_dir(), files)

  def create_host_folder(self, subdirs):
    conf_dir = f"{ self.get_config_dir() }/hosts/{ subdirs }"
    if not os.path.exists(conf_dir):
      os.makedirs(conf_dir)

    return conf_dir

  def yaml_from_file(self, file):
    with open(file, 'r') as f:
      return yaml.safe_load(f)

  def yaml_to_file(self, file, data, force_overwrite=False, yaml_flow=False):
    if not os.path.isfile(file) or force_overwrite:
      with open(file, 'w') as f:
        return yaml.dump(data, f, Dumper=YamlDumper, sort_keys=False,
                         default_flow_style=yaml_flow, explicit_start=True,
                         width=32768, encoding="utf8")

  def json_from_file(self, file):
    with open(file, 'r') as f:
      return json.load(f)

  def json_from_string(self, data):
    return json.loads(data)

  def formatted_json_string(self, json_content):
    return json.dumps(json_content, ensure_ascii=False, sort_keys=True,
                      indent=2, separators=(',', ': '), default=str)

  def format_object(self, obj, params):
    return self.formatted_json_string(self.recurse_object(obj, params))

  def recurse_object(self, obj, params):
    # params = {
    #   "class_type": 'panos',
    #   "ignored_attributes": [ 'parent' ]
    # }
    obj_dict = deepcopy({})
    for attribute in dir(obj):
      if (not attribute.startswith('_')
          and not callable(getattr(obj, attribute))
          and not attribute == 'metadata'):
        attr_value = getattr(obj, attribute)
        if attribute in params['ignored_attributes']:
          # dont do more lookups on attributes we should ignore
          obj_dict.update({ attribute: attr_value })
        else:
          if isinstance(attr_value, list):
            obj_list = deepcopy([])
            for item in attr_value:
              if params['class_type'] in str(type(item)):
                obj_list.append({
                  str(type(item)): self.recurse_object(item, params)
                })
              else:
                obj_list.append(item)
            obj_dict.update({ attribute: obj_list })
          else:
            if params['class_type'] in str(type(attr_value)):
              obj_dict.update({
                str(type(attribute)): self.recurse_object(attr_value, params)
              })
            else:
              obj_dict.update({ attribute: attr_value })
    return obj_dict
    
  def create_logger(self):
    logger = logging.getLogger('panos-conf')
    logger.setLevel(logging.DEBUG)
    formatter = self.create_logger_formatter()
    file_handler = self.create_logger_file_handler(formatter)
    stdout_handler = self.create_logger_stdout_handler(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stdout_handler)

    return logger

  def create_logger_formatter(self):
    log_format = '%(asctime)s | '
    log_format += '%(process)5d | '
    log_format += '%(levelname)-8.8s | '
    log_format += 'L:%(lineno)4d | '
    log_format += '%(message)s'
    return logging.Formatter(log_format)
    
  def create_logger_file_handler(self, formatter, level=logging.DEBUG):
    file_handler = logging.handlers.TimedRotatingFileHandler(
      filename = self.get_filepath_log(self._log_file),
      when = 'midnight', interval=1, backupCount = 0)
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    return file_handler
    
  def create_logger_stdout_handler(self, formatter, level=logging.INFO):
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(level)
    stdout_handler.setFormatter(formatter)
    return stdout_handler

  def ordered_dict(self, items):
    array = []
    for i in items:
      od = OrderedDict()
      for key, value in i.items():
        od[key] = value
      array.append(od)
    return array

  def string_to_int(self, string):
    try:
      i = int(''.join(filter(str.isdigit, string)))
    except:
      i = None
    
    return i

  def class_for_name(self, module_name, class_name):
    # load the module, will raise ImportError if module cannot be loaded
    m = importlib.import_module(module_name)
    # get the class, will raise AttributeError if class cannot be found
    c = getattr(m, class_name)
    return c

  def check_regex_match(self, regex, string):
    try:
      m = re.match(regex, string, re.IGNORECASE)
    except Exception as e:
      m = None
      self.log.warning(f"re.match failed for string '{string}': {e}")
    return m

  def datetime_now(self):
    return datetime.now()

  def time_diff(self, then, interval='default'):
    t_diff = self.datetime_now() - then
    total_sec = t_diff.total_seconds() 

    def years():
      return divmod(total_sec, 31536000)

    def days(s=None):
      return divmod(s if s != None else total_sec, 86400)

    def hours(s=None):
      return divmod(s if s != None else total_sec, 3600)

    def minutes(s=None):
      return divmod(s if s != None else total_sec, 60)

    def seconds(s=None):
      if s != None:
        return divmod(s, 1)
      return total_sec

    def total_duration():
        y = years()
        d = days(y[1])
        h = hours(d[1])
        m = minutes(h[1])
        s = seconds(m[1])

        msg = f"{int(y[0])} year(s), "
        msg += f"{int(d[0])} day(s), "
        msg += f"{int(h[0])} hour(s), "
        msg += f"{int(m[0])} minute(s), "
        msg += f"{int(s[0])} second(s)"
        return msg

    return {
        'years': int(years()[0]),
        'days': int(days()[0]),
        'hours': int(hours()[0]),
        'minutes': int(minutes()[0]),
        'seconds': int(seconds()),
        'default': total_duration()
    }[interval]

  def write_config_file(self):
    config_file = self.get_filepath_config(self._config_file)
    self.yaml_to_file(config_file, self.config, force_overwrite=True)

  def write_host_config_file(self, data, file_params, yaml_flow=False):
    conf_dir = self.create_host_folder(file_params['conf_dir'])
    conf_file = conf_dir + '/' + file_params['filename'] + '.yml'
    self.yaml_to_file(conf_file, data,
                      file_params['force_overwrite'], yaml_flow)

  def return_sorted_list(self, unsorted_list, sort_param):
    if sort_param is None:
      return unsorted_list
    else:
      return sorted(unsorted_list, key=lambda k: k[sort_param])

  def get_hostname_vsys(self, hostname):
    vsys_file = f"{ self.get_config_dir() }/hosts/{ hostname }"
    vsys_file += f"/vsys1/device_vsys.yml"
    
    if os.path.exists(vsys_file):
      vsys_config = self.yaml_from_file(vsys_file)
      vsys_list = []
      for vsys in vsys_config:
        vsys_list.append(vsys['name'])
      return vsys_list
    else:
      return ['vsys1']

  def ask_for_credentials(self, user_description, password_description):
    username = input(f"{ user_description }: ")
    password = self.get_password(password_description)

    return username, password
  
  def get_password(self, description="password", verify=False):
    if verify:
      while True:
        password_one = getpass(f"Enter { description }: ")
        password_two = getpass(f"Verify { description }: ")
        
        if password_one == password_two:
          return password_one
        else:
          print("Not matching. Please try again.")
    else:
      password = getpass(f"Enter { description }: ")
      return password

  def set_or_get_salt(self):
    salt = self.config['settings'].get('crypto_salt', None)
    if salt is None:
      self.config['settings']['crypto_salt'] = os.urandom(16)
      self.write_config_file()
      return self.config['settings']['crypto_salt']
    else:
      return salt

  def set_or_get_crypto(self):
    crypto = getattr(self, 'crypto', None)
    if crypto is None:
      password = self.get_crypto_password()
      salt = self.set_or_get_salt()
      kdf = PBKDF2HMAC(
          algorithm = hashes.SHA256(),
          length = 32,
          salt = salt,
          iterations = 100000,
      )
      key = base64.urlsafe_b64encode(kdf.derive(password))
      self.crypto = Fernet(key)
      return self.crypto
    else:
      return crypto

  def get_crypto_password(self):
    if self.keyring_enabled():
      try:
        password = keyring.get_password(
          self.config['settings']['keyring']['service'],
          self.config['settings']['keyring']['username']
        )
      except:
        return self.set_keyring_password().encode()
      else:
        if password is None:
          return self.set_keyring_password().encode()
        else:
          return password.encode()
    else:
      password = self.get_password(description="encryption password")
      return password.encode()

  def set_keyring_password(self):
    password = self.get_password(verify=True)
    keyring.set_password(
      self.config['settings']['keyring']['service'],
      self.config['settings']['keyring']['username'],
      password
    )
    return password

  def keyring_enabled(self):
    return self.config.get(
        'settings', False).get(
        'keyring', False).get(
        'enabled', False)

  def get_api_key_config(self, args):
    if args.get('api_key', False):
      return args['api_key']
    else:
      return self.get_api_key_keyring()

  def encrypt(self, data):
    crypto = self.set_or_get_crypto()
    return crypto.encrypt(data.encode())

  def decrypt(self, data):
    crypto = self.set_or_get_crypto()
    return crypto.decrypt(data).decode()

  def url_post(self, url, data):
    verify = self.config.get('settings', True).get('ssl_verify', True)
    try:
      response = requests.post(url, data=data, verify=verify)
    except Exception as e:
      print(e)
      return None
    else:
      return response
    