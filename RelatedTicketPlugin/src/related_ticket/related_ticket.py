# -*- coding: utf-8 -*-

'''
Created on 2011/07/09

@author: syaku
'''
from datetime import datetime, timedelta

from trac.core import *
from trac.ticket.api import ITicketChangeListener
from trac.ticket.api import TicketSystem
from trac.ticket.model import Ticket
import trac.util
import trac.util.datefmt

class RelatedTicketPlugin(Component):
    implements(ITicketChangeListener)
    '''
    classdocs
    '''
    ''' Pythonにはstaticとか無いけど一応そういう風に扱うよ '''
    static_key_name = 'rels_ticket'
    
    def ticket_created(self, ticket):
        list = self.get_ticket_id_list(ticket.values)
        
        for id in list:
            related_ticket = Ticket(self.env, id)
            self.add_related_ticket(ticket, related_ticket)
    
    def ticket_changed(self, ticket, comment, author, old_values):
        if not old_values.has_key(self.static_key_name):
            return
        
        list = self.get_ticket_id_list(ticket.values)
        old_list = self.get_ticket_id_list(old_values)

        ''' 削除されたIDだけ残す '''       
        for id in list:
            try:
                old_list.remove(id)
            except ValueError:
                pass
        
        for id in list:
            related_ticket = Ticket(self.env, id)
            self.add_related_ticket(ticket, related_ticket)
    
        for id in old_list:
            related_ticket = Ticket(self.env, id)
            self.delete_related_ticket(ticket, related_ticket)
        
    def ticket_deleted(self, ticket):
        ''' 削除ってあったっけ? '''
        pass
    
    def get_ticket_id_list(self, ticket):
        ''' Ticketオブジェクトの関連チケットのIDリストを取得する処理 '''
        list = []
        if ticket.has_key(self.static_key_name):
            tmp_list = ticket[self.static_key_name].split(',')
            for value in tmp_list:
                try:
                    list.append(int(value.lstrip(' #')))
                except ValueError:
                    ''' さしあたってTicketID以外は無視. '''
                    pass
        return list
    
    def add_related_ticket(self, ticket, related_ticket):
        ''' 関連チケットのカスタムフィールドを更新. '''
        related_list = self.get_ticket_id_list(related_ticket.values)
        if ticket.id in related_list:
            return
        else:
            related_list.append(ticket.id)
            related_list.sort()
            related_ticket[self.static_key_name] = ''
            for id in related_list:
                if related_ticket[self.static_key_name] != '':
                    related_ticket[self.static_key_name] = related_ticket[self.static_key_name] + ','
                related_ticket[self.static_key_name] = related_ticket[self.static_key_name] + "#"+str(id)
            now = datetime.now(trac.util.datefmt.utc)
            related_ticket.save_changes('auto-script', "関連チケットに登録しました.", now)
            
    def delete_related_ticket(self, ticket, related_ticket):
        pass
        