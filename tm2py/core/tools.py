"""Tools module for common resources / shared code and "utilities" in the tm2py package.

"""

from contextlib import contextmanager as _context
import os as _os
import subprocess as _subprocess
import tempfile as _tempfile
from typing import List

import tm2py.core.logging as _log

_Logger = _log.Logger


def run_process(commands: List[str], name: str = "", logger: _Logger = None):
    """Run system level commands as blocking process and log output and error messages.

        Args:
            commands: list of one or more commands to execute
            name: optional name to use for the temp bat file
            logger: optional Logger object to log output and errors from console
    """
    with temp_file("w", prefix=name, suffix=".bat") as (bat_file, bat_file_path):
        bat_file.write("\n".join(commands))
        bat_file.close()
        if logger:
            # temporary file to capture output error messages generated by Java
            # Note: temp file created in the current working directory
            with temp_file(mode="w+", suffix="_error.log") as (err_file, _):
                try:
                    output = _subprocess.check_output(bat_file_path, stderr=err_file, shell=True)
                    logger.log(output.decode("utf-8"))
                except _subprocess.CalledProcessError as error:
                    logger.log(error.output)
                    raise
                finally:
                    err_file.seek(0)
                    error_msg = err_file.read()
                    if error_msg:
                        logger.log(error_msg)
        else:
            _subprocess.check_call(bat_file_path, shell=True)


@_context
def temp_file(mode: str = "w+", prefix: str = "", suffix: str = ""):
    """Temp file wrapper to return open file handle and named path.

        A named temporary file (using mkstemp) with specified prefix and
        suffix is created and opened with the specified mode. The file
        handle and path are returned. The file is closed and deleted on exit.
    
        Args:
            mode: mode to open file, [rw][+][b]
            prefix: optional text to start temp file name
            suffix: optional text to end temp file name
    """
    file_ref, file_path = _tempfile.mkstemp(prefix=prefix, suffix=suffix)
    file = _os.fdopen(file_ref, mode=mode)
    try:
        yield file, file_path
    finally:
        if not file.closed:
            file.close()
        _os.remove(file_path)