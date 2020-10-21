# enumGen

Generate C++ code to convert an enum value to a string + more.

## Usage
```bash
./enumGen.py parse    test/test1.hpp out/test1.json # generates intermediate test1.json
# additional parse calls...

./enumGen.py generate Enum2Str Enum2Str.hpp Enum2Str.cpp *.json # generates class Enum2Str (Enum2Str.{cpp,hpp})
```

for more information see `./enumGen.py -h` and `./enumGen.py parse -h` and `./enumGen.py generate -h`
