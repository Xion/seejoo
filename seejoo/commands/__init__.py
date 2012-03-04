# Import ALL the submodules!

import os as _os
import glob as _glob

_modules = (_os.path.basename(f)[:-len('.py')]
		  	for f in _glob.glob(_os.path.dirname(__file__) + '/*.py'))
for m in _modules:
	__import__(m, globals(), locals())