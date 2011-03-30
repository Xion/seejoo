
def import_plugins():
	'''
	Imports plugin modules.
	These imports are contained within separate functions
	rather than put directly into the module because we must
	ensure that they are imported AFTER config.yaml is read
	(otherwise the disabled_plugins option would not be honored).
	'''
	import greet
	import stats
	import memo
