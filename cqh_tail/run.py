#! /usr/bin/env python3

"""
Real-time log files watcher supporting log rotation.
Works with Python >= 2.6 and >= 3.2, on both POSIX and Windows.
Author: Giampaolo Rodola' <g.rodola [AT] gmail [DOT] com>
License: MIT
"""
import re
import argparse
import glob

import os
import time
import errno
import stat


class LogWatcher(object):
    """Looks for changes in all files of a directory.
    This is useful for watching log file changes in real-time.
    It also supports files rotation.
    Example:
    >>> def callback(filename, lines):
    ...     print(filename, lines)
    ...
    >>> lw = LogWatcher("/var/log/", callback)
    >>> lw.loop()
    """

    def __init__(self, glob_pattern, callback, tail_lines=10,
                 sizehint=1048576):
        """Arguments:
        (str) @folder:
            the folder to watch
        (callable) @callback:
            a function which is called every time one of the file being
            watched is updated;
            this is called with "filename" and "lines" arguments.
        (list) @extensions:
            only watch files with these extensions
        (int) @tail_lines:
            read last N lines from files being watched before starting
        (int) @sizehint: passed to file.readlines(), represents an
            approximation of the maximum number of bytes to read from
            a file on every ieration (as opposed to load the entire
            file in memory until EOF is reached). Defaults to 1MB.
        """
        # self.folder = os.path.realpath(folder)
        self.glob_pattern = glob_pattern
        self._files_map = {}
        self._callback = callback
        self._sizehint = sizehint
        assert callable(callback), repr(callback)
        self.update_files()
        for id, file in self._files_map.items():
            file.seek(os.path.getsize(file.name))  # EOF
            if tail_lines:
                try:
                    lines = self.tail(file.name, tail_lines)
                except IOError as err:
                    if err.errno != errno.ENOENT:
                        raise
                else:
                    if lines:
                        self._callback(file.name, lines)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __del__(self):
        self.close()

    def loop(self, interval=0.1, blocking=True):
        """Start a busy loop checking for file changes every *interval*
        seconds. If *blocking* is False make one loop then return.
        """
        # May be overridden in order to use pyinotify lib and block
        # until the directory being watched is updated.
        # Note that directly calling readlines() as we do is faster
        # than first checking file's last modification times.
        while True:
            self.update_files()
            for fid, file in list(self._files_map.items()):
                self.readlines(file)
            if not blocking:
                return
            time.sleep(interval)

    def log(self, line):
        """Log when a file is un/watched"""
        print(line)

    def listdir(self):
        """List directory and filter files by extension.
        You may want to override this to add extra logic or globbing
        support.
        """
        gen = glob.iglob(self.glob_pattern)
        return list(gen)

    @classmethod
    def open(cls, file):
        """Wrapper around open().
        By default files are opened in binary mode and readlines()
        will return bytes on both Python 2 and 3.
        This means callback() will deal with a list of bytes.
        Can be overridden in order to deal with unicode strings
        instead, like this:
          import codecs, locale
          return codecs.open(file, 'r', encoding=locale.getpreferredencoding(),
                             errors='ignore')
        """
        return open(file, 'rb')

    @classmethod
    def tail(cls, fname, window):
        """Read last N lines from file fname."""
        if window <= 0:
            raise ValueError('invalid window value %r' % window)
        with cls.open(fname) as f:
            BUFSIZ = 1024
            # True if open() was overridden and file was opened in text
            # mode. In that case readlines() will return unicode strings
            # instead of bytes.
            encoded = getattr(f, 'encoding', False)
            CR = '\n' if encoded else b'\n'
            data = '' if encoded else b''
            f.seek(0, os.SEEK_END)
            fsize = f.tell()
            block = -1
            exit = False
            while not exit:
                step = (block * BUFSIZ)
                if abs(step) >= fsize:
                    f.seek(0)
                    newdata = f.read(BUFSIZ - (abs(step) - fsize))
                    exit = True
                else:
                    f.seek(step, os.SEEK_END)
                    newdata = f.read(BUFSIZ)
                data = newdata + data
                if data.count(CR) >= window:
                    break
                else:
                    block -= 1
            return data.splitlines()[-window:]

    def update_files(self):
        ls = []
        for name in self.listdir():
            absname = name
            # absname = os.path.realpath(os.path.join(self.folder, name))
            try:
                st = os.stat(absname)
            except EnvironmentError as err:
                if err.errno != errno.ENOENT:
                    raise
            else:
                if not stat.S_ISREG(st.st_mode):
                    continue
                fid = self.get_file_id(st)
                ls.append((fid, absname))

        # check existent files
        for fid, file in list(self._files_map.items()):
            try:
                st = os.stat(file.name)
            except EnvironmentError as err:
                if err.errno == errno.ENOENT:
                    self.unwatch(file, fid)
                else:
                    raise
            else:
                if fid != self.get_file_id(st):
                    # same name but different file (rotation); reload it.
                    self.unwatch(file, fid)
                    self.watch(file.name)

        # add new ones
        for fid, fname in ls:
            if fid not in self._files_map:
                self.watch(fname)

    def readlines(self, file):
        """Read file lines since last access until EOF is reached and
        invoke callback.
        """
        while True:
            lines = file.readlines(self._sizehint)
            if not lines:
                break
            self._callback(file.name, lines)

    def watch(self, fname):
        try:
            file = self.open(fname)
            fid = self.get_file_id(os.stat(fname))
        except EnvironmentError as err:
            if err.errno != errno.ENOENT:
                raise
        else:
            self.log("watching logfile %s" % fname)
            self._files_map[fid] = file

    def unwatch(self, file, fid):
        # File no longer exists. If it has been renamed try to read it
        # for the last time in case we're dealing with a rotating log
        # file.
        self.log("un-watching logfile %s" % file.name)
        del self._files_map[fid]
        with file:
            lines = self.readlines(file)
            if lines:
                self._callback(file.name, lines)

    @staticmethod
    def get_file_id(st):
        if os.name == 'posix':
            return "%xg%x" % (st.st_dev, st.st_ino)
        else:
            return "%f" % st.st_ctime

    def close(self):
        for id, file in self._files_map.items():
            file.close()
        self._files_map.clear()


