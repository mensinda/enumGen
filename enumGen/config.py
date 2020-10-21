import json
from pathlib import Path
import typing as T

class Config:
  def __init__(self) -> None:
    self.funcName        = 'toStr'
    self.namespace       = ''
    self.useNamespace    = False
    self.enableBitfields = True
    self.bitfieldType    = 'uint64_t'

    self.hppFile         = '@CLASS_NAME@.hpp'
    self.cppFile         = '@CLASS_NAME@.cpp'
    self.indent          = 2
    self.bitfieldConcat  = ' | '
    self.defaultValue   = '<UNKNOWN>'

  @property
  def cfg(self) -> T.Dict[str, T.Any]:
    return {
      'class': {
        'funcName': self.funcName,
        'namespace': self.namespace,
        'useNamespace': self.useNamespace,
        'enableBitfields': self.enableBitfields,
        'bitfieldType': self.bitfieldType,
      },
      'generator': {
        'hppFile': self.hppFile ,
        'cppFile': self.cppFile,
        'indent': self.indent,
        'bitfieldConcat': self.bitfieldConcat,
        'defaultValue': self.defaultValue
      }
    }

  def toJSON(self) -> str:
    return json.dumps(self.cfg, indent=2)

  def writeJSON(self, dest: Path) -> None:
    dest.write_text(json.dumps(self.cfg, indent=2))

  def readJSON(self, src: Path) -> None:
    data = json.loads(src.read_text())
    if not isinstance(data, dict):
      return

    cls_data = data.get('class', {})
    gen_data = data.get('generator', {})

    assert isinstance(cls_data, dict)
    assert isinstance(gen_data, dict)

    self.funcName        = cls_data.get('funcName',        self.funcName)
    self.namespace       = cls_data.get('namespace',       self.namespace)
    self.useNamespace    = cls_data.get('useNamespace',    self.useNamespace)
    self.enableBitfields = cls_data.get('enableBitfields', self.enableBitfields)
    self.hppFile         = gen_data.get('hppFile',         self.hppFile)
    self.cppFile         = gen_data.get('cppFile',         self.cppFile)
    self.indent          = gen_data.get('indent',          self.indent)
    self.bitfieldConcat  = gen_data.get('bitfieldConcat',  self.bitfieldConcat)
    self.defaultValue    = gen_data.get('defaultValue',    self.defaultValue)
