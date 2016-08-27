gLiveSNMP
[![Build Status](https://travis-ci.org/muflone/glivesnmp.svg?branch=master)](https://travis-ci.org/muflone/glivesnmp)
[![Join the chat at https://gitter.im/muflone/glivesnmp](https://badges.gitter.im/muflone/glivesnmp.svg)](https://gitter.im/muflone/glivesnmp?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

=====

**Description:** Detect information on various devices via SNMP.

**Copyright:** 2016 Fabio Castelli (Muflone) <muflone(at)vbsimple.net>

**License:** GPL-2+

**Codice sorgente:** https://github.com/muflone/glivesnmp

**Documentazione:** http://www.muflone.com/glivesnmp/

System Requirements
-------------------

* Python 2.x (developed and tested for Python 2.7.5)
* GTK+ 3.0 libraries for Python 2.x
* GObject libraries for Python 2.x
* XDG library for Python 2.x
* Distutils library for Python 2.x (usually shipped with Python distribution)
* Net-SNMP suite (http://www.net-snmp.org/)

Installation
------------

A distutils installation script is available to install from the sources.

To install in your system please use:

    cd /path/to/folder
    python2 setup.py install

To install the files in another path instead of the standard /usr prefix use:

    cd /path/to/folder
    python2 setup.py install --root NEW_PATH

Usage
-----

If the application is not installed please use:

    cd /path/to/folder
    python2 glivesnmp.py

If the application was installed simply use the glivesnmp command.
