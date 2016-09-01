#!/usr/bin/env python

import os
import logging


_win_path = r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup'
_win_file = r'noipUpdater.bat'
_linux_path = '/etc/init.d'
_linux_file = 'noipUpdater'


def get_path():
    if os.name == 'nt':
        path = r'{}\{}'.format(_win_path, _win_file)
    elif os.name == 'posix':
        path = r'{}/{}'.format(_linux_path, _linux_file)
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
        success = True
        logging.debug('Removing script from start-up folder - {}'.format(path))
        if os_name == 'nt':
            try:
                os.remove(path)
            except Exception as ex:
                logging.exception(ex)
                success = False
        elif os_name == 'posix':
            if _is_user_admin():
                import subprocess
                import traceback
                try:
                    subprocess.call(['update-rc.d', '-f', _linux_file, 'remove'])
                except Exception as ex:
                    logging.exception(ex)
                    success = False
            else:
                logging.error('User not root')
                success = False
        if success:
            logging.info('Startup script removed.')
        else:
            logging.error('Please remove script from startup manually')


def _get_pythonw_path():
    import sys
    python_exe = sys.executable
    return python_exe.replace('.exe', 'w.exe')


def _get_current_path():
    return os.path.dirname(__file__)


def add_startup(_username, _password, _hostname):
    os_name = os.name
    admin_error = script = None
    run_script = '"{}" -s {} {} {}'.format(os.path.join(_get_current_path(), 'updater.py'),
                                           _username, _password, _hostname)
    if os_name == 'nt':
        script = '@echo off\nstart "" {} {}'.format(_get_pythonw_path(), run_script)
        admin_error = 'Please move the "{}" file to the startup folder manually'.format(_win_file)
    elif os_name == 'posix':
        script = '#!/bin/sh\npython {}'.format(run_script)
        admin_error = 'Please move the "{}" file to "/etc/init.d/" folder and configure it to run on startup manually'.\
            format(_linux_file)
    if not _is_user_admin():
        logging.warning('Current user is not a root. Creating script in current directory')
        logging.warning(admin_error)
        path = os.path.join(_get_current_path(), get_file_name())
    else:
        path = get_path()
    logging.debug('Script file location: {}'.format(path))
    try:
        script_file = open(path, 'w')
        script_file.write(script)
        script_file.close()
    except Exception as ex:
        logging.exception(ex.message)
    if os_name == 'posix':
        import subprocess
        subprocess.call(['chmod', 'ugo+x', path])
        if _is_user_admin():
            subprocess.call(['update-rc.d', _linux_file, 'defaults'])


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
