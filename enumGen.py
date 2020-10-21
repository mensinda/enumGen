#!/usr/bin/env python3

from enumGen import main
import sys

if __name__ == '__main__':
  gen = main.EnumGenerator()
  sys.exit(gen.run())
