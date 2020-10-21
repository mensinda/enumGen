import re
import logging
import os
import textwrap
from pathlib import Path
import typing as T

if T.TYPE_CHECKING:
  from .config import Config
  from .enums  import EnumDict

  class PocEnumDict(EnumDict):
    maxLen: int
    id:     str
    fname:  str

class Generator:
  def __init__(self, hppFile: Path, cppFile: Path, cfg: 'Config', name: str) -> None:
    self.cfg      = cfg
    self.name     = name
    self.maxIdLen = 0
    self.hppFile  = hppFile.resolve()
    self.cppFile  = cppFile.resolve()
    self.incList:   T.List[str]           = []
    self.enums_raw: T.List['EnumDict']    = []
    self.enums:     T.List['PocEnumDict'] = []

  def addEnums(self, incFile: str, enums: T.List['EnumDict']) -> None:
    if len(enums) > 0:
      self.incList.append(incFile)
      self.enums_raw += enums

  def indent(self, level: int) -> str:
    if self.cfg.indent >= 0:
      return ' ' * (self.cfg.indent * level)
    else:
      return ''

  def genHpp(self) -> str:
    raw_str = textwrap.dedent(f'''\
      /*!
       * \\file {self.hppFile.name}
       * \\warning This is an automatically generated file!
       */

      // clang-format off

      #pragma once

      #include <string>
      #include <vector>
    ''')

    for inc in self.incList:
      raw_str += f'#include "{inc}"\n'

    ### Open namespace
    if self.cfg.namespace:
      raw_str += f'\nnamespace {self.cfg.namespace} {{\n'

    ### Begin class / namespace
    if self.cfg.useNamespace:
      raw_str += f'\nnamespace {self.name} {{\n\n'
      baseLevel = 1
      static = ''
    else:
      baseLevel = 2
      static = 'static '
      raw_str += f'\nclass {self.name} final {{\n'
      raw_str += self.indent(1) + 'public:\n'
      raw_str += self.indent(2) + f'{self.name}() = delete;\n\n'

    # To string declarations
    fName = self.cfg.funcName
    for i in self.enums:
      pad = ' ' * (self.maxIdLen - len(i['id']))
      raw_str += self.indent(baseLevel) + f'{static}std::string {fName}( {i["id"]}{pad} _var ) noexcept;\n'

    if self.cfg.enableBitfields:
      raw_str += '\n\n' + self.indent(baseLevel)
      raw_str += f'{static}std::string stringListToString(std::vector<std::string> _list) noexcept;\n\n'

      btype = self.cfg.bitfieldType

      for i in self.enums:
        pad = ' ' * (self.maxIdLen - len(i['fname']))
        bitName = f'{i["fname"]}_{fName} {pad}'
        raw_str += self.indent(baseLevel) + f'{static}std::string {bitName}( {btype} _var ) noexcept;\n'

      raw_str += '\n\n'

      for i in self.enums:
        pad = ' ' * (self.maxIdLen - len(i['fname']))
        bitName = f'{i["fname"]}_{fName}_Raw {pad}'
        raw_str += self.indent(baseLevel) + f'{static}std::vector<std::string> {bitName}( {btype} _var ) noexcept;\n'

    ### End class namespace
    if self.cfg.useNamespace:
      raw_str += f'\n}} // namespace {self.name}\n\n'
    else:
      raw_str += f'\n}}; // class {self.name}\n\n'

    ### Close namespace
    if self.cfg.namespace:
      raw_str += f'}} // namespace {self.cfg.namespace} \n\n'
    return raw_str + '// clang-format on\n\n'

  def genCpp(self) -> str:
    raw_str = textwrap.dedent(f'''\
      /*!
       * \\file {self.cppFile.name}
       * \\warning This is an automatically generated file!
       */

      // clang-format off

      #include "{self.hppFile.name}"

      #define CHECK_BIT(v, x) (v & static_cast<{self.cfg.bitfieldType}>(x)) == static_cast<{self.cfg.bitfieldType}>(x)

      ''')

    if self.cfg.namespace:
      raw_str += f'using namespace {self.cfg.namespace};\n\n'

    fName = self.cfg.funcName

    # Generate switch case
    for i in self.enums:
      raw_str += textwrap.dedent(f'''

        /*!
         * \\brief Converts the enum {i['id']} to a std::string
         * \\param _var The enum value to convert
         * \\returns _var converted to a std::string
         */
        std::string {self.name}::{fName}( {i['id']} _var ) noexcept {{
        {self.indent(1)}switch( _var ) {{
        ''')

      scope = i['scope']
      if i['isScoped']:
        scope += '::' + i['name']

      for j in i['entries'].keys():
        if j in i['blackList']:
          continue

        enum_id = scope + '::' + j
        enum_id = re.sub('^::', '', enum_id)
        pad = ' ' * (i['maxLen'] - len(j))
        raw_str += self.indent(2) + 'case {0}:{2} return "{1}"{2} ;\n'.format(enum_id, j, pad)

      raw_str += self.indent(2) + f'default: return "{self.cfg.defaultValue}";\n'
      raw_str += self.indent(1) + '}\n}'

    # Generate common function
    if self.cfg.enableBitfields:
      raw_str += textwrap.dedent(f'''

        /*!
        * \\brief Converts the list of strings to one string concatinated with '{self.cfg.bitfieldConcat}'
        * \\param _list The list of strings to convert
        * \\returns The converted _list
        */
        std::string {self.name}::stringListToString(std::vector<std::string> _list) noexcept {{
          std::string lResult;
          for( size_t i = 0; i < _list.size(); ++i ) {{
            if( i != 0 ) {{
              lResult += "{self.cfg.bitfieldConcat}";
            }}

            lResult += _list[i];
          }}
          return lResult;
        }}

        ''')

      for i in self.enums:
        raw_str += textwrap.dedent(f'''

          /*!
           * \\brief Converts the enum bitfield {i['id']} to a std::string
           * \\param _var The bitfield value to convert
           * \\returns The _var bitfield converted to a std::string
           */
          std::string {self.name}::{i['fname']}_{fName}( {self.cfg.bitfieldType} _var ) noexcept {{
          {self.indent(1)}return stringListToString( {i['fname']}_{fName}_Raw( _var ) );
          }}
          ''')

      for i in self.enums:
        raw_str += textwrap.dedent(f'''

          /*!
           * \\brief Converts the enum bitfield {i['id']} to std::vector of std::string
           * \\param _var The bitfield value to convert
           * \\returns _var converted to a std::vector of std::string
           */
          std::vector<std::string> {self.name}::{i['fname']}_{fName}_Raw( {self.cfg.bitfieldType} _var ) noexcept {{
          {self.indent(1)}std::vector<std::string> list;
          ''')

        scope = i['scope']
        if i['isScoped']:
          scope += '::' + i['name']

        for j in i['entries'].keys():
          id = scope + '::' + j
          id = re.sub('^::', '', id)
          pad = ' ' * (i['maxLen'] - len(j))
          raw_str += self.indent(1)
          raw_str += 'if ( CHECK_BIT( _var, {0}{2} ) ) {{ list.emplace_back( "{1}"{2} ); }}\n'.format(id, j, pad)

        raw_str += '\n{}return list;\n}}'.format(self.indent(1))

    return raw_str + '\n\n// clang-format on\n\n'


  def write(self) -> None:
    logging.info(f'Generating class {self.name} with {len(self.enums)} enums')

    ### set helper values
    self.maxIdLen = 0

    def calcID(indata: 'EnumDict') -> 'PocEnumDict':
      x: 'PocEnumDict' = T.cast('PocEnumDict', indata.copy())
      x['maxLen'] = 0
      x['scope'] = re.sub(r'^{}(::)?'.format(self.cfg.namespace), '', x['scope'])
      x['id'] = x['scope'] + '::' + x['name']
      x['id'] = re.sub('^::', '', x['id'])
      x['fname'] = re.sub('::', '_', x['id'])
      self.maxIdLen = max(len(x['id']), self.maxIdLen)

      for i in x['entries'].keys():
        x['maxLen'] = max(len(i), x['maxLen'])

      return x

    self.enums   = [calcID(x) for x in self.enums_raw]

    self.hppFile.write_text(self.genHpp())
    self.cppFile.write_text(self.genCpp())

    logging.info('Wrote source files')
