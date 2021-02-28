#!/usr/bin/env python3

import importlib
import json
import keyring
import logging, logging.handlers
import os
import re
import sys
import time
import yaml
from collections import OrderedDict
from datetime import datetime
from getpass import getpass

class YamlDumper(yaml.SafeDumper):
  # insert blank lines between top-level objects
  def write_line_break(self, data=None):
    super().write_line_break(data)
    if len(self.indents) == 1:
      super().write_line_break()

class Utilities:
  def __init__(self, **kwargs):
    if not kwargs == None:
      for key, value in kwargs.items():
        setattr(self, key, value)

  def init(self):
    self.start = self.datetime_now()
    self.config = self.yaml_from_file(
        self.get_filepath('/configs/panos-conf.yml'))
    self.log = self.create_logger()

  def get_work_dir(self):
    return self.work_dir

  def get_config_dir(self):
    return self.get_work_dir() + '/configs'

  def get_filepath(self, file):
    return self.get_work_dir() + file
  
  def create_config_folder(self, hostname):
    conf_dir = self.get_config_dir() + '/hosts/' + hostname
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

  def format_object(self, obj):
    dictionary = {}

    for attribute in dir(obj):
      if (not attribute.startswith('_')
          and not callable(getattr(obj, attribute))
          and not attribute == 'metadata'):
        dictionary[attribute] = getattr(obj, attribute)

    return self.formatted_json_string(dictionary)

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
      filename = self.get_filepath('/logs/panos-conf.log'),
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

  def set_api_key(self):
    api_key_one = getpass("Enter API key: ")
    api_key_two = getpass("Enter API key again: ")
    if api_key_one == api_key_two:
      keyring.set_password(
        self.config['settings']['keyring']['service'],
        self.config['settings']['keyring']['username'],
        api_key_one
      )
      self.log.info("API key set.")
    else:
      self.log.error("API keys does not match.")

  def get_api_key(self, args=None):
    if args is None:
      return self.get_api_key_keyring()
    else:
      return self.get_api_key_config(args)

  def get_api_key_keyring(self):
    try:
      api_key = keyring.get_password(
        self.config['settings']['keyring']['service'],
        self.config['settings']['keyring']['username']
      )
    except:
      self.log.error("API key not set.")
      sys.exit(1)
    else:
      return api_key

  def get_api_key_config(self, args):
    if args.get('api_key', False):
      return args['api_key']
    else:
      return self.get_api_key_keyring()

  def write_config_file(self, file_params, yaml_flow=False):
    conf_dir = self.create_config_folder(file_params['hostname'])
    conf_file = conf_dir + '/' + file_params['filename'] + '.yml'
    self.yaml_to_file(conf_file, file_params['data'], 
                      file_params['force_overwrite'], yaml_flow)
