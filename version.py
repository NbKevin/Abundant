#!/usr/env/bin python
# -*- encoding: utf-8 -*-

"""
Agents for various backup versions.
"""

import time
import os
import uuid
import json
import shutil
# from archive import ArchiveAgent
from log import ABUNDANT_LOGGER
from hash import HashAgent

__author__ = 'Kevin'

VERSION_CONFIG_TEMPLATE = {
    'VersionConfigVersion': 0.1,
    'VersionRecords': []
}

VERSION_RECORD_TEMPLATE = {
    'TimeOfCreation': '',
    'IsBaseVersion': False,
    'UUID': ''
}


class VersionAgent:
    """Actual version agent."""

    def __init__(self, uuid: str, archive_agent):
        """Create the version agent from a version uid.
        :type archive_agent: ArchiveAgent"""
        self.uuid, self.archive_agent = uuid, archive_agent
        self.version_config_path = os.path.join(archive_agent.archive_dir, 'meta', 'version_config.json')
        self.hasher = HashAgent(archive_agent.algorithm)
        self.load_config()

    def load_config(self):
        """Load configuration for this version."""
        with open(self.version_config_path, mode='r', encoding='utf-8') as raw_version_config:
            version_config = json.load(raw_version_config)
            for version in version_config['VersionRecords']:
                if version['UUID'] == self.uuid:
                    self.version_config = version
                    ABUNDANT_LOGGER.debug('Version record found: %s' % self.uuid)
                    return
        ABUNDANT_LOGGER.error('Cannot find config for version %s' % self.uuid)
        raise FileNotFoundError('Cannot find config for version %s' % self.uuid)

    @property
    def is_base_version(self) -> bool:
        """Tell if this version is a base version."""
        return self.version_config['IsBaseVersion']

    @is_base_version.setter
    def is_base_version(self, is_base_version: bool):
        """Set if this version is a base version."""
        with open(self.version_config_path, mode='r', encoding='utf-8') as raw_version_config:
            full_version_config = json.load(raw_version_config)
        for version in full_version_config['VersionRecords']:
            if version['UUID'] == self.uuid:
                version['IsBaseVersion'] = is_base_version
                break
        with open(self.version_config_path, mode='w', encoding='utf-8') as raw_version_config:
            json.dump(full_version_config, raw_version_config)
        if is_base_version:
            ABUNDANT_LOGGER.info('Version %s is now base version' % self.uuid)
        else:
            ABUNDANT_LOGGER.info('Version %s is now non-base version' % self.uuid)

    @property
    def time_of_creation(self):
        """Get the time of creation of this version."""
        return self.version_config['TimeOfCreation']

    @property
    def version_dir(self):
        return os.path.join(self.archive_agent.archive_dir, 'archive', self.uuid)

    def __str__(self):
        return 'Version %s' % self.uuid

    def __eq__(self, other: 'VersionAgent'):
        return self.uuid == other.uuid and self.archive_agent.uuid == other.archive_agent.uuid

    def get_last_version_of_file(self, relative_path: str) -> str:
        """Get the last version of a file."""
        version = self.get_previous_version()
        while version:
            if version.time_of_creation < self.time_of_creation:
                file_of_that_version_full_path = os.path.join(version.version_dir, relative_path)
                if os.path.exists(file_of_that_version_full_path):
                    return file_of_that_version_full_path
            version = version.get_previous_version()
        return None

    def get_previous_version(self) -> 'VersionAgent':
        """Get the previous version."""
        if len(self.archive_agent.versions) == 1:
            return None
        for i in range(0, len(self.archive_agent.versions)):
            if self.archive_agent.versions[i] == self:
                return self.archive_agent.versions[i - 1]

    def migrate_to(self, another_version: 'VersionAgent'):
        """Migrate this version to another version."""
        ABUNDANT_LOGGER.debug('Migrating version %s to %s...' % (self.uuid, another_version.uuid))

        # copy all files from current version to another version
        # unless they already exists
        number_of_file_copied = 0
        for root_dir, dirs, files in os.walk(self.version_dir):
            for file in files:
                relative_dir = root_dir.lstrip(self.version_dir).lstrip('/').lstrip('\\')
                current_version_full_path = os.path.join(self.version_dir, relative_dir, file)
                another_version_full_path = os.path.join(another_version.version_dir, relative_dir, file)
                if not os.path.exists(another_version_full_path):
                    shutil.move(current_version_full_path, another_version_full_path)
                    number_of_file_copied += 1
                    ABUNDANT_LOGGER.debug('Copied %s' % another_version_full_path)
        ABUNDANT_LOGGER.info('Copied %s file%s' % (number_of_file_copied, 's' if number_of_file_copied > 1 else ''))

        # set base version
        if self.is_base_version:
            another_version.is_base_version = True

        # remove this version
        self.remove()

        # refresh status
        another_version.load_config()
        ABUNDANT_LOGGER.info('Migrated %s to %s' % (self.uuid, another_version.uuid))

    def copy_files(self):
        """Copy files from source directory to version directory."""
        ABUNDANT_LOGGER.debug('Copying files...')
        version_dir = os.path.join(self.archive_agent.archive_dir, 'archive', self.uuid)
        if not os.path.exists(version_dir):
            os.mkdir(version_dir)

        # create all directories
        source_dir = self.archive_agent.source_dir
        for root_dir, dirs, files in os.walk(source_dir):
            for dir in dirs:
                relative_dir = os.path.join(root_dir, dir).lstrip(source_dir).lstrip('/').lstrip('\\')
                full_dir = os.path.join(version_dir, relative_dir)
                if not os.path.exists(full_dir):
                    os.mkdir(full_dir)

        # copy new or modified files
        number_of_file_copied = 0
        for root_dir, dirs, files in os.walk(source_dir):
            for file in files:
                relative_path = os.path.join(root_dir, file).lstrip(source_dir).lstrip('/').lstrip('\\')
                full_path = os.path.join(version_dir, relative_path)
                source_path = os.path.join(root_dir, file)
                last_version = self.get_last_version_of_file(relative_path)
                if not self.is_base_version and last_version is not None and self.hasher.hash(last_version) \
                        == self.hasher.hash(source_path):
                    continue
                shutil.copy(source_path, full_path)
                number_of_file_copied += 1
                ABUNDANT_LOGGER.debug('Copied file %s' % full_path)
        ABUNDANT_LOGGER.info('Copied %s file%s' % (number_of_file_copied, 's' if number_of_file_copied > 1 else ''))

    def remove(self):
        """Remove this version."""
        # delete version record
        with open(self.version_config_path, mode='r', encoding='utf-8') as raw_version_config:
            current_version_config = json.load(raw_version_config)
        current_version_record = [version for version in current_version_config['VersionRecords']
                                  if version['UUID'] == self.uuid][0]
        current_version_config['VersionRecords'].remove(current_version_record)
        with open(self.version_config_path, mode='w', encoding='utf-8') as raw_version_config:
            json.dump(current_version_config, raw_version_config)

        # delete directory
        shutil.rmtree(self.version_dir)

        ABUNDANT_LOGGER.info('Removed version %s' % self.uuid)


