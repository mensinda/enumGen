import logging
import sys
import re
from pathlib import Path
import typing as T

# Extract enums from C++ source code
# NOTE: this is not a complete C++ parser!
#       it just detects namespace scopes (namespace, class, struct),
#       removes everything except enums and puts the result into a list
#
# the output list contains #!PUSH_SCOPE=<name> and #!POP_SCOPE
class Parser:
  def __init__(self, fp: Path):
    self.scopeList: T.List[str] = []
    self.file                   = fp
    self.data                   = fp.read_text()
    self.it                     = 0

  def skipWhitespace(self) -> None:
    ws = [' ', '\t', '\n']
    while (self.notEOF() and self.get() in ws):
      self.advance()

  def skipStack(self, open_t: str, close_t: str) -> None:
    n = 0
    if self.get() == open_t:
      n += 1
      self.advance()

    while (n > 0 and self.notEOF()):
      n = n + 1 if (self.get() == open_t) else n
      n = n - 1 if (self.get() == close_t) else n
      self.advance()

  # read a word from the internal buffer self.data
  def getWord(self) -> str:
    self.skipWhitespace()
    res = ''
    while (self.notEOF() and (self.get().isalnum() or self.get() == ':')):
      res += self.get()
      self.advance()
    self.skipWhitespace()
    return res

  # Advance the internal iterator by one
  def advance(self) -> None:
    self.it += 1

  # Get the char at the current position
  def get(self) -> str:
    return self.data[self.it] if self.notEOF() else ''

  # Check if the end was reached
  def notEOF(self) -> bool:
    return self.it < len(self.data)

  # cleanup the source code: remove strings, templates, comments, defines
  # makes it a lot easier to parse later
  def cleanup(self) -> None:
    newData = ''

    self.data = re.sub('/\\*([^*]|\\*[^/])*\\*/',  '',  self.data)  # remove c style comments
    self.data = re.sub('//[^\n]*',                 '',  self.data)  # remove c++ comments
    self.data = re.sub('\\\\\n',                   '',  self.data)  # remove \\n  (for easy multi line strings and defines)
    self.data = re.sub('\\\\"',                    '',  self.data)  # remove \"   (for easy string removal
    self.data = re.sub('#[^\n]*',                  '',  self.data)  # remove defines
    self.data = re.sub('\\[\\[[^]]*\\]\\]',        '',  self.data)  # c++11 attributes
    self.data = re.sub('\t',                       ' ', self.data)  # tabs to spaces
    self.data = re.sub('alignas[ \n]*\\([^)]*\\)', ' ', self.data)  # alignas

    ### Remove strings (regex are too greedy)
    while (self.notEOF()):
      if (self.get() == '"'):
        self.advance()
        while (self.notEOF() and self.get() != '"'): self.advance()
        self.advance()
        continue

      newData += self.get()
      self.advance()

    self.data = newData
    self.it = 0

    # remove inherited class definitions
    self.data = re.sub('\n', '', self.data)  # remove newlines
    self.data = re.sub('(class |struct ) *([a-zA-Z_0-9]+)[a-zA-Z_0-9 ]*:[^{]*', '\\1 \\2 ', self.data)
    self.data = re.sub(' +', ' ', self.data)  # one space only

  # Make the C++ scopes more readable and remove funcrion bodies, etc.
  # Outputs a list with just c++ commands, #!PUSH_SCOPE=<id>, #!POP_SCOPE and #!ACC=<normal|hidden>
  def scopeWalker(self) -> T.List[str]:
    newData = ''
    stack: T.List[str] = []

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
          self.advance()
          continue

        newData += self.get()
        self.advance()

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
          self.advance()

        # Begin scope stack
        elif (self.get() == '{'):
          newData += "#!PUSH_SCOPE=" + id + ';'
          if (word == 'class'):
            newData += '#!ACC=hidden;'
          else:
            newData += '#!ACC=normal;'
          stack.append(id)
          self.advance()

        continue

      ### Handle enums
      if (word == 'enum'):
        newData += 'enum '
        while (self.notEOF() and self.get() != ';'):
          newData += self.get()
          self.advance()

        newData += ';'
        self.advance()
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
  def scopeCleaner(self, li: T.List[str]) -> T.List[str]:
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

  def parse(self) -> None:
    logging.info('Parsing file {}'.format(self.file.name))
    self.it = 0

    self.cleanup()
    self.scopeList = self.scopeWalker()
    self.scopeList = self.scopeCleaner(self.scopeList)

  def getResult(self) -> T.List[str]:
    return self.scopeList
