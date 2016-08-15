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

from glivesnmp.models.abstract import ModelAbstract
from glivesnmp.models.device_info import DeviceInfo

devices = {}


class ModelDevices(ModelAbstract):
    COL_DESCRIPTION = 1

    def __init__(self, model):
        """Add a list for enabled services"""
        super(self.__class__, self).__init__(model)
        self.services = {}

    def add_data(self, item):
        """Add a new row to the model if it doesn't exists"""
        super(self.__class__, self).add_data(item)
        if item.name not in self.rows:
            new_row = self.model.append((item.name,
                                         item.description))
            self.services[item.name] = item.services
            self.rows[item.name] = new_row
            return new_row

    def set_data(self, treeiter, item):
        """Update an existing TreeIter"""
        super(self.__class__, self).set_data(treeiter, item)
        self.model.set_value(treeiter, self.COL_KEY, item.name)
        self.model.set_value(treeiter, self.COL_DESCRIPTION, item.description)
        self.services[item.name] = item.services

    def get_description(self, treeiter):
        """Get the description from a TreeIter"""
        return self.model[treeiter][self.COL_DESCRIPTION]

    def get_services(self, treeiter):
        """Get the list of enabled services from a TreeIter"""
        return self.services[self.get_key(treeiter)]

    def dump(self):
        """Extract the model data to a dict object"""
        super(self.__class__, self).dump()
        result = {}
        for key in self.rows.iterkeys():
            result[key] = DeviceInfo(
                name=self.get_key(self.rows[key]),
                description=self.get_description(self.rows[key]),
                services=self.get_services(self.rows[key]))
        return result
