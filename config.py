#!/usr/env/bin python
# -*- encoding: utf-8 -*-

import contextlib
import json

__author__ = 'Kevin'


@contextlib.contextmanager
def get_config(config_path: str, save_change=False):
    """A config wrapper to simplify config loading and saving."""
    with open(config_path, mode='r', encoding='utf-8') as config_file:
        config = json.load(config_file)
    try:
        yield config
    except Exception as e:
        # if anything goes wrong then give up saving
        raise e
    else:
        if save_change:
            with open(config_path, mode='w', encoding='utf-8') as config_file:
                json.dump(config, config_file)


def create_config(config_template: dict, config_path: str) -> dict:
    """Create the config according to the template."""
    with open(config_path, mode='w', encoding='utf-8') as config_file:
        config_to_be_saved = dict(config_template)
        json.dump(config_to_be_saved, config_file)
    return config_to_be_saved