# ===================================================================
# --- tests
# ===================================================================
example_string = """
Examples:

1. simple filter log

    cqh_tail --pattern=~/**/*.log

2. watch dir and filter

    cqh_tail --pattern=~/**/*.log --line-filter="\.general/"

"""


_dir = os.path.dirname(
    os.path.abspath(__file__)
)
init_path = os.path.join(_dir, '__init__.py')

def read_version():
    d = {}
    code = open(init_path).read()
    code = compile(code, '<string>', 'exec', dont_inherit=True)
    exec(code, d, d)
    return d['__version__']

parser = argparse.ArgumentParser('cqh_tail',
                                 description='tail ',
                                 formatter_class=argparse.RawDescriptionHelpFormatter,
                                 epilog=example_string)
parser.add_argument('--pattern', dest='pattern',
                    help='glob pattern', required=True)
parser.add_argument('-n', '--count', dest='count',
                    default=10, help='tail count')
parser.add_argument('--encode', dest='encode', default='utf-8')
parser.add_argument('--line-filter', dest='line_filter', help='regex for line filter')
parser.add_argument("--version", action="version", version=read_version())


def main(argv=None):
    if argv is not None:
        convert_args = parser.parse_args(argv)
    else:
        convert_args = parser.parse_args()
    import os
    pwd = os.getcwd()
    # print("cwd:{}".format(pwd))
    pattern = convert_args.pattern
    if pattern.index('/') == -1:
        pattern = pwd.rstrip('/') + '/'
    pattern = os.path.expanduser(pattern)
    print("pattern:{}".format(pattern))

    line_filter = convert_args.line_filter
    re_line_filter = None
    if line_filter:
        re_line_filter = re.compile(line_filter)

    def filter_line(prefix_line, line):
        def echo(line):
            if prefix_line:
                print(prefix_line, flush=True)
            print(line, flush=True)
        if not re_line_filter:
            echo(line)
        else:
            if re_line_filter.search(line):
                echo(line)
        return ''

    count = convert_args.count

    def echo(name, lines):
        prefix_line = name.center(80, '=')
        for line in lines:
            if not line:
                continue

            if isinstance(line, bytes):
                try:
                    line = line.decode(convert_args.encode)
                except Exception:
                    print(" fail to decode{!r}".format(line))
                    raise



            line = line.rstrip("\n")
            prefix_line = filter_line(prefix_line, line)
            # generated_by_dict_unpack: convert_args

    w = LogWatcher(pattern, tail_lines=count, callback=echo)
    w.loop()


if __name__ == '__main__':
    main()
