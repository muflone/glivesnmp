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


class ModelHosts(ModelAbstract):
    COL_DESCRIPTION = 1
    COL_PROTOCOL = 2
    COL_ADDRESS = 3
    COL_PORT = 4
    COL_VERSION = 5
    COL_COMMUNITY = 6
    COL_DEVICE = 7
    COL_REQUESTS = 8

    def add_data(self, item):
        """Add a new row to the model if it doesn't exists"""
        super(self.__class__, self).add_data(item)
        if item.name not in self.rows:
            new_row = self.model.append(None, (item.name,
                                               item.description,
                                               item.protocol,
                                               item.address,
                                               item.port_number,
                                               item.version,
                                               item.community,
                                               item.device,
                                               item.requests))
            self.rows[item.name] = new_row
            return new_row

    def set_data(self, treeiter, item):
        """Update an existing TreeIter"""
        super(self.__class__, self).set_data(treeiter, item)
        self.model.set_value(treeiter, self.COL_KEY, item.name)
        self.model.set_value(treeiter, self.COL_DESCRIPTION, item.description)

    def get_description(self, treeiter):
        """Get the description from a TreeIter"""
        return self.model[treeiter][self.COL_DESCRIPTION]

    def get_protocol(self, treeiter):
        """Get the network protocol from a TreeIter"""
        return self.model[treeiter][self.COL_PROTOCOL]

    def get_address(self, treeiter):
        """Get the address from a TreeIter"""
        return self.model[treeiter][self.COL_ADDRESS]

    def get_port_number(self, treeiter):
        """Get the port number from a TreeIter"""
        return self.model[treeiter][self.COL_PORT]

    def get_version(self, treeiter):
        """Get the SNMP version from a TreeIter"""
        return self.model[treeiter][self.COL_VERSION]

    def get_community(self, treeiter):
        """Get the community string from a TreeIter"""
        return self.model[treeiter][self.COL_COMMUNITY]

    def get_device(self, treeiter):
        """Get the device from a TreeIter"""
        return self.model[treeiter][self.COL_DEVICE]

    def get_requests(self, treeiter):
        """Get the requests type from a TreeIter"""
        return self.model[treeiter][self.COL_REQUESTS]
