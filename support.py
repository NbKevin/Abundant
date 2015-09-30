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
