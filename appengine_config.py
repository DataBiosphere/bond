from google.appengine.ext import vendor

# Set path to your libraries folder.
path = 'lib'
# Add libraries installed in the path folder.
vendor.add(path)

# Import pkg_resources after libraries have been installed.
import pkg_resources
# Add libraries to pkg_resources working set to find the distribution.
pkg_resources.working_set.add_entry(path)
