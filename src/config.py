import json


class Config:
  cfg = {
    'class': {
      'funcName': 'toStr',
      'namespace': '',
      'useNamespace': False,
      'enableBitfields': True,
      'bitfieldType': 'uint64_t'
    },
    'generator': {
      'hppFile': '@CLASS_NAME@.hpp',
      'cppFile': '@CLASS_NAME@.cpp',
      'indent': 2,
      'bitfieldConcat': ' | '
    }
  }

  def toJSON(self):
    return json.dumps(self.cfg, indent=2)

  def writeJSON(self, dest):
    json.dump(self.cfg, dest, indent=2)

  def readJSON(self, src):
    data = json.load(src)
    for i in self.cfg:
      if (i not in data):
        continue

      for j in self.cfg[i]:
        if (j not in data[i]):
          continue

        self.cfg[i][j] = data[i][j]
