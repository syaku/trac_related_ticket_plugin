from setuptools import setup

PACKAGE = 'RelatedTicket'
VERSION = '0.1'

setup(name=PACKAGE,
      version=VERSION,
      packages=['related_ticket'],
      entry_points={'trac.plugins': '%s = related_ticket' % PACKAGE},
)