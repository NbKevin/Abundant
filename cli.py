#!/usr/env/bin python
# -*- encoding: utf-8 -*-

"""
Command line interface for abundant.
"""

from log import ABUNDANT_LOGGER, ABUNDANT_LOG_STD_OUT_HANDLER

ABUNDANT_LOGGER.info('Starting command line interface...')
ABUNDANT_LOGGER.removeHandler(ABUNDANT_LOG_STD_OUT_HANDLER)
from abundant import Abundant

__author__ = 'Kevin'


class CLICommandError(Exception):
    """CLI command error, either caused by incorrect parameter
    or syntax."""

    def __init__(self, message: str):
        self.message = message
        super(CLICommandError, self).__init__(message)


WELCOME_MESSAGE = '\nCommand line interface for Abundant, version 0.3'

LIST_ARCHIVE_FORMAT = '''
Number: {0}
UUID: {1}
Source directory: {2}
Archive directory: {3}'''

LIST_VERSION_FORMAT = '''
Number: {0}
UUID: {1}
Archive UUID: {2}
Time of creation: {3}
Base version: {4}'''

DETAIL_ARCHIVE_FORMAT = '''
ARCHIVE
UUID: {0}
Source directory: {1}
Archive directory: {2}
Max number of versions: {3}
Hash algorithm: {4}'''

DETAIL_VERSION_FORMAT = '''
VERSION
UUID: {0}
Archive UUID: {1}
Time of creation: {2}
Base version: {3}'''

CREATE_ARCHIVE_FORMAT = '''Creating archive:

Source directory: {0}
Archive directory: {1}
Hash algorithm: {2}
Max number of versions: {3}

Proceed? '''

CREATE_VERSION_FORMAT = '''Creating version:

For archive: {0}

Proceed? '''

REMOVE_ARCHIVE_FORMAT = '''Removing archive:

UUID: {0}
Source directory: {1}
Archive directory: {2}
Max number of versions: {3}
Hash algorithm: {4}

Proceed? '''

REMOVE_VERSION_FORMAT = '''Removing version:

UUID: {0}
Archive UUID: {1}
Time of creation: {2}
Base version: {3}

Proceed? '''

MIGRATE_ALL_FORMAT = '''Migrating all versions in archive:

UUID: {0}
Source directory: {1}
Archive directory: {2}
Hash algorithm: {3}
Max number of versions: {4}

to version:

UUID {5}
Time of creation: {6}
Base version: {7}

{8} version(s) will be migrated and then removed

Proceed? '''

MIGRATE_SOME_FORMAT = '''Migrating {0} version(s) in archive:

UUID: {1}
Source directory: {2}
Archive directory: {3}
Hash algorithm: {4}
Max number of versions: {5}

to version:

UUID {6}
Time of creation: {7}
Base version: {8}

{9} version(s) will be migrated and then removed

Proceed? '''

EXPORT_FORMAT = '''Exporting version:

UUID {0}
Time of creation: {1}
Base version: {2}

to directory:

{3}

Proceed? '''

EXPORT_EXACT_FORMAT = '''Exporting version:

UUID {0}
Time of creation: {1}
Base version: {2}

exactly to directory:

{3}

Proceed? '''


