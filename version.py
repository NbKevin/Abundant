#!/usr/env/bin python
# -*- encoding: utf-8 -*-

"""
Agents for various backup versions.
"""

import time
import os
import uuid
import shutil
# from archive import ArchiveAgent
from log import ABUNDANT_LOGGER
from hash import HashAgent
from config import get_config, create_config
from support import get_relative_path

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
        with get_config(self.version_config_path) as version_config:
            for version in version_config['VersionRecords']:
                if version['UUID'] == self.uuid:
                    self.version_config = dict(version)
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
        with get_config(config_path=self.version_config_path, save_change=True) as version_config:
            for version in version_config['VersionRecords']:
                if version['UUID'] == self.uuid:
                    version['IsBaseVersion'] = is_base_version
                    break
        if is_base_version:
            ABUNDANT_LOGGER.info('Version %s is now base version' % self.uuid)
        else:
            ABUNDANT_LOGGER.info('Version %s is now non-base version' % self.uuid)

    @property
    def time_of_creation(self) -> float:
        """Get the time of creation of this version."""
        return self.version_config['TimeOfCreation']

    @property
    def version_dir(self) -> str:
        """Get the directory of this version."""
        return os.path.join(self.archive_agent.archive_dir, 'archive', self.uuid)

    @property
    def _base_version(self) -> 'VersionAgent':
        """Get the base version of the archive this version is in."""
        return self.archive_agent.base_version

    @property
    def exact_files(self):
        """Generator for files in the directory of this version."""
        for root_dir, dirs, files in os.walk(self.version_dir):
            for file in files:
                absolute_path = os.path.join(root_dir, file)
                relative_path = self._get_relative_path_of_file(absolute_path)
                yield relative_path, absolute_path

    @property
    def files(self):
        """Generator for all files in this version."""
        base_version = self.archive_agent.base_version

        # find the currently effective version for all files existing since base version
        for root_dir, dirs, files in os.walk(base_version.version_dir):
            for file in files:
                effective_absolute_path = os.path.join(root_dir, file)
                relative_path = base_version._get_relative_path_of_file(effective_absolute_path)

                # find last appearance of this file
                last_appearance_version = base_version._get_last_appearance_of_file(relative_path)
                yield relative_path, last_appearance_version._get_full_path_of_file(relative_path)

        # find all files that was added after the base version
        version_in_work = self
        while version_in_work and version_in_work != base_version:
            for root_dir, dirs, files in os.walk(version_in_work.version_dir):
                for file in files:
                    absolute_path = os.path.join(root_dir, file)
                    relative_path = version_in_work._get_relative_path_of_file(absolute_path)

                    # if file exists in base version than ignore it
                    if base_version.has_file(relative_path):
                        continue

                    # otherwise find the last appearance of that file
                    # and yield it if that version is current version
                    last_appearance_version = version_in_work._get_last_appearance_of_file(relative_path)
                    if last_appearance_version == version_in_work:
                        yield relative_path, version_in_work._get_full_path_of_file(relative_path)
            version_in_work = version_in_work.previous_version

    def __str__(self):
        return 'Version %s' % self.uuid

    def __repr__(self):
        return self.__str__()

    def __eq__(self, other: 'VersionAgent'):
        return self.uuid == other.uuid and self.archive_agent.uuid == other.archive_agent.uuid

    def __gt__(self, other: 'VersionAgent'):
        return self.time_of_creation > other.time_of_creation

    def __lt__(self, other: 'VersionAgent'):
        return self.time_of_creation < other.time_of_creation

    def __ge__(self, other: 'VersionAgent'):
        return self.time_of_creation >= other.time_of_creation

    def __le__(self, other: 'VersionAgent'):
        return self.time_of_creation <= other.time_of_creation

    def has_file(self, relative_path: str) -> bool:
        """Tell if this version contains a file."""
        return os.path.exists(self._get_full_path_of_file(relative_path))

    def _get_full_path_of_file(self, relative_path: str) -> str:
        """Get the full path of a file."""
        return os.path.join(self.version_dir, relative_path)

    def _get_relative_path_of_file(self, absolute_path: str) -> str:
        """Get the relative path of a file."""
        return absolute_path.replace(self.version_dir, '', 1).lstrip('/').lstrip('\\')

    def _get_previous_version_of_file(self, relative_path: str, from_version=None, until_version=None):
        """Get the last version of a file."""
        version_candidate = self.previous_version
        while version_candidate:
            if from_version and version_candidate > from_version:
                continue
            full_path_in_that_version = version_candidate._get_full_path_of_file(relative_path)
            if os.path.exists(full_path_in_that_version):
                return version_candidate
            version_candidate = version_candidate.previous_version
            if until_version and version_candidate < until_version:
                break
        return None

    def _get_first_appearance_of_file(self, relative_path: str):
        """Get the first appearance of a file.
        File must exist in current version."""
        assert self.has_file(relative_path)
        version = version_candidate = self
        while version:
            if version.has_file(relative_path):
                version_candidate = version
            version = version.previous_version
        return version_candidate

    def _get_last_appearance_of_file(self, relative_path: str):
        """Get the last appearance of a file.
        File must exist in current version."""
        assert self.has_file(relative_path)
        version = version_candidate = self
        while version:
            if version.has_file(relative_path):
                version_candidate = version
            version = version.next_version
        return version_candidate

    def _get_next_version_of_file(self, relative_path: str, from_version=None, until_version=None):
        """Get next version of a file."""
        version_candidate = self.next_version
        while version_candidate:
            if from_version and version_candidate < from_version:
                continue
            full_path_in_that_version = version_candidate._get_full_path_of_file(relative_path)
            if os.path.exists(full_path_in_that_version):
                return version_candidate
            if until_version and version_candidate > until_version:
                break
            version_candidate = version_candidate.next_version
        return None

    @property
    def previous_version(self) -> 'VersionAgent':
        """Get the previous version."""
        if len(self.archive_agent.versions) == 1 or self.archive_agent.base_version == self:
            return None
        for i in range(0, len(self.archive_agent.versions)):
            if self.archive_agent.versions[i] == self:
                return self.archive_agent.versions[i - 1]

    @property
    def next_version(self) -> 'VersionAgent':
        """Get the next version."""
        if len(self.archive_agent.versions) == 1:
            return None
        for i in range(0, len(self.archive_agent.versions) - 1):
            if self.archive_agent.versions[i] == self:
                return self.archive_agent.versions[i + 1]
        return None

    def migrate_to_next_version(self):
        """Migrate this version to its next version."""
        next_version = self.next_version
        ABUNDANT_LOGGER.debug('Migrating version %s to %s...' % (self.uuid, next_version.uuid))

        # copy all files from current version to another version
        # unless they already exists
        number_of_file_copied = 0
        for relative_path, absolute_path in self.exact_files:
            if not next_version.has_file(relative_path):
                absolute_path_in_another_version = next_version._get_full_path_of_file(relative_path)
                shutil.move(absolute_path, absolute_path_in_another_version)
                number_of_file_copied += 1
                ABUNDANT_LOGGER.debug('Copied %s' % absolute_path_in_another_version)
        ABUNDANT_LOGGER.info('Copied %s file(s)' % number_of_file_copied)

        # set base version
        if self.is_base_version:
            next_version.is_base_version = True

        # remove this version
        self.remove(base_version_pardon=True)

        # refresh status
        next_version.load_config()
        ABUNDANT_LOGGER.info('Migrated %s to %s' % (self.uuid, next_version.uuid))

    def copy_files(self):
        """Copy files from source directory to version directory."""
        ABUNDANT_LOGGER.debug('Copying files...')

        # copy new or modified files
        source_dir = self.archive_agent.source_dir
        number_of_file_copied = 0
        for root_dir, dirs, files in os.walk(source_dir):
            for dir in dirs:
                absolute_dir = os.path.join(root_dir, dir)
                relative_dir = get_relative_path(absolute_dir, source_dir)
                os.makedirs(self._get_full_path_of_file(relative_dir), exist_ok=True)
            for file in files:
                source_absolute_path = os.path.join(root_dir, file)
                relative_path = get_relative_path(source_absolute_path, source_dir)

                # find the previous version of this file
                previous_version = self._get_previous_version_of_file(relative_path)

                # under following circumstances file will be treated
                # as already existing in previous versions and will
                # not be copied
                # if this is not a base version
                # and if there is a previous version for this file
                # and if that previous version is identical to current one
                if not self.is_base_version \
                        and previous_version is not None \
                        and self.hasher.hash(previous_version._get_full_path_of_file(relative_path)) \
                                == self.hasher.hash(source_absolute_path):
                    ABUNDANT_LOGGER.debug('Skipping %s' % source_absolute_path)
                    continue

                # otherwise just copy the file
                shutil.copy(source_absolute_path, self._get_full_path_of_file(relative_path))
                number_of_file_copied += 1
                ABUNDANT_LOGGER.debug('Copied file %s' % relative_path)
        ABUNDANT_LOGGER.info('Copied %s file(s)' % number_of_file_copied)

    def remove(self, base_version_pardon=False):
        """Remove this version."""
        if not base_version_pardon and self.is_base_version:
            raise PermissionError('Base version cannot be removed')

        # delete version record
        with get_config(self.version_config_path, save_change=True) as version_config:
            current_version_record = [version for version in version_config['VersionRecords']
                                      if version['UUID'] == self.uuid][0]
            version_config['VersionRecords'].remove(current_version_record)

        # delete directory
        shutil.rmtree(self.version_dir)

        # update version records
        self.archive_agent.load_versions()

        ABUNDANT_LOGGER.info('Removed version %s' % self.uuid)

    def export(self, destination_dir: str, exact=False):
        """Export files in this version to destination directory."""
        ABUNDANT_LOGGER.debug('Exporting version %s to %s' % (self.uuid, destination_dir))

        if not os.path.exists(destination_dir):
            ABUNDANT_LOGGER.error('Cannot find destination directory: %s' % destination_dir)
            raise FileNotFoundError('Cannot find destination directory: %s' % destination_dir)

        file_source = self.files if not exact else self.exact_files
        for relative_path, absolute_path in file_source:
            destination_path = os.path.join(destination_dir, relative_path)
            os.makedirs(os.path.dirname(destination_path), exist_ok=True)
            shutil.copy(absolute_path, destination_path)
            ABUNDANT_LOGGER.debug('Copied %s' % destination_path)
        ABUNDANT_LOGGER.info('Exported version %s to %s' % (self.uuid, destination_dir))


