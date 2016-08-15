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

import os.path

from gi.repository import Gtk

from glivesnmp.gtkbuilder_loader import GtkBuilderLoader
from glivesnmp.functions import (
    check_invalid_input, get_ui_file, set_error_message_on_infobar, text, _)
import glivesnmp.preferences as preferences
import glivesnmp.settings as settings

import glivesnmp.models.services as model_services
from glivesnmp.models.device_service_info import DeviceServiceInfo
from glivesnmp.models.device_services import ModelDeviceServices

SECTION_WINDOW_NAME = 'device detail'


class UIDeviceDetail(object):
    def __init__(self, parent, devices):
        """Prepare the devices detail dialog"""
        # Load the user interface
        self.ui = GtkBuilderLoader(get_ui_file('device_detail.glade'))
        if not preferences.get(preferences.DETACHED_WINDOWS):
            self.ui.dialog_edit_device.set_transient_for(parent)
        # Restore the saved size and position
        settings.positions.restore_window_position(
            self.ui.dialog_edit_device, SECTION_WINDOW_NAME)
        # Initialize actions
        for widget in self.ui.get_objects_by_type(Gtk.Action):
            # Connect the actions accelerators
            widget.connect_accelerator()
            # Set labels
            widget.set_label(text(widget.get_label()))
        # Initialize labels
        for widget in self.ui.get_objects_by_type(Gtk.Label):
            widget.set_label(text(widget.get_label()))
            widget.set_tooltip_text(widget.get_label().replace('_', ''))
        # Initialize tooltips
        for widget in self.ui.get_objects_by_type(Gtk.Button):
            action = widget.get_related_action()
            if action:
                widget.set_tooltip_text(action.get_label().replace('_', ''))
        self.model = devices
        self.selected_iter = None
        self.model_services = ModelDeviceServices(self.ui.store_services)
        self.name = ''
        self.description = ''
        # Connect signals from the glade file to the module functions
        self.ui.connect_signals(self)

    def show(self, name, description, services, title, treeiter):
        """Show the devices detail dialog"""
        self.ui.txt_name.set_text(name)
        self.ui.txt_description.set_text(description)
        self.ui.txt_name.grab_focus()
        self.ui.dialog_edit_device.set_title(title)
        self.selected_iter = treeiter
        # Load the list of the selected services
        for service_name in model_services.services:
            service_info = DeviceServiceInfo(service_name,
                                             service_name in services)
            self.model_services.add_data(service_info)
        response = self.ui.dialog_edit_device.run()
        self.ui.dialog_edit_device.hide()
        self.name = self.ui.txt_name.get_text().strip()
        self.description = self.ui.txt_description.get_text().strip()
        # Get the list of the selected services
        self.services = []
        for service_name in model_services.services:
            if self.model_services.get_status(
                    self.model_services.rows[service_name]):
                self.services.append(service_name)
        return response

    def destroy(self):
        """Destroy the devices dialog"""
        settings.positions.save_window_position(
            self.ui.dialog_edit_device, SECTION_WINDOW_NAME)
        self.ui.dialog_edit_device.destroy()
        self.ui.dialog_edit_device = None

    def on_action_confirm_activate(self, action):
        """Check che device configuration before confirm"""
        def show_error_message_on_infobar(widget, error_msg):
            """Show the error message on the GtkInfoBar"""
            set_error_message_on_infobar(
                widget=widget,
                widgets=(self.ui.txt_name, self.ui.txt_description),
                label=self.ui.lbl_error_message,
                infobar=self.ui.infobar_error_message,
                error_msg=error_msg)
        name = self.ui.txt_name.get_text().strip()
        description = self.ui.txt_description.get_text().strip()
        if len(name) == 0:
            # Show error for missing device name
            show_error_message_on_infobar(
                self.ui.txt_name,
                _('The device name is missing'))
        elif '\'' in name or '\\' in name or '/' in name or ',' in name:
            # Show error for invalid device name
            show_error_message_on_infobar(
                self.ui.txt_name,
                _('The device name is invalid'))
        elif self.model.get_iter(name) not in (None, self.selected_iter):
            # Show error for existing device name
            show_error_message_on_infobar(
                self.ui.txt_name,
                _('A device with that name already exists'))
        elif len(description) == 0:
            # Show error for missing device description
            show_error_message_on_infobar(
                self.ui.txt_description,
                _('The device description is missing'))
        elif '\'' in description or '\\' in description:
            # Show error for invalid device description
            show_error_message_on_infobar(
                self.ui.txt_description,
                _('The device description is invalid'))
        else:
            self.ui.dialog_edit_device.response(Gtk.ResponseType.OK)

    def on_infobar_error_message_response(self, widget, response_id):
        """Close the infobar"""
        if response_id == Gtk.ResponseType.CLOSE:
            self.ui.infobar_error_message.set_visible(False)

    def on_txt_name_changed(self, widget):
        """Check the device name field"""
        check_invalid_input(widget, False, False, False)

    def on_txt_description_changed(self, widget):
        """Check the device description field"""
        check_invalid_input(widget, False, True, False)

    def on_column_enabled_toggled(self, widget, treepath):
        """Enable or disable the selected service"""
        self.model_services.set_status(
            treepath, not self.model_services.get_status(treepath))