# noinspection PyMethodMayBeStatic
class CLI:
    """Command line interface fir abundant."""

    def __init__(self):
        """Create the command line interface."""
        self.archive_selected = self.version_selected = None
        """:type archive_selected: ArchiveAgent
        :type version_selected: VersionAgent"""
        self.archives = Abundant.get_all_archives()
        self.VERB_TO_FUNCTION = {
            'list': self.list,
            'list-exact': self.list_exact,
            'select': self.select,
            'detail': self.detail,
            'quit': self.quit,
            'create': self.create,
            'remove': self.remove,
            'migrate': self.migrate,
            'export': self.export,
            'export-exact': self.export_exact
        }

    def loop(self):
        """Main loop of the CLI."""
        print(WELCOME_MESSAGE)
        while True:
            raw_command = input('\nAbundant> ')
            self.evaluate(raw_command)
            self.validate_selected_archive_and_version()

    def validate_selected_archive_and_version(self):
        """Make sure selected archive and version are valid."""
        if self.archive_selected is None:
            self.version_selected = None
        else:
            all_archives = Abundant.get_all_archives()
            found_match = False
            for archive in all_archives:
                if archive['UUID'] == self.archive_selected.uuid:
                    found_match = True
            if not found_match:
                self.archive_selected = None
            else:
                if self.version_selected is not None:
                    found_match = False
                    for version in self.archive_selected.versions:
                        if version == self.version_selected:
                            found_match = True
                    if not found_match:
                        self.version_selected = None

    def evaluate(self, raw_command: str):
        """Evaluate the raw command."""
        commands = raw_command.split()
        try:
            if not commands:
                return
            verb = commands[0]
            if verb not in self.VERB_TO_FUNCTION:
                raise CLICommandError('Unknown command')
            if len(commands) == 1 and verb != 'quit':
                raise CLICommandError('Missing command parameter')
            self.VERB_TO_FUNCTION[verb](*commands[1:])
        except Exception as e:
            print('Error: %s' % e)

    def quit(self, *args):
        """Quit command."""
        raise SystemExit(0)

    def list(self, target: str, *args):
        """List command."""
        if target not in ['archive', 'version', 'file']:
            raise CLICommandError('Unknown list target')
        if target == 'archive':
            if self.archives:
                counter = 0
                for archive in self.archives:
                    print(LIST_ARCHIVE_FORMAT.format(
                        counter, archive['UUID'],
                        archive['SourceDirectory'],
                        archive['ArchiveDirectory']
                    ))
                    counter += 1
            else:
                print('No available archive')
        elif target == 'version':
            if self.archive_selected is None:
                raise CLICommandError('No archive selected')
            elif self.archive_selected:
                counter = 0
                for version in self.archive_selected.versions:
                    print(LIST_VERSION_FORMAT.format
                          (counter, version.uuid,
                           version.archive_agent.uuid,
                           version.time_of_creation,
                           version.is_base_version))
                    counter += 1
            else:
                print('No available versions')
        elif target == 'file':
            if self.version_selected is None:
                raise CLICommandError('No version selected')
            counter = 0
            print('Listing file in version %s:\n' % self.version_selected.uuid)
            for relative_path, absolute_path in self.version_selected.files:
                counter += 1
                print(absolute_path)
            print('\n%s file(s) in version %s' % (counter, self.version_selected.uuid))

    def list_exact(self, target: str, *args):
        """List exact command."""
        if target != 'file':
            raise CLICommandError('Unknown list-exact target')
        if self.version_selected is None:
            raise CLICommandError('No version selected')
        counter = 0
        print('Listing file exactly in version %s:\n' % self.version_selected.uuid)
        for relative_path, absolute_path in self.version_selected.exact_files:
            counter += 1
            print(absolute_path)
        print('\nExactly %s file(s) in version %s' % (counter, self.version_selected.uuid))

    def select(self, target: str, index: str, *args):
        """Select command."""
        if target not in ['archive', 'version']:
            raise CLICommandError('Unknown select target')
        try:
            index = int(index)
        except ValueError:  # which indicates that index is not an integer
            raise CLICommandError('Invalid select index')
        if target == 'archive':
            if not self.archives:
                raise CLICommandError('No available archive to be selected')
            if index >= len(self.archives):
                raise CLICommandError('Invalid select index')
            self.archive_selected = Abundant.get_archive(uuid=self.archives[index]['UUID'])
            print('Selected archive %s\nUUID: %s' % (index, self.archive_selected.uuid))
        elif target == 'version':
            if self.archive_selected is None:
                raise CLICommandError('No archive selected')
            if not self.archive_selected.versions:
                raise CLICommandError('No available version to be selected')
            if index > len(self.archive_selected.versions):
                raise CLICommandError('Invalid select index')
            self.version_selected = self.archive_selected.versions[index]
            print('Selected version %s\nUUID: %s' % (index, self.version_selected.uuid))

    def detail(self, target: str, *args):
        """Detail command."""
        if target not in ['archive', 'version']:
            raise CLICommandError('Unknown detail target')
        if target == 'archive':
            if not self.archive_selected:
                raise CLICommandError('No archive selected')
            print(DETAIL_ARCHIVE_FORMAT.format
                  (self.archive_selected.uuid, self.archive_selected.source_dir,
                   self.archive_selected.archive_dir,
                   self.archive_selected.max_number_of_versions,
                   self.archive_selected.algorithm))
        elif target == 'version':
            if not self.version_selected:
                raise CLICommandError('No version selected')
            print(DETAIL_VERSION_FORMAT.format
                  (self.version_selected.uuid,
                   self.version_selected.archive_agent.uuid,
                   self.version_selected.time_of_creation,
                   self.version_selected.is_base_version))

    def create(self, target: str, *args, **kwargs):
        """Create command."""
        if target not in ['archive', 'version']:
            raise CLICommandError('Unknown create target')
        if target == 'archive':
            if len(args) != 4:
                raise CLICommandError('Incorrect archive parameter')
            try:
                int(args[3])
            except ValueError:
                raise CLICommandError('Invalid max number of versions')
            if input(CREATE_ARCHIVE_FORMAT.format(
                    args[0], args[1],
                    args[2], args[3]
            )).lower() == 'y':
                archive = Abundant.create_archive(args[0], args[1], args[2], int(args[3]))
                print('Created archive %s' % archive.uuid)
        elif target == 'version':
            if len(args) != 0:
                raise CLICommandError('Unknown parameter')
            if self.archive_selected is None:
                raise CLICommandError('No archive selected')
            if input(CREATE_VERSION_FORMAT.format(self.archive_selected)).lower() == 'y':
                version = self.archive_selected.create_version()
                print('Created version %s' % version.uuid)

    def remove(self, target: str, *args):
        """Remove command."""
        if target not in ['archive', 'version']:
            raise CLICommandError('Unknown create target')
        if target == 'archive':
            if self.archive_selected is None:
                raise CLICommandError('No archive selected')
            archive_uuid = self.archive_selected.uuid
            if input(REMOVE_ARCHIVE_FORMAT.format(
                    self.archive_selected.uuid,
                    self.archive_selected.source_dir,
                    self.archive_selected.archive_dir,
                    self.archive_selected.max_number_of_versions,
                    self.archive_selected.algorithm
            )).lower() == 'y':
                Abundant.remove_archive(uuid=self.archive_selected.uuid)
                self.archive_selected = None
                print('Removed archive %s' % archive_uuid)
        elif target == 'version':
            if self.version_selected is None:
                raise CLICommandError('No version selected')
            version_uuid = self.version_selected.uuid
            if input(REMOVE_VERSION_FORMAT.format(
                    self.version_selected.uuid,
                    self.version_selected.archive_agent.uuid,
                    self.version_selected.time_of_creation,
                    self.version_selected.is_base_version
            )).lower() == 'y':
                self.version_selected.remove()
                self.version_selected = None
                print('Removed version %s' % version_uuid)

    def migrate(self, number_of_archives_to_be_removed_or_all: str, *args):
        """Migrate command."""
        if number_of_archives_to_be_removed_or_all != 'all':
            try:
                int(number_of_archives_to_be_removed_or_all)
            except ValueError:
                raise CLICommandError('Migrate only accepts positive integer or all')
        if self.archive_selected is None:
            raise CLICommandError('No archive selected')
        if number_of_archives_to_be_removed_or_all == 'all':
            last_version = self.archive_selected.last_version
            if input(MIGRATE_ALL_FORMAT.format(
                    self.archive_selected.uuid,
                    self.archive_selected.source_dir,
                    self.archive_selected.archive_dir,
                    self.archive_selected.algorithm,
                    self.archive_selected.max_number_of_versions,
                    last_version.uuid,
                    last_version.time_of_creation,
                    last_version.is_base_version,
                            len(self.archive_selected.versions) - 1
            )) == 'y':
                self.archive_selected.migrate_all_versions_to_base()
                print('Migrated all versions')
        else:
            number_of_archives_to_be_removed_or_all = int(number_of_archives_to_be_removed_or_all)
            if number_of_archives_to_be_removed_or_all < 0:
                raise CLICommandError('Cannot migrate negative number of versions')
            elif number_of_archives_to_be_removed_or_all >= len(self.archive_selected.archive_config):
                raise CLICommandError('Cannot migrate more versions than current present ones')
            version = self.archive_selected.versions[
                -(len(self.archive_selected.versions) - number_of_archives_to_be_removed_or_all)]
            if input(MIGRATE_SOME_FORMAT.format(
                    number_of_archives_to_be_removed_or_all,
                    self.archive_selected.uuid,
                    self.archive_selected.source_dir,
                    self.archive_selected.archive_dir,
                    self.archive_selected.algorithm,
                    self.archive_selected.max_number_of_versions,
                    version.uuid,
                    version.time_of_creation,
                    version.is_base_version,
                    number_of_archives_to_be_removed_or_all
            )) == 'y':
                for i in range(number_of_archives_to_be_removed_or_all):
                    self.archive_selected.migrate_oldest_version_to_base()
                print('Migrated %s version(s)' % number_of_archives_to_be_removed_or_all)

    def export(self, destination_dir: str, *args):
        """Export command."""
        if self.version_selected is None:
            raise CLICommandError('No version selected')
        if input(EXPORT_FORMAT.format(
                self.version_selected.uuid,
                self.version_selected.time_of_creation,
                self.version_selected.is_base_version,
                destination_dir
        )) == 'y':
            self.version_selected.export(destination_dir)
            print('Exported version %s to %s' % (self.version_selected.uuid, destination_dir))

    def export_exact(self, destination_dir: str, *args):
        """Export command."""
        if self.version_selected is None:
            raise CLICommandError('No version selected')
        if input(EXPORT_EXACT_FORMAT.format(
                self.version_selected.uuid,
                self.version_selected.time_of_creation,
                self.version_selected.is_base_version,
                destination_dir
        )) == 'y':
            self.version_selected.export(destination_dir, exact=True)
            print('Exported version %s exactly to %s' % (self.version_selected.uuid, destination_dir))


if __name__ == '__main__':
    CLI().loop()
