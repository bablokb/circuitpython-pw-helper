# ----------------------------------------------------------------------------
# SecretsManager.py: manage secrets
#
# Author: Bernhard Bablok
# License: GPL3
#
# Website: https://github.com/bablokb/circuitpython-pw-helper
#
# ----------------------------------------------------------------------------

# try to import secrets
try:
  from secrets import secrets
except ImportError:
  raise RuntimeError("secrets are managed in file secrets.py")

class SecretsManager:
  """ manage list of secrets """

  # --- constructor   --------------------------------------------------------

  def __init__(self):
    """ constructor """

    self._list  = secrets
    self._index = 0

  # -- return entry by key   -------------------------------------------------

  def __getitem__(self,key):
    """ return entry by index """

    return self._list[key]

  # -- return current entry   ------------------------------------------------

  def current(self):
    """ return current entry """

    return self._list[self._index]

  # --- navigate to and return next entry   ----------------------------------

  def next(self):
    """ navigate to next entry and return it   """

    self._index = (self._index + 1) % len(self._list)
    return self._list[self._index]

  # --- navigate to and return previous entry   ------------------------------

  def prev(self):
    """ navigate to prev entry and return it   """

    if self._index == 0:
      self._index = len(self._list) - 1
    else:
      self._index = self._index - 1
    return self._list[self._index]