def create_version(is_base_version: bool, archive_agent) -> VersionAgent:
    """Create a version.
    :type archive_agent: ArchiveAgent"""
    # generate version uuid
    version_uuid = str(uuid.uuid4())
    while archive_agent.get_version(version_uuid):
        version_uuid = str(uuid.uuid4())

    # create version record
    version_record = dict(VERSION_RECORD_TEMPLATE)
    version_record.update({
        'TimeOfCreation': time.time(),
        'IsBaseVersion': is_base_version,
        'UUID': version_uuid
    })
    ABUNDANT_LOGGER.debug('Creating %s version: %s' % ('base' if is_base_version else 'non-base', version_uuid))

    # read current version records
    version_config_path = os.path.join(archive_agent.archive_dir, 'meta', 'version_config.json')
    if not os.path.exists(version_config_path):
        version_config = dict(VERSION_CONFIG_TEMPLATE)
        ABUNDANT_LOGGER.debug('Created version config: %s' % archive_agent.uuid)
    else:
        with open(version_config_path, mode='r', encoding='utf-8') as raw_version_config:
            version_config = json.load(raw_version_config)

    # add version record
    version_config['VersionRecords'].append(version_record)
    with open(version_config_path, mode='w', encoding='utf-8') as raw_version_config:
        json.dump(version_config, raw_version_config)
    ABUNDANT_LOGGER.info('Added version record: %s' % version_uuid)

    # copy files
    version = VersionAgent(version_uuid, archive_agent)
    archive_agent.load_versions()
    version.copy_files()

    ABUNDANT_LOGGER.info('Created %s version %s' % ('base' if is_base_version else 'non-base', version_uuid))
    return version


def get_versions(archive_agent) -> list:
    """Get all versions."""
    version_config_path = os.path.join(archive_agent.archive_dir, 'meta', 'version_config.json')
    if not os.path.exists(version_config_path):
        return list()
    with open(version_config_path, mode='r', encoding='utf-8') \
            as raw_version_config:
        return [VersionAgent(version_record['UUID'], archive_agent) for version_record in
                json.load(raw_version_config)['VersionRecords']]
