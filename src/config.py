import json


class Config:
  cfg = {
    'class': {
      'className': 'Enum2Str',
      'funcName': 'toStr',
      'namespace': '',
      'useConstexpr': False,
      'useCStrings': False
    },
    'generator': {
      'path': '.',
      'indentStr': '  ',
      'bitfieldConcat': ' | ',
      'compact': False,
      'enableBitfields': True
    },
    'extract': {
      'inputFileTypes': ['h', 'hpp', 'h++', 'hxx', 'H', 'HPP', 'H++', 'HXX'],
      'blacklistEnums': []
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
