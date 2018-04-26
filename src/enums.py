import re

class Enums:
  enums = []

  def addEnum(self, scope, name, isClass, entries):
    self.enums.append({
      'scope': scope,
      'name': name,
      'isClass': True if isClass else False,
      'entries': entries
    })

  def addEnumsFromList(self, li):
    scopeStack = []
    for i in li:
      if(i == '#!POP_SCOPE'):
        scopeStack.pop()
        continue

      if(re.match('#!PUSH_SCOPE=', i)):
        sc = re.sub('^#!PUSH_SCOPE=', '', i)
        print('PUSH: {}'.format(sc))
        scopeStack.append(sc)
        continue

  def addParser(self, p):
    return self.addEnumsFromList(p.getResult())