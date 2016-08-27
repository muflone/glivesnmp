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

import subprocess

snmp = None


class SNMP(object):
    def __init__(self):
        """Object initialization"""
        self.oids = {}

    def translate(self, oid, force_lookup=False):
        """Translate a literal OID to numeric OID"""
        if oid not in self.oids or force_lookup:
            arguments = ['snmptranslate', ]
            arguments.append('-On')
            arguments.append(oid)
            process = subprocess.Popen(args=arguments,
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            if stderr:
                print 'stderr = ', stderr
                return None
            else:
                self.oids[oid] = stdout.replace('\n', '')
        return self.oids[oid]

    def get_from_host(self, host, oid):
        """Get the value for a requested OID for a HostInfo object"""
        return self.get(protocol=host.protocol.lower(),
                        address=host.address,
                        port_number=host.port_number,
                        version=host.version,
                        community=host.community,
                        oid=oid)

    def get(self, protocol, address, port_number, version, community, oid):
        """Get the value for a requested OID"""
        process = subprocess.Popen(args=['snmpget',
                                         '-v1' if version == 1 else '-v2c',
                                         '-c', community,
                                         '-O', 'vn',
                                         '-t', '0.3',
                                         '%s:%s:%d' % (protocol,
                                                       address,
                                                       port_number),
                                         self.translate(oid)],
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if stderr:
            print 'Error: ', stderr
            return None
        else:
            datatype, value = stdout.replace('\n', '').split(': ', 1)
            if datatype == 'STRING':
                if value.startswith('"') and value.endswith('"'):
                    # Strip quotes
                    value = value[1:-1]
            elif datatype in ('INTEGER', 'Counter32', 'IpAddress', 'OID'):
                # No conversion needed
                pass
            elif datatype == 'Hex-STRING':
                # Convert Hex string to string
                value = str(bytearray.fromhex(value))
            elif datatype == 'Timeticks':
                # Skip the number of timeticks as the full time follows
                value = value.split(') ')[1]
            else:
                # An unexpected data type was found
                print 'Unexpected data type: %s' % datatype
            return value
