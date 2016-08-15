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

from gi.repository import Gtk

from glivesnmp.gtkbuilder_loader import GtkBuilderLoader
from glivesnmp.functions import (
    get_ui_file, get_treeview_selected_row, text, _)
import glivesnmp.preferences as preferences
import glivesnmp.settings as settings

from glivesnmp.models.devices import ModelDevices
from glivesnmp.models.device_info import DeviceInfo

from glivesnmp.ui.device_detail import UIDeviceDetail
from glivesnmp.ui.message_dialog import (
    show_message_dialog, UIMessageDialogNoYes)

SECTION_WINDOW_NAME = 'devices'


class UIDevices(object):
    def __init__(self, parent):
        """Prepare the devices dialog"""
        # Load the user interface
        self.ui = GtkBuilderLoader(get_ui_file('devices.glade'))
        if not preferences.get(preferences.DETACHED_WINDOWS):
            self.ui.dialog_devices.set_transient_for(parent)
        # Restore the saved size and position
        settings.positions.restore_window_position(
            self.ui.dialog_devices, SECTION_WINDOW_NAME)
        # Initialize actions
        for widget in self.ui.get_objects_by_type(Gtk.Action):
            # Connect the actions accelerators
            widget.connect_accelerator()
            # Set labels
            widget.set_label(text(widget.get_label()))
        # Initialize tooltips
        for widget in self.ui.get_objects_by_type(Gtk.Button):
            action = widget.get_related_action()
            if action:
                widget.set_tooltip_text(action.get_label().replace('_', ''))
        # Initialize column headers
        for widget in self.ui.get_objects_by_type(Gtk.TreeViewColumn):
            widget.set_title(text(widget.get_title()))
        # Load the devices
        self.model = ModelDevices(self.ui.store_devices)
        self.selected_iter = None
        # Sort the data in the models
        self.model.model.set_sort_column_id(
            self.ui.column_name.get_sort_column_id(),
            Gtk.SortType.ASCENDING)
        # Connect signals from the glade file to the module functions
        self.ui.connect_signals(self)

    def show(self):
        """Show the devices dialog"""
        self.ui.dialog_devices.run()
        self.ui.dialog_devices.hide()

    def destroy(self):
        """Destroy the devices dialog"""
        settings.positions.save_window_position(
            self.ui.dialog_devices, SECTION_WINDOW_NAME)
        self.ui.dialog_devices.destroy()
        self.ui.dialog_devices = None

    def on_action_add_activate(self, action):
        """Add a new device"""
        dialog = UIDeviceDetail(self.ui.dialog_devices, self.model)
        if dialog.show(name='',
                       description='',
                       services=[],
                       title=_('Add new device type'),
                       treeiter=None) == Gtk.ResponseType.OK:
            self.model.add_data(DeviceInfo(name=dialog.name,
                                           description=dialog.description,
                                           services=dialog.services))
        dialog.destroy()

    def on_action_edit_activate(self, action):
        """Edit the selected device"""
        selected_row = get_treeview_selected_row(self.ui.tvw_devices)
        if selected_row:
            name = self.model.get_key(selected_row)
            description = self.model.get_description(selected_row)
            services = self.model.get_services(selected_row)
            selected_iter = self.model.get_iter(name)
            dialog = UIDeviceDetail(self.ui.dialog_devices, self.model)
            if dialog.show(name=name,
                           description=description,
                           services=services,
                           title=_('Edit device type'),
                           treeiter=selected_iter
                           ) == Gtk.ResponseType.OK:
                # Update values
                self.model.set_data(selected_iter, DeviceInfo(
                    name=dialog.name,
                    description=dialog.description,
                    services=dialog.services))
            dialog.destroy()

    def on_action_remove_activate(self, action):
        """Remove the selected devices"""
        selected_row = get_treeview_selected_row(self.ui.tvw_devices)
        if selected_row and show_message_dialog(
                class_=UIMessageDialogNoYes,
                parent=self.ui.dialog_devices,
                message_type=Gtk.MessageType.WARNING,
                title=None,
                msg1=_("Remove device"),
                msg2=_("Remove the selected device?"),
                is_response_id=Gtk.ResponseType.YES):
            self.model.remove(selected_row)

    def on_tvw_devices_row_activated(self, widget, treepath, column):
        """Edit the selected row on activation"""
        self.ui.action_edit.activate()
