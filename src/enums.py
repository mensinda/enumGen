import re
import logging


class Enums:
  enums = []

  def addEnum(self, scope, isScoped, name, entries, blackList):
    self.enums.append({
      'scope': scope,
      'isScoped': True if (isScoped) else False,
      'name': name,
      'entries': entries,
      'blackList': blackList
    })
    logging.info(
      'Found enum "{}" with {} entries with {} duplicates detected'.format(name, len(entries), len(blackList)))

  def parseEnum(self, str, scope):
    # Get name and scope
    decl = re.sub('{[^}]*}', '', str)  # remove the enum entries

    isClass = True if ('class' in decl or 'struct' in decl) else False
    isTypedef = True if ('typedef' in decl) else False

    for i in ['class', 'struct', 'typedef', 'enum']:
      decl = re.sub(i, '', decl)

    nameList = decl.split(' ')
    nameList = list(filter(None, nameList))  # remove empty entries

    name = nameList[0] if (not isTypedef) else nameList[-1]

    ### Parse the enum body
    body = re.sub('(^[^{]+{)|(}[^}]*$)', '', str)  # only the enum body
    body = re.sub(' ', '', body)
    body = body.split(',')

    ### Calculate enum values
    enums = {}
    nextValue = 0
    blackList = []

    for i in body:
      en = re.sub('=.*', '', i)
      value = nextValue
      nextValue += 1

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

        if (len(temp) == 0):
          value = eval(val)
          nextValue = value + 1
        else:
          value = val

      if (value in enums.values()):
        blackList.append(en)

      enums[en] = value

    self.addEnum(scope, isClass, name, enums, blackList)
    return True

  def addEnumsFromList(self, li):
    scopeStack = []
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

    if (len(scopeStack) != 0):
      logging.warning('Parsing error: scope stack not empty')
      return False

    return True

  def addParser(self, p):
    return self.addEnumsFromList(p.getResult())
