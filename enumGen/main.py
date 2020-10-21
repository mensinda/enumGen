#!/usr/bin/env python3

import sys
import argparse
import os
import pathlib
import logging
import json
from pathlib import Path
from . import config, parser, enums, generate


class EnumGenerator:
  cfg = config.Config()

  def __init__(self) -> None:
    argParser = argparse.ArgumentParser(description='Enum to String generator for C++')

    argParser.add_argument('-c', '--config', help='read config from CFG', metavar='CFG', type=Path)
    argParser.add_argument('-v', '--version', action='version', version='1.0.0')
    argParser.add_argument('-V', '--verbose', action='store_true', help='verbose output')

    argParser.add_argument('-C', dest='printCfg', action='store_true', help='print config and exit')
    argParser.add_argument('-W', dest='writeCfg', help='write config to OUT', metavar='OUT', type=Path)

    subparsers = argParser.add_subparsers(title='commands')
    compileGroup = subparsers.add_parser('parse', help='compile c/c++ headers to enum lists')
    compileGroup.add_argument('input', help='input header file', type=Path)
    compileGroup.add_argument('output', help='"compiled" output JSON file', type=Path)

    linkGroup = subparsers.add_parser('generate', help='link enum lists to a c++ class')
    linkGroup.add_argument('cls', help='create the C++ class <cls>')
    linkGroup.add_argument('hpp', help='The output HPP file', type=Path)
    linkGroup.add_argument('cpp', help='The output CPP file', type=Path)
    linkGroup.add_argument('enumFiles', nargs='+', help='JSON enum list files', type=Path)

    self.args: argparse.Namespace = argParser.parse_args()

    fmt = '%(levelname)s: %(message)s'
    if self.args.verbose:
      logging.basicConfig(format=fmt, level=logging.INFO)
    else:
      logging.basicConfig(format=fmt, level=logging.WARNING)

  def run(self) -> int:
    ### Config setup
    if self.args.config:
      cfgfile: Path = self.args.config
      logging.info(f'Loading config file {cfgfile.name}')
      self.cfg.readJSON(cfgfile)

    ### Write config
    if self.args.printCfg:
      print(self.cfg.toJSON())
      return 0

    if self.args.writeCfg:
      cfgfile = self.args.writeCfg
      cfgfile = cfgfile.resolve()
      logging.info(f'Writing config file {cfgfile}')
      self.cfg.writeJSON(cfgfile)
      return 0

    ### Begin parsing
    if 'input' in vars(self.args):
      assert isinstance(self.args.input, Path)
      assert isinstance(self.args.output, Path)
      in_file:  Path = self.args.input
      out_file: Path = self.args.output
      in_file  = in_file.resolve()
      out_file = out_file.resolve()
      p = parser.Parser(in_file)
      e = enums.Enums()
      p.parse()
      e.parseScope(p)

      out = {
        'file': in_file.as_posix(),
        'enums': e.enums
      }

      out_file.write_text(json.dumps(out, indent=2))
      logging.info(f'Wrote file {out_file}')

    ### Generate C++ files
    if 'cls' in vars(self.args):
      assert isinstance(self.args.hpp, Path)
      assert isinstance(self.args.cpp, Path)
      gen = generate.Generator(self.args.hpp, self.args.cpp, self.cfg, self.args.cls)
      for i in self.args.enumFiles:
        data = json.loads(i.read_text())

        if isinstance(data, dict) and 'file' in data and 'enums' in data:
          assert isinstance(data['file'], str)
          assert isinstance(data['enums'], list)
          gen.addEnums(data['file'], data['enums'])

      gen.write()

    return 0
