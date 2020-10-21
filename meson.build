project('enumGen', [])

enumGen = find_program('./enumGen.py')

cc_enumGen = generator(
  enumGen,
  output: ['@BASENAME@.json'],
  arguments: ['parse', '@INPUT@', '@OUTPUT@'],
)
