#!/usr/env/bin python
# -*- encoding: utf-8 -*-

"""
Hash helper.
"""

import hashlib

import binascii

__author__ = 'Nb'

VALID_ALGORITHMS = ('md5', 'sha1', 'sha256', 'sha512', 'crc32')


def get_hashlib_instance(algorithm: str):
    """Get the hashlib instance for an algorithm.
    No validity check will be performed."""
    return getattr(hashlib, algorithm)()


class CRC32HashlibWrapper:
    """A wrapper to make CRC32 lib behave like hashlib instance."""

    def __init__(self):
        """Create the wrapper."""
        self.hasher = binascii.crc32(b'', 0)

    def update(self, byte: bytes):
        """Feed bytes to the hasher."""
        self.hasher = binascii.crc32(byte, self.hasher)

    def hexdigest(self) -> str:
        """Get the hash value in hex form."""
        return '%08X' % self.hasher


class HashAgent:
    """Hash agent provides a common interface for hash algorithms."""

    def __init__(self, algorithm: str):
        """Create the agent from an algorithm name."""
        algorithm = algorithm.lower()
        if algorithm not in VALID_ALGORITHMS:
            raise NotImplementedError('Requested algorithm is either invalid or has not been implemented yet: %s'
                                      % algorithm)
        self.algorithm = algorithm

    def hash(self, path: str) -> str:
        """Hash a file."""
        if self.algorithm == 'crc32':
            hasher = CRC32HashlibWrapper()
        else:
            hasher = get_hashlib_instance(self.algorithm)

        # feed the data to hasher chuck by chuck
        # and digest the hash
        with open(path, mode='rb') as file:
            chuck = file.read(2048)
            while chuck:
                hasher.update(chuck)
                chuck = file.read(2048)
            return hasher.hexdigest()
