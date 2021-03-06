# -*- coding: UTF-8 -*-
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

import os
import os.path
import threading

from gi.repository import Gtk
from gi.repository import GLib

from glivesnmp.gtkbuilder_loader import GtkBuilderLoader
from glivesnmp.constants import DIR_HOSTS
from glivesnmp.functions import (
    get_ui_file, get_treeview_selected_row, text, _)
import glivesnmp.preferences as preferences
import glivesnmp.settings as settings
import glivesnmp.snmp as snmp
from glivesnmp.semaphored_thread import SemaphoredThread
from glivesnmp.snmp_exception import SNMPException

from glivesnmp.ui.message_dialog import (
    show_message_dialog, UIMessageDialogNoYes)

import glivesnmp.models.devices as model_devices
import glivesnmp.models.services as model_services
from glivesnmp.models.snmp_values import SNMPValues
from glivesnmp.models.snmp_value_info import SNMPValueInfo

SECTION_WINDOW_NAME = 'snmp values'


class UISNMPValues(object):
    def __init__(self, parent, host):
        """Prepare the snmp values dialog"""
        # Load the user interface
        self.ui = GtkBuilderLoader(get_ui_file('snmp_values.glade'))
        if not preferences.get(preferences.DETACHED_WINDOWS):
            self.ui.window_snmp.set_transient_for(parent)
        # Restore the saved size and position
        settings.positions.restore_window_position(
            self.ui.window_snmp, SECTION_WINDOW_NAME)
        # Initialize actions
        for widget in self.ui.get_objects_by_type(Gtk.Action):
            # Connect the actions accelerators
            widget.connect_accelerator()
            # Set labels
            if widget.get_label():
                widget.set_label(text(widget.get_label()))
        # Initialize tooltips
        for widget in self.ui.get_objects_by_type(Gtk.Button):
            action = widget.get_related_action()
            if action:
                widget.set_tooltip_text(action.get_label().replace('_', ''))
        # Initialize column headers
        for widget in self.ui.get_objects_by_type(Gtk.TreeViewColumn):
            widget.set_title(text(widget.get_title()))
        # Initialize services
        self.model = SNMPValues(self.ui.store_values)
        self.services = {}
        for service in model_devices.devices[host.device].services:
            oid = model_services.services[service].numeric_oid
            self.services[service] = oid
            value = SNMPValueInfo(name=service, value='', timestamp=0)
            self.model.add_data(value)
        # Sort the data in the models
        self.model.model.set_sort_column_id(
            self.ui.column_name.get_sort_column_id(),
            Gtk.SortType.ASCENDING)
        self.host = host
        self.ui.window_snmp.set_title(_('SNMP values for %s') % host.name)
        self.semaphore = None
        self.completed_threads = 0
        # Connect signals from the glade file to the module functions
        self.ui.connect_signals(self)

    def show(self):
        """Show the Groups dialog"""
        self.ui.window_snmp.show()

    def destroy(self):
        """Destroy the Groups dialog"""
        settings.positions.save_window_position(
            self.ui.window_snmp, SECTION_WINDOW_NAME)
        self.ui.window_snmp.hide()
        self.ui.window_snmp.destroy()
        self.ui.window_snmp = None

    def on_window_snmp_delete_event(self, widget, event):
        """Window closing event"""
        # Disable timer and scan when the window is closed
        self.ui.action_timer.set_active(False)
        self.ui.action_refresh.set_active(False)
        self.destroy()

    def on_action_refresh_activate(self, action):
        """Update values"""
        def update_ui(values):
            """Update the UI in a thread-safe way using GLib"""
            for service in self.services.keys():
                treeiter = self.model.rows[service]
                self.model.set_value(treeiter,
                                     values.get(self.services[service],
                                                _('<SNMP Error>')))
                if values.has_key('error'):
                    print values

            # Start scan again if the timer is enabled
            if self.ui.action_timer.get_active():
                GLib.timeout_add(self.ui.adjustment_timer.get_value(),
                                 self.on_action_refresh_activate,
                                 action)
            else:
                # Stop the scan
                self.ui.action_refresh.set_active(False)

        def worker(host, oids):
            """Get a reply from SNMP and update the model accordingly"""
            try:
                values = snmp.snmp.get_from_host(host, oids)
            except SNMPException as error:
                print 'Exception: %s' % error.value
                values = {'error': 'Exception: %s' % error.value}
            GLib.idle_add(update_ui, values)

        if self.ui.action_refresh.get_active():
            # Scan for new data
            self.completed_threads = 0
            self.ui.action_refresh.set_icon_name('media-playback-stop')
            # Set the number of maximum running threads
            self.semaphore = threading.BoundedSemaphore(1)
            self.semaphore.cancel = False
            oids = []
            for service in self.services.keys():
                treeiter = self.model.rows[service]
                self.model.set_value(treeiter, '')
                oids.append(self.services[service])
            # Create a new thread and launch it
            thread = SemaphoredThread(semaphore=self.semaphore,
                                      callback=worker,
                                      arguments=(self.host, oids),
                                      name=self.services[service],
                                      target=worker)
            thread.start()
        else:
            # Stop a previous scan
            self.semaphore.cancel = True
            self.ui.action_refresh.set_icon_name('media-playback-start')
            # Disable the timer when the scan is stopped
            self.ui.action_timer.set_active(False)
        # Returning False the timer automatically ends
        # It will be fired again after the scan is completed
        return False

    def on_action_timer_toggled(self, action):
        """Enable the timer for the autoscan"""
        if self.ui.action_timer.get_active():
            # Start scan when the timer is active
            self.ui.action_refresh.set_active(True)
