import re
import logging
import os
import pathlib


hppHead = """
"""


class Generator:
  incList = []
  enums = []



  def __init__(self, cfg, name):
    self.cfg = cfg
    self.name = name

    self.cfg['generator']['hppFile'] = re.sub('@CLASS_NAME@', name, self.cfg['generator']['hppFile'])
    self.cfg['generator']['cppFile'] = re.sub('@CLASS_NAME@', name, self.cfg['generator']['cppFile'])



  def addEnums(self, incFile, enums):
    if len(enums) > 0:
      self.incList.append(incFile)
      self.enums += enums



  def indent(self, level):
    if self.cfg['generator']['indent'] >= 0:
      return ' ' * (self.cfg['generator']['indent'] * level)
    else:
      return ''



  def genHpp(self):
    str = '''/*!
 * \\file {}
 * \\warning This is an automatically generated file!
 */

// clang-format off

#pragma once

#include <string>
'''.format(self.cfg['generator']['hppFile'])

    for i in self.incList:
      str += '#include "%s"\n' % i

    ### Open namespace
    if len(self.cfg['class']['namespace']) > 0:
      str += '\nnamespace %s {\n' % self.cfg['class']['namespace']

    ### Begin class / namespace
    if self.cfg['class']['useNamespace']:
      str += '\nnamespace %s {\n\n' % self.name
      baseLevel = 1
      static = ''
    else:
      baseLevel = 2
      static = 'static '
      str += '\nclass %s final {\n' % self.name
      str += self.indent(1) + 'public:\n'
      str += self.indent(2) + '%s() = delete;\n\n' % self.name

    # To string declarations
    fName = self.cfg['class']['funcName']
    for i in self.enums:
      pad = ' ' * (self.maxIdLen - len(i['id']))
      str += self.indent(baseLevel) + '%sstd::string %s( %s%s _var ) noexcept;\n' % (static, fName, i['id'], pad)

    if self.cfg['class']['enableBitfields']:
      str += '\n\n' + self.indent(baseLevel)
      str += '%sstd::string stringListToString(std::vector<std::string> _list) noexcept;\n\n' % static

      type = self.cfg['class']['bitfieldType']

      for i in self.enums:
        bitName = '{}_{}'.format(re.sub('::', '_', i['id']), fName)
        str += self.indent(baseLevel) + '%sstd::string %s( %s _var ) noexcept;\n' % (static, bitName, type)

      str += '\n\n'

      for i in self.enums:
        bitName = '{}_{}_Raw'.format(re.sub('::', '_', i['id']), fName)
        str += self.indent(baseLevel) + '%sstd::vector<std::string> %s( %s _var ) noexcept;\n' % (static, bitName, type)

    ### End class namespace
    if self.cfg['class']['useNamespace']:
      str += '\n} // namespace %s\n\n' % self.name
    else:
      str += '\n}; // class %s\n\n' % self.name

    ### Close namespace
    if len(self.cfg['class']['namespace']) > 0:
      str += '} // namespace %s \n\n' % self.cfg['class']['namespace']

    return str + '// clang-format on\n\n'



  def genCpp(self):
    str = '''/*!
 * \\file {0}
 * \\warning This is an automatically generated file!
 */

// clang-format off

#include "{1}"

#define CHECK_BIT(v, x) (v & static_cast<{2}>(x)) == static_cast<{2}>(x)

'''.format(self.cfg['generator']['cppFile'], self.cfg['generator']['hppFile'], self.cfg['class']['bitfieldType'])

    if len(self.cfg['class']['namespace']) > 0:
      str += 'using namespace %s;\n\n' % self.cfg['class']['namespace']

    fName = self.cfg['class']['funcName']

    # Generate switch case
    for i in self.enums:
      str += '''

/*!
 * \\brief Converts the enum {0} to a std::string
 * \\param _var The enum value to convert
 * \\returns _var converted to a std::string
 */
std::string {3}::{2}( {0} _var ) noexcept {{
{1}switch( _var ) {{
'''.format(i['id'], self.indent(1), fName, self.name)

      scope = i['scope']
      if i['isScoped']:
        scope += '::' + i['name']

      for j in i['entries'].keys():
        if j in i['blackList']:
          continue

        id = scope + '::' + j
        id = re.sub('^::', '', id)
        pad = ' ' * (i['maxLen'] - len(j))
        str += self.indent(2) + 'case {0}:{2} return "{1}"{2} ;\n'.format(id, j, pad)

      str += self.indent(2) + 'default: return "<UNKNOWN>";\n'
      str += self.indent(1) + '}\n}'

    if self.cfg['class']['enableBitfields']:
      for i in self.enums:
        str += '''

/*!
 * \\brief Converts the enum bitfield {0} to a std::string
 * \\param _var The bitfield value to convert
 * \\returns The _var bitfield converted to a std::string
 */
std::string {5}::{1}_{4}( {3} _var ) noexcept {{
{2}return stringListToString( {1}_{4}_Raw( _var ) );
}}
'''.format(i['id'], re.sub('::', '_', i['id']), self.indent(1), self.cfg['class']['bitfieldType'], fName, self.name)

      for i in self.enums:
        str += '''

/*!
 * \\brief Converts the enum bitfield {0} to std::vector of std::string
 * \\param _var The bitfield value to convert
 * \\returns _var converted to a std::vector of std::string
 */
std::vector<std::string> {5}::{1}_{4}_Raw( {3} _var ) noexcept {{
{2}std::vector<std::string> list;
'''.format(i['id'], re.sub('::', '_', i['id']), self.indent(1), self.cfg['class']['bitfieldType'], fName, self.name)

        scope = i['scope']
        if i['isScoped']:
          scope += '::' + i['name']

        for j in i['entries'].keys():
          id = scope + '::' + j
          id = re.sub('^::', '', id)
          pad = ' ' * (i['maxLen'] - len(j))
          str += self.indent(1)
          str += 'if ( CHECK_BIT( _var, {0}{2} ) ) {{ list.emplace_back( "{1}"{2} ); }}\n'.format(id, j, pad)

        str += '\n{}return list;\n}}'.format(self.indent(1))

    return str + '\n\n// clang-format on\n\n'



  def write(self, dir, projectRoot):
    logging.info('Generating class {} with {} enums'.format(self.name, len(self.enums)))
    logging.info('Writing {}'.format(self.cfg['generator']['hppFile']))

    ### set helper values
    self.maxIdLen = 0



    def calcID(x):
      x['maxLen'] = 0
      x['scope'] = re.sub('^{}(::)?'.format(self.cfg['class']['namespace']), '', x['scope'])
      x['id'] = x['scope'] + '::' + x['name']
      x['id'] = re.sub('^::', '', x['id'])
      self.maxIdLen = max(len(x['id']), self.maxIdLen)

      for i in x['entries'].keys():
        x['maxLen'] = max(len(i), x['maxLen'])

      return x



    self.enums = list(map(calcID, self.enums))
    self.incList = list(map(lambda x: os.path.relpath(x, dir) if projectRoot in x else x, self.incList))

    pHpp = pathlib.Path(dir) / self.cfg['generator']['hppFile']
    pCpp = pathlib.Path(dir) / self.cfg['generator']['cppFile']

    fHpp = open(pHpp, 'w')
    fCpp = open(pCpp, 'w')

    fHpp.write(self.genHpp())
    fCpp.write(self.genCpp())

    logging.info('Wrote {}'.format(pHpp))
    logging.info('Wrote {}'.format(pCpp))
