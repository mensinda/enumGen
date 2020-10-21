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

    self.indent          = 2
    self.bitfieldConcat  = ' | '
    self.defaultValue   = '<UNKNOWN>'

  @property
  def cfg(self) -> T.Dict[str, T.Any]:
    return {
      'funcName': self.funcName,
      'namespace': self.namespace,
      'useNamespace': self.useNamespace,
      'enableBitfields': self.enableBitfields,
      'bitfieldType': self.bitfieldType,
      'indent': self.indent,
      'bitfieldConcat': self.bitfieldConcat,
      'defaultValue': self.defaultValue
    }

  def toJSON(self) -> str:
    return json.dumps(self.cfg, indent=2)

  def writeJSON(self, dest: Path) -> None:
    dest.write_text(json.dumps(self.cfg, indent=2))

  def readJSON(self, src: Path) -> None:
    data = json.loads(src.read_text())
    if not isinstance(data, dict):
      return

    self.funcName        = data.get('funcName',        self.funcName)
    self.namespace       = data.get('namespace',       self.namespace)
    self.useNamespace    = data.get('useNamespace',    self.useNamespace)
    self.enableBitfields = data.get('enableBitfields', self.enableBitfields)
    self.indent          = data.get('indent',          self.indent)
    self.bitfieldConcat  = data.get('bitfieldConcat',  self.bitfieldConcat)
    self.defaultValue    = data.get('defaultValue',    self.defaultValue)
