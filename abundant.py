#!/usr/env/bin python
# -*- encoding: utf-8 -*-

"""
Main loader.
"""

import os

from config import MasterConfigAgent
from archive import create_archive, ArchiveAgent
from log import ABUNDANT_LOGGER
from hash import VALID_ALGORITHMS

__author__ = 'Kevin'


class AbundantAgent:
    """Abundant provides a universal interface for backup operations."""

    def __init__(self):
        """Create the abundant."""
        self.master_config = MasterConfigAgent()

    def create_archive(self, source_dir: str, archive_dir: str, algorithm: str, max_number_of_versions: int):
        """Create an archive."""
        # validity check
        if not os.path.exists(source_dir):
            ABUNDANT_LOGGER.error('Source directory does not exist: %s' % source_dir)
            raise FileNotFoundError('Source directory does not exist: %s' % source_dir)
        if not os.path.exists(archive_dir):
            ABUNDANT_LOGGER.error('Archive directory does not exist: %s' % archive_dir)
            raise FileNotFoundError('Archive directory does not exist: %s' % archive_dir)
        if self.master_config.get_archive_record(archive_dir=archive_dir):
            ABUNDANT_LOGGER.error('Archive directory has already been used: %s' % archive_dir)
            raise FileNotFoundError('Archive directory has already been used: %s' % archive_dir)
        algorithm = algorithm.lower()
        if algorithm not in VALID_ALGORITHMS:
            ABUNDANT_LOGGER.error('Invalid hash algorithm: %s' % algorithm)
            raise NotImplementedError('Requested algorithm is either invalid or has not been implemented yet: %s'
                                      % algorithm)
        if max_number_of_versions < 0:
            ABUNDANT_LOGGER.error('At least one version should be kept: %s' % max_number_of_versions)
            raise ValueError('At least one version should be kept: %s' % max_number_of_versions)

        # create archive record
        new_archive_record = self.master_config.add_archive_record(source_dir, archive_dir)

        # create archive
        try:
            archive = create_archive(new_archive_record, algorithm, max_number_of_versions)
        except OSError as e:
            # delete the archive record previously created
            self.master_config.remove_archive_record(uuid=new_archive_record['UUID'])
            ABUNDANT_LOGGER.debug('Archive record added removed')

            raise e

        # create base version
        archive.create_base()
        ABUNDANT_LOGGER.info('Created archive %s' % archive.uuid)
        return archive

    def get_archive(self, uuid=None, source_dir=None, archive_dir=None) -> ArchiveAgent:
        """Get the archive that matches given restraints."""
        if uuid is None and source_dir is None and archive_dir is None:
            ABUNDANT_LOGGER.warning('Must provide at least one restraint')
            raise ValueError('Must provide at least one restraint')

        archive_record = self.master_config.get_archive_record(uuid, source_dir, archive_dir)
        if archive_record is None:
            return archive_record
        return ArchiveAgent(archive_record['ArchiveDirectory'])

    def get_all_archives(self):
        """Get all available archives."""
        return self.master_config['ArchiveRecords']

    def remove_archive(self, uuid=None, source_dir=None, archive_dir=None):
        """Remove an archive."""
        archive = self.get_archive(uuid, source_dir, archive_dir)
        archive.remove()
        self.master_config.remove_archive_record(uuid)


Abundant = AbundantAgent()
