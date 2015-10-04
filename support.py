#!/usr/env/bin python
# -*- encoding: utf-8 -*-

"""
Supportive matters.
"""

__author__ = 'Kevin'


class SingletonMeta(type):
    """Meta class for creating singleton class."""
    __instance_dict = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls.__instance_dict:
            cls.__instance_dict[cls] = super(SingletonMeta, cls).__call__(*args, **kwargs)
        return cls.__instance_dict[cls]


def get_relative_path(absolute_path: str, root_dir: str) -> str:
    """Get the relative path of an absolute path to a root directory."""
    return absolute_path.replace(root_dir, '', 1).lstrip('/').lstrip('\\')
