#!/usr/bin/env python3

import sys
import argparse
import os
import logging
import json
from src import config, parser, enums


class EnumGenerator:
  cfg = config.Config()

  def __init__(self):
    argParser = argparse.ArgumentParser(description='Enum to String generator for C++')

    argParser.add_argument('-p', '--print', action='store_true', help='print config and exit')
    argParser.add_argument('-w', '--write', nargs=1, help='write config to OUT and exit', metavar='OUT',
                           type=argparse.FileType('w'))
    argParser.add_argument('-c', '--config', nargs=1, help='read config from CFG', metavar='CFG',
                           type=argparse.FileType('r'))
    argParser.add_argument('-v', '--version', action='version', version='0.0.1')
    argParser.add_argument('-V', '--verbose', action='store_true', help='verbose output')
    argParser.add_argument('input', nargs='*', help='input header files', type=argparse.FileType('r'))

    self.args = argParser.parse_args()

    fmt = '%(levelname)s: %(message)s'
    if (self.args.verbose):
      logging.basicConfig(format=fmt, level=logging.INFO)
    else:
      logging.basicConfig(format=fmt, level=logging.WARNING)

  def run(self):
    # Config setup
    if (self.args.config):
      file = self.args.config[0]
      logging.info('Loading config file {}'.format(os.path.basename(file.name)))
      self.cfg.readJSON(file)

    if (self.args.print):
      print(self.cfg.toJSON())

    if (self.args.write):
      file = self.args.write[0]
      logging.info('Writing file {}'.format(os.path.basename(file.name)))
      self.cfg.writeJSON(file)
      return 0

    # Begin parsing
    parsedEnums = enums.Enums()

    logging.info('Begin Parsing files')
    for i in self.args.input:
      # Check for files to skip
      skip = True
      for j in self.cfg.cfg['extract']['inputFileTypes']:
        if(i.name.endswith('.{}'.format(j))):
          skip = False
          break

      if(skip):
        logging.info('Skipping file {}'.format(i.name))
        continue

      p = parser.Parser(i)
      if (not p.parse()):
        return 1

      parsedEnums.addParser(p)

    return 0


if __name__ == '__main__':
  gen = EnumGenerator()
  sys.exit(gen.run())
