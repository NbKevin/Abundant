#!/usr/env/bin python
# -*- encoding: utf-8 -*-

"""
Archive agent.
"""

import os
import json
import shutil

from version import VersionAgent, create_version, get_versions
from log import ABUNDANT_LOGGER

__author__ = 'Kevin'

ARCHIVE_CONFIG_TEMPLATE = {
    'ArchiveConfigVersion': 0.1,
    'SourceDirectory': '',
    'HashAlgorithm': '',
    'MaxNumberOfVersions': 1,
    'UUID': ''
}


class ArchiveAgent:
    """Archive agent is responsible for a single archive."""

    def __init__(self, archive_dir: str):
        """Create the agent from an archive directory."""
        self.archive_dir = archive_dir
        self.archive_config_path = os.path.join(self.archive_dir, 'meta', 'archive_config.json')
        self.versions = []
        self.load_config()
        self.load_versions()

    def load_versions(self):
        """Load all versions in this archive."""
        self.versions = get_versions(self)
        self.versions.sort(key=lambda x: x.time_of_creation)
        self.validate_versions()
        number_of_versions = len(self.versions)
        ABUNDANT_LOGGER.debug('Found %s version%s' % (number_of_versions, 's' if number_of_versions > 1 else ''))

    def load_config(self):
        """Load archive configurations."""
        if not os.path.exists(self.archive_config_path):
            ABUNDANT_LOGGER.error('Archive config not found at %s' % self.archive_config_path)
            raise FileNotFoundError('Archive config not found at %s' % self.archive_config_path)

        with open(self.archive_config_path, mode='r', encoding='utf-8') as raw_archive_config:
            self.archive_config = json.load(raw_archive_config)
        ABUNDANT_LOGGER.debug('Loaded archive config')

    def validate_versions(self):
        """Validate versions."""
        # make sure only one base version exists
        # and versions are sorted from oldest to latest
        found_base_version = False
        previous_version = None
        for version in self.versions:
            if version.is_base_version:
                if found_base_version:
                    return False
                found_base_version = True
            if previous_version:
                if version < previous_version:
                    return False
        return True

    def get_version(self, uuid: str):
        """Get version with a given UUID."""
        for version in self.versions:
            if version.uuid == uuid:
                return version
        return None

    def __str__(self):
        return 'Archive %s from %s to %s' % (self.uuid, self.source_dir, self.archive_dir)

    def __repr__(self):
        return 'Archive %s' % self.uuid

    @property
    def algorithm(self) -> str:
        """Get the hash algorithm used for this archive."""
        return self.archive_config['HashAlgorithm']

    @property
    def source_dir(self) -> str:
        """Get the source directory."""
        return self.archive_config['SourceDirectory']

    @property
    def uuid(self) -> str:
        """Get the UUID of the archive."""
        return self.archive_config['UUID']

    @property
    def max_number_of_versions(self):
        return self.archive_config['MaxNumberOfVersions']

    @property
    def base_version(self) -> VersionAgent:
        """Get the base version in this archive."""
        return self.versions[0]

    @property
    def last_version(self) -> VersionAgent:
        """Get the last version in this archive."""
        return self.versions[-1]

    def create_base(self) -> VersionAgent:
        """Create the base version."""
        if self.base_version is None:
            create_version(True, self)
        else:
            ABUNDANT_LOGGER.warning('Cannot create duplicate base versions')
        self.load_versions()
        return self.base_version

    def create_version(self) -> VersionAgent:
        """Add a new version."""
        if self.max_number_of_versions == 1:
            self.base_version.remove()
            self.create_base()
        else:
            while len(self.versions) >= self.max_number_of_versions:
                self.migrate_oldest_version_to_base()
            if self.base_version is None:
                ABUNDANT_LOGGER.warning('Cannot create non-base versions without a base version')
            else:
                create_version(False, self)
        self.load_versions()
        return self.versions[-1]

    def migrate_oldest_version_to_base(self):
        """Migrate the oldest version to the base version.
        But underneath it migrate the base version to the oldest version."""
        assert self.base_version == self.versions[0]
        if not self.versions:
            ABUNDANT_LOGGER.warning('No base version found')
        elif len(self.versions) == 1:
            ABUNDANT_LOGGER.warning('Cannot migrate when only base version exists')
        else:
            self.base_version.migrate_to_next_version()
            self.load_versions()

    def migrate_all_versions_to_base(self):
        """Migrate all versions to the base."""
        assert self.base_version == self.versions[0]
        while len(self.versions) > 1:
            self.base_version.migrate_to_next_version()
            self.load_versions()

    def remove(self):
        """Remove the archive."""
        shutil.rmtree(self.archive_dir)


def create_archive(archive_record: dict, algorithm: str, max_number_of_versions: int) -> ArchiveAgent:
    """Create an archive according to the archive record.
    No validity check will be performed."""
    source_dir, archive_dir = archive_record['SourceDirectory'], archive_record['ArchiveDirectory']
    uuid = archive_record['UUID']
    archive_content_dir = os.path.join(archive_dir, 'archive')
    archive_meta_dir = os.path.join(archive_dir, 'meta')
    ABUNDANT_LOGGER.debug('Creating archive: %s' % uuid)

    try:
        # create archive and meta directories
        os.mkdir(archive_content_dir)
        os.mkdir(archive_meta_dir)

        # set archive config
        archive_config = dict(ARCHIVE_CONFIG_TEMPLATE)
        archive_config.update({
            'HashAlgorithm': algorithm,
            'SourceDirectory': source_dir,
            'MaxNumberOfVersions': max_number_of_versions,
            'UUID': uuid
        })
        with open(os.path.join(archive_meta_dir, 'archive_config.json'), mode='w', encoding='utf-8') \
                as raw_archive_config:
            json.dump(archive_config, raw_archive_config)
        ABUNDANT_LOGGER.debug('Created archive config: %s' % uuid)

    except OSError as e:
        # OSError on file operations usually indicates insufficient privilege or
        # incorrect configurations
        ABUNDANT_LOGGER.error('Cannot create archive %s, possibly caused by insufficient privilege' %
                              uuid)

        # undo previous change
        if os.path.exists(archive_content_dir):
            os.rmdir(archive_content_dir)
        if os.path.exists(archive_meta_dir):
            os.rmdir(archive_meta_dir)
        ABUNDANT_LOGGER.info('Previous change undone')

        # raise
        raise e
    else:
        ABUNDANT_LOGGER.info('Created archive: %s' % uuid)
        return ArchiveAgent(archive_dir)
