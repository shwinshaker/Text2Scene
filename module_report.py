#!./env python

#!/usr/bin/env python
import sys
from modulefinder import ModuleFinder
finder = ModuleFinder()
finder.run_script(sys.argv[1])
# finder.report()
for name, mod in finder.modules.items():
    print(name)
