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

import json

from gi.repository import Gtk

from glivesnmp.gtkbuilder_loader import GtkBuilderLoader
from glivesnmp.functions import (
    check_invalid_input, get_ui_file, get_treeview_selected_row,
    set_error_message_on_infobar, text, _)
import glivesnmp.preferences as preferences
import glivesnmp.settings as settings

import glivesnmp.models.services as model_services

from glivesnmp.ui.message_dialog import (
    show_message_dialog, UIMessageDialogNoYes)

SECTION_WINDOW_NAME = 'host'


class UIHost(object):
    def __init__(self, parent, hosts):
        """Prepare the host dialog"""
        self.hosts = hosts
        # Load the user interface
        self.ui = GtkBuilderLoader(get_ui_file('host.glade'))
        if not preferences.get(preferences.DETACHED_WINDOWS):
            self.ui.dialog_host.set_transient_for(parent)
        # Restore the saved size and position
        settings.positions.restore_window_position(
            self.ui.dialog_host, SECTION_WINDOW_NAME)
        # Initialize actions
        for widget in self.ui.get_objects_by_type(Gtk.Action):
            # Connect the actions accelerators
            widget.connect_accelerator()
            # Set labels
            if widget.get_label():
                widget.set_label(text(widget.get_label()))
            else:
                widget.set_label(text(widget.get_short_label()))
        # Initialize labels
        for widget in self.ui.get_objects_by_type(Gtk.Label):
            widget.set_label(text(widget.get_label()))
            widget.set_tooltip_text(widget.get_label().replace('_', ''))
        # Initialize tooltips
        for widget in self.ui.get_objects_by_type(Gtk.Button):
            action = widget.get_related_action()
            if action:
                widget.set_tooltip_text(action.get_label().replace('_', ''))
        # Initialize column headers
        for widget in self.ui.get_objects_by_type(Gtk.TreeViewColumn):
            widget.set_title(text(widget.get_title()))
        self.selected_iter = None
        # Connect signals from the glade file to the module functions
        self.ui.connect_signals(self)

    def show(self, default_name, default_description, default_protocol,
             default_address, default_port_number, default_version,
             default_community, title, treeiter):
        """Show the destinations dialog"""
        self.ui.txt_name.set_text(default_name)
        self.ui.txt_description.set_text(default_description)
        self.ui.combo_protocol.set_active_id(default_protocol)
        self.ui.txt_address.set_text(default_address)
        self.ui.spin_port_number.set_value(default_port_number)
        self.ui.action_snmp_v1.set_current_value(default_version)
        self.ui.txt_community.set_text(default_community)
        self.ui.txt_name.grab_focus()
        self.ui.dialog_host.set_title(title)
        self.selected_iter = treeiter
        # Show the dialog
        response = self.ui.dialog_host.run()
        self.ui.dialog_host.hide()
        self.name = self.ui.txt_name.get_text().strip()
        self.description = self.ui.txt_description.get_text().strip()
        self.protocol = self.ui.combo_protocol.get_active_id()
        self.address = self.ui.txt_address.get_text().strip()
        self.port_number = self.ui.spin_port_number.get_value_as_int()
        self.version = 2 if self.ui.action_snmp_v2c.get_active() else 1
        self.community = self.ui.txt_community.get_text().strip()
        return response

    def destroy(self):
        """Destroy the destinations dialog"""
        settings.positions.save_window_position(
            self.ui.dialog_host, SECTION_WINDOW_NAME)
        self.ui.dialog_host.destroy()
        self.ui.dialog_host = None

    def on_action_confirm_activate(self, action):
        """Check che host configuration before confirm"""
        def show_error_message_on_infobar(widget, error_msg):
            """Show the error message on the GtkInfoBar"""
            set_error_message_on_infobar(
                widget=widget,
                widgets=(self.ui.txt_name, self.ui.txt_description,
                         self.ui.txt_address, self.ui.txt_community),
                label=self.ui.lbl_error_message,
                infobar=self.ui.infobar_error_message,
                error_msg=error_msg)
        name = self.ui.txt_name.get_text().strip()
        description = self.ui.txt_description.get_text().strip()
        address = self.ui.txt_address.get_text().strip()
        community = self.ui.txt_community.get_text().strip()
        if len(name) == 0:
            # Show error for missing host name
            show_error_message_on_infobar(
                self.ui.txt_name,
                _('The host name is missing'))
        elif '\'' in name or '\\' in name or '/' in name:
            # Show error for invalid host name
            show_error_message_on_infobar(
                self.ui.txt_name,
                _('The host name is invalid'))
        elif self.hosts.get_iter(name) not in (None, self.selected_iter):
            # Show error for existing host name
            show_error_message_on_infobar(
                self.ui.txt_name,
                _('A host with that name already exists'))
        elif len(description) == 0:
            # Show error for missing host description
            show_error_message_on_infobar(
                self.ui.txt_description,
                _('The host description is missing'))
        elif len(address) == 0:
            # Show error for missing address
            show_error_message_on_infobar(
                self.ui.txt_address,
                _('The host address is missing'))
        elif '\'' in address or '\\' in address or '/' in address:
            # Show error for invalid address
            show_error_message_on_infobar(
                self.ui.txt_address,
                _('The host address is invalid'))
        elif len(community) == 0:
            # Show error for missing community string
            show_error_message_on_infobar(
                self.ui.txt_community,
                _('The community string is missing'))
        else:
            self.ui.dialog_host.response(Gtk.ResponseType.OK)

    def on_infobar_error_message_response(self, widget, response_id):
        """Close the infobar"""
        if response_id == Gtk.ResponseType.CLOSE:
            self.ui.infobar_error_message.set_visible(False)

    def on_txt_name_changed(self, widget):
        """Check the host name field"""
        check_invalid_input(widget, False, False, False)

    def on_txt_description_changed(self, widget):
        """Check the host description field"""
        check_invalid_input(widget, False, True, True)

    def on_txt_address_changed(self, widget):
        """Check the host address field"""
        check_invalid_input(widget, False, False, False)

    def on_txt_community_changed(self, widget):
        """Check the community string field"""
        check_invalid_input(widget, False, True, True)
