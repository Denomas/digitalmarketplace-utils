import datetime
import math
import os
from .formats import DATE_FORMAT
from flask import jsonify, current_app
from flask_featureflags import FEATURE_FLAGS_CONFIG


def get_version_label(path):
    try:
        path = os.path.join(path, 'version_label')
        with open(path) as f:
            return f.read().strip()
    except IOError:
        return None


def get_flags(current_app):
    """ Loop through config variables and return a dictionary of flags.  """
    flags = {}

    for config_var in current_app.config.keys():
        # Check that the (inline) key starts with our config variable
        if config_var.startswith("{}_".format(FEATURE_FLAGS_CONFIG)):

                flags[config_var] = current_app.config[config_var]

    return flags


def get_disk_space_status(low_disk_percent_threshold=5):
    """Accepts a single parameter that indicates the minimum percentage of disk space which should be free for the
    instance to be considered healthy.

    Returns a tuple containing two items: a status (OK or LOW) indicating whether the disk space remaining on the
    instance is below the threshold and the integer percentage remaining disk space."""
    disk_stats = os.statvfs('/')

    disk_free_percent = int(math.ceil(((disk_stats.f_bfree * 1.0) / disk_stats.f_blocks) * 100))

    return 'OK' if disk_free_percent >= low_disk_percent_threshold else 'LOW', disk_free_percent


def enabled_since(date_string):
    if date_string:
        # Check format like YYYY-MM-DD
        datetime.datetime.strptime(date_string, DATE_FORMAT)
        return date_string

    return False


class StatusError(Exception):
    """A stub class to use when implementing additional checks for an app's _status endpoint. See API for example.
    When raising a StatusError, make sure that the message passed in uniquely identifies the additional check you are
    performing so that any errors can more easily be tied back to a specific dependency that has failed."""
    message = ''

    def __init__(self, message):
        super().__init__(message)
        self.message = message


def get_app_status(data_api_client=None,
                   search_api_client=None,
                   ignore_dependencies=False,
                   additional_checks=None):
    """Generates output for `_status` endpoints on apps

    :param current_app: The flask `current_app` global.
    :param data_api_client: The app's data_api_client, if used.
    :param search_api_client: The app's search_api_client, if used.
    :param ignore_dependencies: Minimal endpoint checks only (i.e. the app is routable and disk space is fine).
    :param additional_checks: A sequence of callables that return dicts of data to be injected into the final JSON
                              response or raise StatusErrors if they need to log an error that should fail the
                              check (this will cause the endpoint to return a 500).
    :return: A dictionary describing the current state of the app with, at least, a 'status' key with a value of 'ok'
             or 'error'.
    """
    error_messages = []
    response_data = {'status': 'ok'}

    disk_status = get_disk_space_status()
    response_data['disk'] = f'{disk_status[0]} ({disk_status[1]}% free)'
    if disk_status[0].lower() != 'ok':
        error_messages.append(f'Disk space low: {disk_status[1]}% remaining.')

    if not ignore_dependencies:
        response_data['version'] = current_app.config['VERSION']
        response_data['flags'] = get_flags(current_app)

        if data_api_client:
            data_api_status = data_api_client.get_status() or {'status': 'n/a'}
            response_data['api_status'] = data_api_status
            if data_api_status['status'].lower() != 'ok':
                error_messages.append('Error connecting to the Data API.')

        if search_api_client:
            search_api_status = search_api_client.get_status() or {'status': 'n/a'}
            response_data['search_api_status'] = search_api_status
            if search_api_status['status'].lower() != 'ok':
                error_messages.append('Error connecting to the Search API.')

        for additional_check in (additional_checks or []):
            try:
                response_data.update(additional_check())

            except StatusError as e:
                error_messages.append(e.message)

    if error_messages:
        response_data['status'] = 'error'
        response_data['message'] = error_messages

    return jsonify(**response_data), 200 if not error_messages else 500
