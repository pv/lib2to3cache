"""
lib2to3cache
============

:author: Pauli Virtanen <pav@iki.fi>

Module that modifies lib2to3 to cache its results, significantly
reducing the time taken by repeated 2 to 3 translation of Python code.

"""

# This code is in the public domain. Do whatever you wish with it.

import sys
import os
import os
import shutil
import hashlib
import lib2to3.refactor

if sys.version_info[0] < 3:
    raise RuntimeError("This module is only for Python 3")

# cache location
CACHE_DIR = os.path.expanduser("~/.2to3cache")

# size of cache
MAX_CACHED_FILES = 10000

def do_monkeypatch():
    if not os.path.isdir(CACHE_DIR):
        os.makedirs(CACHE_DIR)

    def file_mtime(fn):
        try:
            return os.stat(fn).st_mtime
        except:
            return 0.0

    files = os.listdir(CACHE_DIR)
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
        digest = hashlib.sha1(input.encode('utf-8'))

        # the files present in the same directory may affect the result
        # of refactoring -- cf. fixes/fix_import.py in 2to3
        #
        # so we need to include that info in the key
        path = getattr(self, '_cur_path', None)
        if path is not None and os.path.isdir(path):
            for fn in sorted(os.listdir(path)):
                ext = os.path.splitext(fn)[1]
                if ext in ['.py', '.pyc', '.so', '.sl', '.pyd']:
                    digest.update(fn.encode('utf-8'))
                    digest.update(b'\0')

        digest = digest.hexdigest()
        
        cache_file = os.path.join(CACHE_DIR, digest)
        if os.path.isfile(cache_file):
            # fetch from cache
            f = open(cache_file, 'r', encoding='utf-8')
            was_changed = (f.readline() == 'y\n')
            output = f.read()
            f.close()
            # update cache file mtime
            os.utime(cache_file, None)
        else:
            # refactor
            tree = old_refactor_string(self, input, name)
            was_changed = tree.was_changed
            output = str(tree)

            # put to cache
            f = open(cache_file + '.new', 'w', encoding='utf-8')
            if was_changed:
                f.write('y\n')
            else:
                f.write('n\n')
            f.write(output)
            f.close()
            shutil.move(cache_file + '.new', cache_file)

        return DummyTree(output, was_changed)

    def new_refactor_file(self, filename, write=False, doctests_only=False):
        """Refactors a file."""
        self._cur_path = os.path.abspath(os.path.dirname(filename))
        return old_refactor_file(self, filename, write, doctests_only)

    lib2to3.refactor.RefactoringTool.refactor_string = new_refactor_string
    lib2to3.refactor.RefactoringTool.refactor_file = new_refactor_file

do_monkeypatch()
