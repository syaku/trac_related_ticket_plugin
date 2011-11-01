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
from trac.db import DatabaseManager
from trac.ticket.api import ITicketChangeListener, ITicketManipulator
from trac.resource import Resource, ResourceNotFound
import trac.util
import trac.util.datefmt
import re

class RelatedTicketPlugin(Component):
    implements(ITicketChangeListener,ITicketManipulator)
    NUMBERS_RE = re.compile(r'\d+', re.U)
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
            '''
            チケット削除時に存在しないidが入ってくる.
            チケットが存在しない場合はResourceNotFound Exceptionを投げる仕様(上がExceptionを拾ってUIに
            表示している)になっている仕様っぽい。
            ここではUIに表示したくないので、Exceptionを上に投げない。
            '''
            try:
                related_ticket = Ticket(self.env, id)
                self.delete_related_ticket(ticket, related_ticket)
            except ResourceNotFound, e:
                pass

    def ticket_deleted(self, ticket):
        ''' 削除(削除プラグインが存在する)'''
        list = self.get_ticket_id_list(ticket.values)
        for id in list:
            related_ticket = Ticket(self.env, id)
            self.delete_related_ticket(ticket, related_ticket)

    def get_ticket_id_list(self, ticket):
        ''' Ticketオブジェクトの関連チケットのIDリストを取得する処理 '''
        list = []
        if ticket.has_key(self.static_key_name):
            if ticket[self.static_key_name] == None:
                ''' rels_ticket項目追加前のチケットはsplitでこけるのでこの地点でreturn'''
                return list
            tmp_list = ticket[self.static_key_name].split(u',')
            for value in tmp_list:
                try:
                    list.append(int(value.lstrip(u' #')))
                except ValueError:
                    ''' さしあたってTicketID以外は無視. '''
                    pass
        return list
    
    ''' 関連チケットのカスタムフィールドの更新処理 (追加と削除でほとんど同じなんでまとめたい.) '''
   
    def add_related_ticket(self, ticket, related_ticket):
        ''' 関連チケットのカスタムフィールドを更新.(追加) '''
        related_list = self.get_ticket_id_list(related_ticket.values)
        if ticket.id in related_list:
            return
        else:
            related_list.append(ticket.id)
            related_list.sort()
            related_ticket[self.static_key_name] = u''
            for id in related_list:
                if related_ticket[self.static_key_name] != u'':
                    related_ticket[self.static_key_name] = related_ticket[self.static_key_name] + u','
                related_ticket[self.static_key_name] = related_ticket[self.static_key_name] + unicode("#"+str(id), encoding='utf-8')
            now = datetime.now(trac.util.datefmt.utc)
            related_ticket.save_changes(u'auto-script', u"関連チケットに登録されました.", now)

    def delete_related_ticket(self, ticket, related_ticket):
        ''' 関連チケットのカスタムフィールドを更新.(削除) '''
        related_list = self.get_ticket_id_list(related_ticket.values)
        
        if ticket.id in related_list:
            related_list.remove(ticket.id)
        else:
            return
                
        related_ticket[self.static_key_name] = u''
        for id in related_list:
            if related_ticket[self.static_key_name] != u'':
                related_ticket[self.static_key_name] = related_ticket[self.static_key_name] + u','
            related_ticket[self.static_key_name] = related_ticket[self.static_key_name] + unicode("#"+str(id), encoding='utf-8')
        now = datetime.now(trac.util.datefmt.utc)
        related_ticket.save_changes(u'auto-script', u"関連チケットから解除されました.", now)

    # ITicketManipulator methods
    def prepare_ticket(self, req, ticket, fields, actions):
        pass

    def validate_ticket(self, req, ticket):
        ''' チケットの存在チェック '''
        db = self.env.get_db_cnx()
        cursor = db.cursor()

        try:
            list = self.NUMBERS_RE.findall(ticket[self.static_key_name] or '')

            for id in list[:]:
                cursor.execute('SELECT id FROM ticket WHERE id=%s', (id,))
                row = cursor.fetchone()
                if row is None:
                    '''存在しないチケットの場合、メッセージを投げる(メッセージを投げると、上でエラーと判断してくれるので)'''
                    yield None, u'チケット %s は存在しません。'%id

            '''チケットIDの先頭に#をつけてやる(この地点で付ければ、入力で#が付いていなくてもチケットIDとして認識するはず)'''
            ticket[self.static_key_name] = u','.join(map(lambda x: u'#' + x ,sorted(list, key=lambda x: int(x))) )
        except Exception, e:
            yield self.static_key_name, u'Not a valid list of ticket IDs'


