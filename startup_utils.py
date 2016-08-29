#!/usr/bin/env python

import os
import logging


_win_path = r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup'
_win_file = r'updater.bat'
_linux_path = ''
_linux_file = ''


def get_path():
    if os.name == 'nt':
        path = r'{}\{}'.format(_win_path, _win_file)
    elif os.name == 'posix':
        # TODO: need to implement path find on unix
        path = ''
    else:
        path = None
    return path


def get_file_name():
    if os.name == 'nt':
        name = _win_file
    elif os.name == 'posix':
        name = _linux_file
    else:
        name = None
    return name


def remove_startup():
    os_name = os.name
    path = get_path()
    if os.path.exists(path):
        logging.debug('Removing script from start-up folder - {}'.format(path))
        if os_name == 'nt':
            try:
                os.remove(path)
            except Exception as ex:
                logging.exception(ex)
        elif os_name == 'posix':
            # TODO: need to implement remover on unix
            pass
        logging.info('Startup script removed.')


def _get_pythonw_path():
    import sys
    python_exe = sys.executable
    return python_exe.replace('.exe', 'w.exe')


def _get_current_path():
    return os.path.dirname(__file__)


def add_startup(_username, _password, _hostname):
    os_name = os.name
    if os_name == 'nt':
        pythonw_exe = _get_pythonw_path()
        script = '@echo off\nstart "" {} "{}/updater.py" -s {} {} {}'.format(pythonw_exe, _get_current_path(),
                                                                    _username, _password, _hostname)
        if not _is_user_admin():
            logging.warning('Current user is not an Admin. Creating script in current directory')
            logging.warning('Please move the "updater.bat" file to the startup folder manually')
            path = _get_current_path() + '/' + _win_file
        else:
            path = get_path()
        logging.debug('Script file location: {}'.format(path))
        script_file = open(path, 'w')
        script_file.write(script)
        script_file.close()
    elif os_name == 'posix':
        # TODO: need to implement startup creation on unix
        pass


def _is_user_admin():
    import traceback
    if os.name == 'nt':
        import ctypes
        # WARNING: requires Windows XP SP2 or higher!
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            logging.exception(traceback.print_exc())
            logging.debug('Admin check failed, assuming not an admin.')
            return False
    elif os.name == 'posix':
        # Check for root on Posix
        return os.getuid() == 0
    else:
        raise RuntimeError("Unsupported operating system for this module: %s" % (os.name,))
