#!/usr/env/bin python
# -*- encoding: utf-8 -*-

"""
Config agent for master and archive configurations.
"""

import json
import os
import uuid

from support import SingletonMeta
from log import ABUNDANT_LOGGER

__author__ = 'Kevin'

MASTER_CONFIG_TEMPLATE = {
    'MasterConfigVersion': 0.1,
    'ArchiveRecords': []
}

ARCHIVE_RECORD_TEMPLATE = {
    'SourceDirectory': '',
    'ArchiveDirectory': '',
    'UUID': ''
}


class MasterConfigAgent(metaclass=SingletonMeta):
    """Agent for master configurations."""

    def __init__(self):
        """Create the agent."""
        self.load_config()

    def load_config(self):
        """Load the config."""
        with open('init_config.json', mode='r', encoding='utf-8') as raw_init_config:
            self.init_config = json.load(raw_init_config)
        ABUNDANT_LOGGER.info('Loaded initialisation config')

        master_config_dir = self.init_config['MasterConfigDirectory']
        self.master_config_path = os.path.join(master_config_dir, 'master_config.json')

        if not os.path.exists(self.master_config_path):
            ABUNDANT_LOGGER.warning('No master config found')
            self.save_config(use_default_template=True)

        with open(self.master_config_path, mode='r', encoding='utf-8') as raw_master_config:
            self.master_config = json.load(raw_master_config)
        ABUNDANT_LOGGER.info('Loaded master config')

    def save_config(self, use_default_template=False):
        """Save the config."""
        with open(self.master_config_path, mode='w', encoding='utf-8') as raw_master_config:
            json.dump(self.master_config if not use_default_template else MASTER_CONFIG_TEMPLATE, raw_master_config)
        if use_default_template:
            ABUNDANT_LOGGER.debug('Create default master config')

    def __getitem__(self, item: str):
        """Get an master config item."""
        return self.master_config[item]

    def __setitem__(self, key, value):
        """Update a master config item."""
        self.master_config[key] = value
        self.save_config()
        ABUNDANT_LOGGER.info('Updated master config [%s] to [%s]' % (key, value))

    @property
    def archive_records(self) -> list:
        """Getter shortcut for archive records."""
        return self.master_config['ArchiveRecords']

    def add_archive_record(self, source_dir: str, archive_dir: str):
        """Add an archive record."""
        archive_uuid = str(uuid.uuid4())
        while self.get_archive_record(archive_uuid):
            archive_uuid = str(uuid.uuid4())

        archive_record = dict(ARCHIVE_RECORD_TEMPLATE)
        archive_record.update({
            'SourceDirectory': source_dir,
            'ArchiveDirectory': archive_dir,
            'UUID': archive_uuid
        })
        self.archive_records.append(archive_record)
        self.save_config()

        ABUNDANT_LOGGER.info('Added archive record: %s' % archive_uuid)
        ABUNDANT_LOGGER.debug('From %s to %s' % (source_dir, archive_dir))
        return archive_record

    def get_archive_record(self, uuid=None, source_dir=None, archive_dir=None) -> dict:
        """Get an archive record matching given restraints."""
        if uuid is None and source_dir is None and archive_dir is None:
            raise ValueError('Must provide at least one restraint')
        for archive_record in self.archive_records:
            if uuid and uuid != archive_record['UUID']:
                continue
            if source_dir and source_dir != archive_record['SourceDirectory']:
                continue
            if archive_dir and archive_dir != archive_record['ArchiveDirectory']:
                continue
            return archive_record
        return None

    def delete_archive_record(self, uuid=None, source_dir=None, archive_dir=None):
        """Delete an archive record matching given restraints."""
        archive = self.get_archive_record(uuid, source_dir, archive_dir)
        if archive_dir is not None:
            self.archive_records.remove(archive)
            ABUNDANT_LOGGER.info('Deleted archive record: %s' % archive['UUID'])
