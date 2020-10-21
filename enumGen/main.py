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

    argParser.add_argument('-d', dest='dir', metavar='DIR', help='the output directory', default='.', type=Path)
    argParser.add_argument('-p', dest='project', metavar='DIR', help='the project root dir', default='.', type=Path)
    argParser.add_argument('-c', '--config', help='read config from CFG', metavar='CFG', type=Path)
    argParser.add_argument('-v', '--version', action='version', version='0.0.1')
    argParser.add_argument('-V', '--verbose', action='store_true', help='verbose output')

    argParser.add_argument('-C', dest='printCfg', action='store_true', help='print config and exit')
    argParser.add_argument('-W', dest='writeCfg', help='write config to OUT', metavar='OUT', type=Path)

    subparsers = argParser.add_subparsers(title='commands')
    compileGroup = subparsers.add_parser('parse', help='compile c/c++ headers to enum lists')
    compileGroup.add_argument('input', help='input header file', type=Path)

    linkGroup = subparsers.add_parser('generate', help='link enum lists to a c++ class')
    linkGroup.add_argument('cls', help='create the C++ class <cls>')
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

    ### Check the output dir
    outDir:      Path = self.args.dir
    projectRoot: Path = self.args.project
    outDir      = outDir.resolve()
    projectRoot = projectRoot.resolve()

    logging.info(f'Project root directory: {projectRoot}')
    logging.info(f'Output directory:       {outDir}')
    if not outDir.is_dir():
      logging.error(f'Directory {outDir} does not exist')
      return 1

    ### Write config
    if self.args.printCfg:
      print(self.cfg.toJSON())

    if self.args.writeCfg:
      cfgfile = self.args.writeCfg
      cfgfile = cfgfile.resolve()
      logging.info(f'Writing config file {cfgfile}')
      self.cfg.writeJSON(cfgfile)

    ### Begin parsing
    if 'input' in vars(self.args):
      assert isinstance(self.args.input, Path)
      in_file: Path = self.args.input
      in_file = in_file.resolve()
      p = parser.Parser(in_file)
      e = enums.Enums()
      p.parse()
      e.parseScope(p)

      out = {
        'file': in_file.as_posix(),
        'enums': e.enums
      }

      path = outDir / f'{in_file.stem}.json'
      path.write_text(json.dumps(out, indent=2))
      logging.info(f'Wrote file {path}')

    ### Generate C++ files
    if 'cls' in vars(self.args):
      gen = generate.Generator(self.cfg, self.args.cls)
      for i in self.args.enumFiles:
        data = json.loads(i.read_text())

        if isinstance(data, dict) and 'file' in data and 'enums' in data:
          assert isinstance(data['file'], str)
          assert isinstance(data['enums'], list)
          gen.addEnums(data['file'], data['enums'])

      gen.write(outDir, projectRoot)

    return 0
