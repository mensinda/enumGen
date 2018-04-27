import logging
import sys
import re


# Extract enums from C++ source code
# NOTE: this is not a complete C++ parser!
#       it just detects namespace scopes (namespace, class, struct),
#       removes everything except enums and puts the result into a list
#
# the output list contains #!PUSH_SCOPE=<name> and #!POP_SCOPE
class Parser:
  enums = []

  def __init__(self, fp):
    self.file = fp

  def skipWhitespace(self):
    ws = [' ', '\t', '\n']
    while (self.notEOF() and self.get() in ws):
      self.next()

  def skipStack(self, open, close):
    n = 0
    if self.get() == open:
      n += 1
      self.next()

    while (n > 0 and self.notEOF()):
      n = n + 1 if (self.get() == open) else n
      n = n - 1 if (self.get() == close) else n
      self.next()

  # read a word from the internal buffer self.data
  def getWord(self):
    self.skipWhitespace()
    str = ''
    while (self.notEOF() and (self.get().isalnum() or self.get() == ':')):
      str += self.get()
      self.next()
    self.skipWhitespace()
    return str

  # Advance the internal iterator by one
  def next(self):
    self.it += 1

  # Get the char at the current position
  def get(self):
    return self.data[self.it] if self.notEOF() else ''

  # Check if the end was reached
  def notEOF(self):
    return self.it < len(self.data)

  # cleanup the source code: remove strings, templates, comments, defines
  # makes it a lot easier to parse later
  def cleanup(self):
    newData = ''

    self.data = re.sub('/\\*([^*]|\\*[^/])*\\*/', '', self.data)  # remove c style comments
    self.data = re.sub('//[^\n]*', '', self.data)  # remove c++ comments
    self.data = re.sub('\\\\\n', '', self.data)  # remove \\n  (for easy multi line strings and defines)
    self.data = re.sub('\\\\"', '', self.data)  # remove \"   (for easy string removal
    self.data = re.sub('#[^\n]*', '', self.data)  # remove defines
    self.data = re.sub('\\[\\[[^]]*\\]\\]', '', self.data)  # c++11 attributes
    self.data = re.sub('\t', ' ', self.data)  # tabs to spaces
    self.data = re.sub('alignas[ \n]*\\([^)]*\\)', ' ', self.data) # alignas

    ### Remove strings (regex are too greedy)
    while (self.notEOF()):
      if (self.get() == '"'):
        self.next()
        while (self.notEOF() and self.get() != '"'): self.next()
        self.next()
        continue

      newData += self.get()
      self.next()

    self.data = newData
    self.it = 0

    # remove inherited class definitions
    self.data = re.sub('\n', '', self.data)  # remove newlines
    self.data = re.sub('(class |struct ) *([a-zA-Z_0-9]+)[a-zA-Z_0-9 ]*:[^{]*', '\\1 \\2 ', self.data)
    self.data = re.sub(' +', ' ', self.data)  # one space only
    return True

  # Make the C++ scopes more readable and remove funcrion bodies, etc.
  # Outputs a list with just c++ commands, #!PUSH_SCOPE=<id>, #!POP_SCOPE and #!ACC=<normal|hidden>
  def scopeWalker(self):
    newData = ''
    stack = []

    while (self.notEOF()):
      self.skipWhitespace()

      # Skip uninteresting stuff (function bodies, etc)
      while (self.notEOF() and (not self.get().isalnum() and self.get() != ':')):
        # Replace block with ;
        if (self.get() == '{'):
          self.skipStack('{', '}')
          newData += ';'
          continue

        # A scope we care about closed
        if (self.get() == '}'):
          newData += '#!POP_SCOPE;'
          stack.pop()
          self.next()
          continue

        newData += self.get()
        self.next()

      word = self.getWord()

      ### Templates... DELTE THEM!!! WHY CAN YOU DO TEMPLATES INSIDE OF TEMPLATES!?!?!?
      if(word == 'template'):
        self.skipWhitespace()
        if(self.get() != '<'):
          logging.warning('Expected < after the template keyword')
          continue

        self.skipStack('<', '>')
        continue

      ### Handle namespaces
      if (word in ['namespace', 'class', 'struct', 'extern']):
        id = self.getWord()

        # Meh :( either using or forward declaration ==> skip we wont need it anyway
        if (self.get() == ';'):
          newData += ';'  # just to be on the safe side
          self.next()

        # Begin scope stack
        elif (self.get() == '{'):
          newData += "#!PUSH_SCOPE=" + id + ';'
          if (word == 'class'):
            newData += '#!ACC=hidden;'
          else:
            newData += '#!ACC=normal;'
          stack.append(id)
          self.next()

        continue

      ### Handle enums
      if (word == 'enum'):
        newData += 'enum '
        while (self.notEOF() and self.get() != ';'):
          newData += self.get()
          self.next()

        newData += ';'
        self.next()
        continue

      ### Word not found ==> append for now
      newData += word + ' '

    # Final cleanup
    newData = re.sub('public *:', '#!ACC=normal;', newData)
    newData = re.sub('(private|protected) *:', '#!ACC=hidden;', newData)
    newData = re.sub(';[ ;]+', ';', newData)  # remove double ;
    newData = re.sub(';[^#;]*#!', ';#!', newData)  # remove stuff in front of #!<command>
    return newData.split(';')

  # Removes private scopes, and non enum c++ statements
  def scopeCleaner(self, li):
    # remove all non control and non enum entries
    reg = re.compile('(^#![A-Z_]+.*$)|(^(typedef +)?enum +)')
    li = [i for i in li if reg.match(i)]

    newList = []
    stack = 0

    for i in li:
      # Remove entire hidden scopes
      if (stack > 1):
        if (i == '#!POP_SCOPE'):
          stack -= 1
        elif (re.search('#!PUSH_SCOPE', i)):
          stack += 1

        continue

      if (stack == 1):
        if (i == '#!POP_SCOPE' or i == '#!ACC=normal'):
          stack = 0
        elif (re.search('#!PUSH_SCOPE', i)):
          stack += 1
          continue
        else:
          continue

      if (i == '#!ACC=normal'): continue  # Remove
      if (i == '#!ACC=hidden'):
        stack = 1
        continue

      newList.append(i)

    return newList

  def parse(self):
    logging.info('Parsing file {}'.format(self.file.name))
    self.file.seek(0)
    self.data = self.file.read()
    self.it = 0

    self.cleanup()
    self.scopeList = self.scopeWalker()
    self.scopeList = self.scopeCleaner(self.scopeList)

    return True

  def getResult(self):
    return self.scopeList
