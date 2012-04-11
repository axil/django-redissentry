# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'BlocksHistoryRecord.failed_attempts'
        db.alter_column('redissentry_blockshistoryrecord', 'failed_attempts', self.gf('django.db.models.fields.IntegerField')(null=True))

        # Changing field 'BlocksHistoryRecord.blocked_attempts'
        db.alter_column('redissentry_blockshistoryrecord', 'blocked_attempts', self.gf('django.db.models.fields.IntegerField')(null=True))
    def backwards(self, orm):

        # Changing field 'BlocksHistoryRecord.failed_attempts'
        db.alter_column('redissentry_blockshistoryrecord', 'failed_attempts', self.gf('django.db.models.fields.IntegerField')())

        # Changing field 'BlocksHistoryRecord.blocked_attempts'
        db.alter_column('redissentry_blockshistoryrecord', 'blocked_attempts', self.gf('django.db.models.fields.IntegerField')())
    models = {
        'redissentry.blockshistoryrecord': {
            'Meta': {'object_name': 'BlocksHistoryRecord'},
            'block_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'blocked_attempts': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'db_index': 'True', 'blank': 'True'}),
            'failed_attempts': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.CharField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'last_segment_duration': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'db_index': 'True', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['redissentry']