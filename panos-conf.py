#!/usr/bin/env python3

import argparse
import os
import sys
import time
from modules.panos_utils import PanosUtils
from modules.utilities import Utilities

work_dir = os.path.dirname(os.path.realpath(__file__))
utils = Utilities(work_dir=work_dir)
utils.init()

panos_utils = PanosUtils(utils=utils)

def parse_arguments():
  parser = argparse.ArgumentParser(description='PAN-OS configuration utility')  
  subparsers = parser.add_subparsers()
  
  # set/get api key
  api_key = subparsers.add_parser('apikey', help='configure apikey')
  api_key.set_defaults(func=api_key_cmd)
  api_key_group = api_key.add_mutually_exclusive_group(required=True)
  api_key_group.add_argument('--set', action='store_true',
      help="set the api key")
  api_key_group.add_argument('--get', action='store_true',
      help="get the api key")

  # generate yaml config based on current config
  get_yaml = subparsers.add_parser('getyaml', help='get yaml config')
  get_yaml.set_defaults(func=get_yaml_cmd)
  get_yaml.add_argument('--all', action='store_true', required=True,
      help="get all yaml config")
  get_yaml.add_argument('--force', action='store_true',
      help="force overwrite exisiting yaml config")

  # print help + exit if no arguments given
  if len(sys.argv) == 1:
    parser.print_help(sys.stderr)
    sys.exit(1)

  args = parser.parse_args()
  if hasattr(args, 'func'):
    args.func(args)

def api_key_cmd(args):
  if args.set:
    utils.set_api_key()
  if args.get:
    print(f"apikey: { utils.get_api_key() }")

def get_yaml_cmd(args):
  if args.all:
    panos_utils.get_yaml_conf(args.force)

if __name__ == '__main__':
  parse_arguments()

