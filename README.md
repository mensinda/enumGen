# enumGen
Generate enum to string class form C++ headers

## Usage
```bash
./enumGen.py parse    test/test1.hpp  # generates intermediate test1.json
# additional parse calls...

./enumGen.py generate Enum2Str *.json # generates class Enum2Str (Enum2Str.{cpp,hpp})
```

for more information see `./enumGen.py -h` and `./enumGen.py parse -h` and `./enumGen.py generate -h`