def create_version(is_base_version: bool, archive_agent) -> VersionAgent:
    """Create a version.
    :type archive_agent: ArchiveAgent"""
    # generate version uuid
    version_uuid = str(uuid.uuid4())
    while archive_agent.get_version(version_uuid):
        version_uuid = str(uuid.uuid4())

    # prepare version record
    version_record = dict(VERSION_RECORD_TEMPLATE)
    version_record.update({
        'TimeOfCreation': time.time(),
        'IsBaseVersion': is_base_version,
        'UUID': version_uuid
    })
    ABUNDANT_LOGGER.debug('Creating %s version: %s' % ('base' if is_base_version else 'non-base', version_uuid))

    # create version config if no version is present
    version_config_path = os.path.join(archive_agent.archive_dir, 'meta', 'version_config.json')
    if not os.path.exists(version_config_path):
        create_config(VERSION_CONFIG_TEMPLATE, version_config_path)
        ABUNDANT_LOGGER.debug('Created version config: %s' % archive_agent.uuid)

    # add version record
    with get_config(version_config_path, save_change=True) as version_config:
        version_config['VersionRecords'].append(version_record)
    archive_agent.load_versions()
    ABUNDANT_LOGGER.info('Added version record: %s' % version_uuid)

    # create version directory and copy files
    version = archive_agent.get_version(version_uuid)
    if not os.path.exists(version.version_dir):
        os.mkdir(version.version_dir)
    version.copy_files()

    ABUNDANT_LOGGER.info('Created %s version %s' % ('base' if is_base_version else 'non-base', version_uuid))
    return version


def get_versions(archive_agent) -> list:
    """Get all versions."""
    version_config_path = os.path.join(archive_agent.archive_dir, 'meta', 'version_config.json')
    if not os.path.exists(version_config_path):
        ABUNDANT_LOGGER.warning('Version config missing')
        return list()

    with get_config(version_config_path) as version_config:
        return [VersionAgent(version_record['UUID'], archive_agent) for version_record in
                version_config['VersionRecords']]
