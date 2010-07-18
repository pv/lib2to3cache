"""
lib2to3cache
============

:author: Pauli Virtanen <pav@iki.fi>
:license: Public domain

Monkeypatch lib2to3 to cache its results in ~/.2to3cache

"""

import sys
import os
import os
import shutil
import hashlib
import tempfile
import gzip
import lib2to3.refactor

# cache location
CACHE_DIR = os.path.expanduser("~/.2to3cache")

# size of cache
MAX_CACHED_FILES = 10000

# cache encoding
CACHE_ENCODING = 'utf-8'

# Python 2 vs Python 3 compatibility
if sys.version_info[0] < 3:
    bytes = str
    asbytes = lambda x: x
else:
    unicode = str
    asbytes = lambda x: x.encode('latin1')

# Perform the monkeypatching

def do_monkeypatch():
    if not os.path.isdir(CACHE_DIR):
        os.makedirs(CACHE_DIR)

    def file_mtime(fn):
        try:
            return os.stat(fn).st_mtime
        except:
            return 0.0

    files = [os.path.join(CACHE_DIR, fn) for fn in os.listdir(CACHE_DIR)]
    if len(files) > MAX_CACHED_FILES:
        files.sort(key=file_mtime)
        for fn in files[:-MAX_CACHED_FILES]:
            os.unlink(fn)

    class DummyTree(object):
        def __init__(self, output, was_changed):
            self.output = output
            self.was_changed = was_changed
        def __str__(self):
            return self.output

    old_refactor_string = lib2to3.refactor.RefactoringTool.refactor_string
    old_refactor_file = lib2to3.refactor.RefactoringTool.refactor_file

    def new_refactor_string(self, input, name):
        digest = hashlib.sha1(input.encode(CACHE_ENCODING))

        def feed_digest(s):
            if isinstance(s, unicode):
                digest.update(s.encode(CACHE_ENCODING))
            else:
                digest.update(s)

        # the files present in the same directory may affect the result
        # of refactoring -- cf. fixes/fix_import.py in 2to3
        #
        # so we need to include that info in the key
        path = getattr(self, '_cur_path', None)
        if path is not None and os.path.isdir(path):
            for fn in sorted(os.listdir(path)):
                ext = os.path.splitext(fn)[1]
                if ext in ['.py', '.pyc', '.so', '.sl', '.pyd']:
                    feed_digest(fn + '\0')

        # also fixers and options must be taken into account
        feed_digest('\0')
        for f in sorted(self.fixers):
            feed_digest(f + '\0')
        feed_digest('\0')
        for f in sorted(self.explicit):
            feed_digest(f + '\0')
        feed_digest('\0')
        for k, v in sorted(self.options.items()):
            feed_digest(k + '\0')
            feed_digest(repr(v) + '\0')

        # finish digesting
        digest = digest.hexdigest()

        cache_file = os.path.join(CACHE_DIR, digest)
        if os.path.isfile(cache_file):
            # fetch from cache
            f = gzip.open(cache_file, 'rb')
            header = f.readline()
            was_changed = (header == asbytes('y\n'))
            output = f.read().decode(CACHE_ENCODING)
            f.close()
            # update cache file mtime
            os.utime(cache_file, None)
        else:
            # refactor
            tree = old_refactor_string(self, input, name)
            was_changed = tree.was_changed
            output = str(tree)

            # put to cache
            tmp_fd, tmp_fn = tempfile.mkstemp(dir=CACHE_DIR, suffix='.new')
            os.close(tmp_fd)

            f = gzip.open(tmp_fn, 'wb')
            if was_changed:
                f.write(asbytes('y\n'))
            else:
                f.write(asbytes('n\n'))
            f.write(output.encode(CACHE_ENCODING))
            f.close()
            shutil.move(tmp_fn, cache_file)

        return DummyTree(output, was_changed)

    def new_refactor_file(self, filename, write=False, doctests_only=False):
        """Refactors a file."""
        self._cur_path = os.path.abspath(os.path.dirname(filename))
        return old_refactor_file(self, filename, write, doctests_only)

    lib2to3.refactor.RefactoringTool.refactor_string = new_refactor_string
    lib2to3.refactor.RefactoringTool.refactor_file = new_refactor_file

do_monkeypatch()

def main():
    from lib2to3.main import main
    return main("lib2to3.fixes")
