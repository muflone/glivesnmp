##
#     Project: gLiveSNMP
# Description: Detect information on various devices via SNMP
#      Author: Fabio Castelli (Muflone) <muflone@vbsimple.net>
#   Copyright: 2016 Fabio Castelli
#     License: GPL-2+
#  This program is free software; you can redistribute it and/or modify it
#  under the terms of the GNU General Public License as published by the Free
#  Software Foundation; either version 2 of the License, or (at your option)
#  any later version.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT
#  ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
#  FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License for
#  more details.
#  You should have received a copy of the GNU General Public License along
#  with this program; if not, write to the Free Software Foundation, Inc.,
#  51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA
##

import threading


class SemaphoredThread(threading.Thread):
    def __init__(self, semaphore, callback, arguments, **kwargs):
        """A thread queue which allows only a limited number of running
        threads using threading.BoundedSemaphore."""
        self.semaphore = semaphore
        self.callback = callback
        self.arguments = arguments
        super(self.__class__, self).__init__(**kwargs)

    def run(self):
        """Launch the thread and run the code only when a lock was acquired
        from the semaphore"""
        self.semaphore.acquire()
        try:
            self.callback(*self.arguments)
        finally:
            self.semaphore.release()