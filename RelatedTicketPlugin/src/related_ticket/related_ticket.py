'''
Created on 2011/07/09

@author: syaku
'''

from trac.core import *
from trac.ticket.api import ITicketChangeListener

class RelatedTicketPlugin(Component):
    implements(ITicketChangeListener)
    '''
    classdocs
    '''
    def ticket_created(self, ticket):
        pass
    
    def ticket_changed(self, ticket):
        pass
    
    def ticket_deleted(self, ticket):
        pass