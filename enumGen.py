#!/usr/bin/env python3

import sys
import argparse
import os
import pathlib
import logging
import json
from src import config, parser, enums, generate


class EnumGenerator:
  cfg = config.Config()

  def __init__(self):
    argParser = argparse.ArgumentParser(description='Enum to String generator for C++')

    argParser.add_argument('-d', dest='dir', metavar='DIR', help='the output directory', default='.')
    argParser.add_argument('-p', dest='project', metavar='DIR', help='the project root dir', default='.')
    argParser.add_argument('-c', '--config', help='read config from CFG', metavar='CFG', type=argparse.FileType('r'))
    argParser.add_argument('-v', '--version', action='version', version='0.0.1')
    argParser.add_argument('-V', '--verbose', action='store_true', help='verbose output')

    argParser.add_argument('-C', dest='printCfg', action='store_true', help='print config and exit')
    argParser.add_argument('-W', dest='writeCfg', help='write config to OUT', metavar='OUT', type=argparse.FileType('w'))

    subparsers = argParser.add_subparsers(title='commands')
    compileGroup = subparsers.add_parser('parse', help='compile c/c++ headers to enum lists')
    compileGroup.add_argument('input', help='input header file', type=argparse.FileType('r'))

    linkGroup = subparsers.add_parser('generate', help='link enum lists to a c++ class')
    linkGroup.add_argument('cls', help='create the C++ class <cls>')
    linkGroup.add_argument('enumFiles', nargs='+', help='JSON enum list files', type=argparse.FileType('r'))

    self.args = argParser.parse_args()

    fmt = '%(levelname)s: %(message)s'
    if self.args.verbose:
      logging.basicConfig(format=fmt, level=logging.INFO)
    else:
      logging.basicConfig(format=fmt, level=logging.WARNING)

  def run(self):
    ### Config setup
    if self.args.config:
      file = self.args.config
      logging.info('Loading config file {}'.format(os.path.basename(file.name)))
      self.cfg.readJSON(file)

    ### Check the output dir
    dir = os.path.abspath(self.args.dir)
    projectRoot = os.path.abspath(self.args.project)

    logging.info('Project root directory: {}'.format(projectRoot))
    logging.info('Output directory:       {}'.format(dir))
    if not os.path.isdir(dir):
      logging.error('Directory {} does not exist'.format(dir))
      return 1

    if not os.access(dir, os.W_OK):
      logging.error('Can not write to {}'.format(dir))
      return 1

    ### Write config
    if self.args.printCfg:
      print(self.cfg.toJSON())

    if self.args.writeCfg:
      file = self.args.writeCfg
      logging.info('Writing config file {}'.format(os.path.abspath(file.name)))
      self.cfg.writeJSON(file)

    ### Begin parsing
    if 'input' in vars(self.args):
      p = parser.Parser(self.args.input)
      e = enums.Enums()
      if (not p.parse()):
        return 1

      e.addParser(p)
      out = {
        'file': os.path.abspath(self.args.input.name),
        'enums': e.enums
      }

      fileName = os.path.splitext(os.path.basename(self.args.input.name))[0] + '.json'
      path = pathlib.Path(dir) / fileName
      fp = open(path, 'w')
      json.dump(out, fp, indent=2)
      logging.info('Wrote file {}'.format(path))


    ### Generate C++ files
    if 'cls' in vars(self.args):
      gen = generate.Generator(self.cfg.cfg, self.args.cls)
      for i in self.args.enumFiles:
        data = json.load(i)
        gen.addEnums(data['file'], data['enums'])

      gen.write(dir, projectRoot)

    return 0


if __name__ == '__main__':
  gen = EnumGenerator()
  sys.exit(gen.run())
