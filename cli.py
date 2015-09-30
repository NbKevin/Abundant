#!/usr/env/bin python
# -*- encoding: utf-8 -*-

"""
Command line interface for abundant.
"""

from log import ABUNDANT_LOGGER, ABUNDANT_LOG_STD_OUT_HANDLER

ABUNDANT_LOGGER.removeHandler(ABUNDANT_LOG_STD_OUT_HANDLER)
from abundant import Abundant

__author__ = 'Kevin'


def cli():
    """Main loop for CLI."""
    archive_selected = version_selected = None
    archives = Abundant.get_all_archives()
    print('\nCommand line interface for Abundant, version 0.1')
    while True:
        try:
            raw_command = input('\n$ ')
            commands = raw_command.split()
            if commands[0] == 'quit':
                break
            elif commands[0] == 'list':
                if commands[1] == 'archive':
                    archives = Abundant.get_all_archives()
                    counter = 0
                    for archive in archives:
                        print('''
    Number: %s
    UUID: %s
    Source directory: %s
    Archive directory: %s''' % (counter, archive['UUID'], archive['SourceDirectory'], archive['ArchiveDirectory']))
                        counter += 1
                elif commands[1] == 'version':
                    if archive_selected:
                        counter = 0
                        for version in archive_selected.versions:
                            print('''
    Number: %s
    UUID: %s
    Archive UUID: %s
    Time of creation: %s''' % (counter, version.uuid, archive_selected.uuid, version.time_of_creation))
                            counter += 1
                    else:
                        print('Unknown command')
                else:
                    print('Unknown command')
            elif commands[0] == 'select':
                if commands[1] == 'archive':
                    archive_selected = Abundant.get_archive(uuid=archives[int(commands[2])]['UUID'])
                    print('Selected archive %s' % commands[2])
                elif commands[1] == 'version':
                    version_selected = archive_selected.versions[int(commands[2])]
                    print('Selected version %s' % commands[2])
                else:
                    print('Unknown command')
            elif commands[0] == 'detail':
                if commands[1] == 'archive':
                    print('''
    ARCHIVE
    UUID: %s
    Source directory: %s
    Archive directory: %s
    Maximum number of versions: %s
    Hash algorithm: %s''' % (archive_selected.uuid, archive_selected.source_dir, archive_selected.archive_dir,
                             archive_selected.maximum_number_of_versions, archive_selected.algorithm))
                elif commands[1] == 'version':
                    print('''
    VERSION
    UUID: %s
    Archive UUID: %s
    Time of creation: %s''' % (version_selected.uuid, version_selected.archive_agent.uuid,
                               version_selected.time_of_creation))
                else:
                    print('Unknown command')
            else:
                print('Unknown command')
        except (KeyError, IndexError):
            print('Unknown command')


if __name__ == '__main__':
    cli()
