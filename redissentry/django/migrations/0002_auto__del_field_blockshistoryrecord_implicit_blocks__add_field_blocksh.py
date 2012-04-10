# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'BlocksHistoryRecord.implicit_blocks'
        db.delete_column('redissentry_blockshistoryrecord', 'implicit_blocks')

        # Adding field 'BlocksHistoryRecord.block_type'
        db.add_column('redissentry_blockshistoryrecord', 'block_type',
                      self.gf('django.db.models.fields.CharField')(default='A', max_length=1),
                      keep_default=False)

        # Adding field 'BlocksHistoryRecord.failed_attempts'
        db.add_column('redissentry_blockshistoryrecord', 'failed_attempts',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)

        # Adding field 'BlocksHistoryRecord.blocked_attempts'
        db.add_column('redissentry_blockshistoryrecord', 'blocked_attempts',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)

    def backwards(self, orm):
        # Adding field 'BlocksHistoryRecord.implicit_blocks'
        db.add_column('redissentry_blockshistoryrecord', 'implicit_blocks',
                      self.gf('django.db.models.fields.IntegerField')(default=0),
                      keep_default=False)

        # Deleting field 'BlocksHistoryRecord.block_type'
        db.delete_column('redissentry_blockshistoryrecord', 'block_type')

        # Deleting field 'BlocksHistoryRecord.failed_attempts'
        db.delete_column('redissentry_blockshistoryrecord', 'failed_attempts')

        # Deleting field 'BlocksHistoryRecord.blocked_attempts'
        db.delete_column('redissentry_blockshistoryrecord', 'blocked_attempts')

    models = {
        'redissentry.blockshistoryrecord': {
            'Meta': {'object_name': 'BlocksHistoryRecord'},
            'block_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'blocked_attempts': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'failed_attempts': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'last_segment_duration': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['redissentry']