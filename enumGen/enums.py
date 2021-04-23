import re
import logging
import typing as T

if T.TYPE_CHECKING:
  from .parser import Parser

  class EnumDict(T.TypedDict):
    scope:     str
    isScoped:  bool
    name:      str
    entries:   T.Dict[str, T.Union[str, int]]
    blackList: T.List[str]

class Enums:
  def __init__(self) -> None:
    self.enums: T.List['EnumDict'] = []

  def addEnum(self, scope: str, isScoped: bool, name: str, entries: T.Dict[str, T.Union[str, int]], blackList: T.List[str]) -> None:
    self.enums += [{
      'scope':     scope,
      'isScoped':  isScoped,
      'name':      name,
      'entries':   entries,
      'blackList': blackList,
    }]
    logging.info(f'Found enum "{name}" with {len(entries)} entries with {len(blackList)} duplicates detected')

  def parseEnum(self, raw: str, scope: str) -> None:
    # Get name and scope
    decl = re.sub('{[^}]*}', '', raw)  # remove the enum entries

    isClass   = True if ('class' in decl or 'struct' in decl) else False
    isTypedef = True if ('typedef' in decl) else False

    for i in ['class', 'struct', 'typedef', 'enum']:
      decl = re.sub(i, '', decl)

    nameList = decl.split(' ')
    nameList = list(filter(None, nameList))  # remove empty entries

    if not nameList:
      logging.warning('Could not determine the name of the enum --> skipping')
      return

    name = nameList[0] if (not isTypedef) else nameList[-1]

    ### Parse the enum body
    body_str = re.sub('(^[^{]+{)|(}[^}]*$)', '', raw)  # only the enum body
    body_str = re.sub(' ', '', body_str)
    body = body_str.split(',')

    ### Calculate enum values
    enums: T.Dict[str, T.Union[str, int]] = {}
    nextValue = 0
    blackList = []

    for i in body:
      en = re.sub('=.*', '', i)
      value: T.Union[str, int] = nextValue
      nextValue += 1

      if not en:
        continue

      if ('=' in i):
        val = re.sub('.*=', '', i)

        # check for known values
        splitList = re.split('[^A-Za-z0-9_]', val)
        for j in splitList:
          if (j in enums.keys()):
            val = val.replace(j, '{}'.format(enums[j]))

        # check input before eval --> remove all legal strings and then check if empty
        temp = val
        for j in ['0x[0-9A-Fa-f]+', '0b[01]+', '[0-9]', '[()\\+\\-\\*\\/]', '<<', '>>']:
          temp = re.sub(j, '', temp)

        if len(temp) == 0:
          value = eval(val)
          assert isinstance(value, int)
          nextValue = value + 1
        else:
          value = val

      if (value in enums.values()):
        blackList.append(en)

      enums[en] = value

    self.addEnum(scope, isClass, name, enums, blackList)

  def parseScope(self, parser: 'Parser') -> bool:
    scopeStack: T.List[str] = []
    li = parser.getResult()
    for i in li:
      if (i == '#!POP_SCOPE'):
        scopeStack.pop()
        continue

      if (re.match('#!PUSH_SCOPE=', i)):
        sc = re.sub('^#!PUSH_SCOPE=', '', i)
        scopeStack.append(sc)
        continue

      scope = '::'.join(scopeStack)
      self.parseEnum(i, scope)

    if scopeStack:
      logging.warning('Parsing error: scope stack not empty')
      return False

    return True
