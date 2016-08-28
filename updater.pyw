#!/usr/bin/env python

import requests
from requests.auth import HTTPBasicAuth
import time
import ctypes
import os
import logging
import argparse
import startup_utils

logging.basicConfig(
    filename='ddns-update-service.log',
    level=logging.DEBUG,
    format='%(asctime)s [ddns-update] %(levelname)-8s %(message)s'
)

_minute = 60
_hour = 3600


class UpdaterError(Exception):
    pass


class InputError(UpdaterError):
    def __init__(self, msg):
        self.msg = msg


class BadError(UpdaterError):
    def __init__(self, msg):
        self.msg = msg


class Updater(object):

    __auth = None
    __hostname = None
    __last_ip = None
    __daemon = None

    def __init__(self, _username, _password, _hostname, _daemon=False):
        logging.info('')
        logging.info('===============================================')
        logging.info('Service Initializing')
        logging.debug('username: {}'.format(_username))
        self.__auth = HTTPBasicAuth(_username, _password)
        logging.debug('hostname: {}'.format(_hostname))
        self.__hostname = _hostname
        logging.debug('daemon: {}'.format(_daemon))
        self.__daemon = _daemon

        if self.__daemon and not os.path.exists(startup_utils.get_path()):
            if not os.path.exists(startup_utils.get_file_name()):
                startup_utils.add_startup(arguments.username, arguments.password, arguments.hostname)
            else:
                logging.warning('Startup script need to be copied to startup folder')
                ctypes.windll.user32.MessageBoxA(0, 'Startup script need to be copied to startup folder.',
                                                 'No-Ip Updater', 0)

    def start(self):
        continue_running = True
        logging.info('Starting service run...')
        while continue_running:
            continue_running = self._update() and self.__daemon
            if continue_running:
                Updater._start_hours_delay(2.5)
        logging.info('Stopping service...')

    def _update(self):
        logging.info('Getting current IP address')
        new_ip = self._get_ip()
        is_different = new_ip != self.__last_ip
        logging.debug('if {} != {} : {}'.format(new_ip, self.__last_ip, is_different))
        if is_different:
            try:
                logging.info('IP was changed. Sending update to NO-IP')
                self._send_update(new_ip)
                logging.info('IP updated successfully')
                return_value = True
            except InputError as ex:
                self._show_message(ex.msg)
                logging.error('Input Error: {}'.format(ex.msg))
                return_value = False
            except BadError as ex:
                log_msg = popup_msg = ''
                if self.__daemon:
                    popup_msg = '\n\rRemoving script from start-up folder.'
                    log_msg = ' Removing script from start-up folder - {}'.format(startup_utils.get_path())
                    startup_utils.remove_startup()
                self._show_message('Critical error.{}'.format(popup_msg))
                logging.critical('{}.'.format(ex.msg, log_msg))
                return_value = False
        else:
            logging.info('No change in IP. Skipping...')
            return_value = True
        return return_value

    @staticmethod
    def _get_ip():
        ip = None
        while ip is None or ip == '':
            try:
                ip = requests.get('https://httpbin.org/ip').json()['origin']
            except requests.ConnectionError:
                logging.error('Connection to "httpbin.org" encountered an error. Retry in 5 minutes...')
                Updater._start_minutes_delay(5)
            except requests.Timeout:
                logging.error('Connection to "httpbin.org" timed out. Retry in 1.5 minutes...')
                Updater._start_minutes_delay(1.5)
        logging.info('Current IP is: ' + ip)
        return ip

    def _send_update(self, new_ip):
        update_url = 'https://dynupdate.no-ip.com/nic/update'
        payload = {'hostname': self.__hostname, 'myip': new_ip}
        headers = {'user-agent': 'python update client Win10/ dj_legolas1@hotmail.com'}
        logging.debug(headers)
        again = True
        while again:
            r = None
            try:
                r = requests.get(update_url, params=payload, auth=self.__auth, headers=headers)
            except requests.ConnectionError:
                logging.error('Connection to "no-ip.com" encountered an error. Retry in 5 minutes...')
                self._start_minutes_delay(5)
                again = True
            except requests.Timeout:
                logging.error('Connection to "no-ip.com" timed out. Retry in 1.5 minutes...')
                self._start_minutes_delay(1.5)
                again = True

            if r is not None:
                if 'nohost' in r.text:
                    raise InputError('No Host')
                elif 'badauth' in r.text:
                    raise InputError('Bad Authentication')
                elif 'badagent' in r.text:
                    raise BadError('Bad Agent')
                elif 'abuse' in r.text:
                    raise BadError('Abuse')
                elif '!donator' in r.text:
                    raise BadError('Not Donator')
                elif '911' in r.text:
                    self._start_minutes_delay(35)
                    again = True
                elif 'good ' + new_ip in r.text or 'nochg ' + new_ip in r.text:
                    again = False
                    self.__last_ip = new_ip
                    logging.debug('last ip updated to: {}'.format(new_ip))

    @staticmethod
    def _show_message(message):
        ctypes.windll.user32.MessageBoxA(0, message, 'No-Ip Updater', 0)

    @staticmethod
    def _start_minutes_delay(amount_of_minutes):
        time.sleep(_minute * amount_of_minutes)

    @staticmethod
    def _start_hours_delay(amount_of_hours):
        time.sleep(_hour * amount_of_hours)


if __name__ == "__main__":
    argument_parser = argparse.ArgumentParser()
    argument_parser.add_argument('username',
                                 type=str,
                                 help='User name at no-ip.com')
    argument_parser.add_argument('password',
                                 type=str,
                                 help='Password of the user')
    argument_parser.add_argument('hostname',
                                 type=str,
                                 help='Host name URL')
    argument_parser.add_argument('-s', '--startup',
                                 action='store_true',
                                 help='Configure to run on startup')
    arguments = argument_parser.parse_args()

    updater = Updater(arguments.username, arguments.password, arguments.hostname, arguments.startup)
    updater.start()
