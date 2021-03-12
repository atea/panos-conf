#!/usr/bin/env python3

import argparse
import os
import sys
from modules.panos_utils import PanosUtils
from modules.utilities import Utilities

work_dir = os.path.dirname(os.path.realpath(__file__))
utils = Utilities(work_dir=work_dir)
utils.init()

panos_utils = PanosUtils(utils=utils)

def parse_arguments():
  parser = argparse.ArgumentParser(description='PAN-OS configuration utility')  
  subparsers = parser.add_subparsers()
  
  # set/get api keys
  api_key = subparsers.add_parser('apikey', help='configure apikey')
  api_key.set_defaults(func=api_key_cmd)
  api_key.add_argument('--set', action='store_true', required=True,
      help="set the api key")
  api_key_group = api_key.add_mutually_exclusive_group()
  api_key_group.add_argument('--force', action='store_true',
      help="force set the api key")
  api_key_group.add_argument('--verify', action='store_true',
      help="verify the api keys, and set were needed")
  
  # set or change password
  password = subparsers.add_parser('password', help='configure password')
  password.set_defaults(func=password_cmd)
  password_group = password.add_mutually_exclusive_group(required=True)
  password_group.add_argument('--set', action='store_true',
      help="set the keyring password")
  password_group.add_argument('--change', action='store_true',
      help="change old password, regardless if keyring or not")

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
    panos_utils.set_api_keys(force=args.force, verify=args.verify)

def password_cmd(args):
  if args.set:
    password = utils.get_keyring_password()
    if password is None:
      utils.set_keyring_password()
    else:
      print("Password already set. Please use --change parameter.")
  if args.change:
    utils.change_password()

def get_yaml_cmd(args):
  if args.all:
    panos_utils.get_yaml_conf(args.force)

if __name__ == '__main__':
  parse_arguments()

