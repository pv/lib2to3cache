lib2to3cache
============

:author: Pauli Virtanen <pav@iki.fi>
:license: Public domain

Tired of waiting for ``2to3`` run to finish?

This module monkeypatches lib2to3 to cache its results, often
significantly reducing the time taken by repeated 2 to 3 translations
of Python code.


Example usage
-------------

In the beginning of your ``setup.py``::

    try:
        import lib2to3cache
    except ImportError:
        pass

    # whatever follows
    ...

On command line::

    $ 2to3cache -w foo.py

