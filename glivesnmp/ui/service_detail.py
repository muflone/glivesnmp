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
import glivesnmp.snmp as snmp

SECTION_WINDOW_NAME = 'service detail'


class UIServiceDetail(object):
    def __init__(self, parent, services):
        """Prepare the services detail dialog"""
        # Load the user interface
        self.ui = GtkBuilderLoader(get_ui_file('service_detail.glade'))
        if not preferences.get(preferences.DETACHED_WINDOWS):
            self.ui.dialog_edit_service.set_transient_for(parent)
        # Restore the saved size and position
        settings.positions.restore_window_position(
            self.ui.dialog_edit_service, SECTION_WINDOW_NAME)
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
        self.model = services
        self.selected_iter = None
        self.name = ''
        self.description = ''
        # Connect signals from the glade file to the module functions
        self.ui.connect_signals(self)

    def show(self, name, description, title, treeiter):
        """Show the Services detail dialog"""
        self.ui.txt_name.set_text(name)
        self.ui.txt_description.set_text(description)
        self.ui.txt_name.grab_focus()
        self.ui.dialog_edit_service.set_title(title)
        self.selected_iter = treeiter
        response = self.ui.dialog_edit_service.run()
        self.ui.dialog_edit_service.hide()
        self.name = self.ui.txt_name.get_text().strip()
        self.description = self.ui.txt_description.get_text().strip()
        return response

    def destroy(self):
        """Destroy the Service detail dialog"""
        settings.positions.save_window_position(
            self.ui.dialog_edit_service, SECTION_WINDOW_NAME)
        self.ui.dialog_edit_service.destroy()
        self.ui.dialog_edit_service = None

    def on_action_confirm_activate(self, action):
        """Check che service configuration before confirm"""
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
            # Show error for missing service name
            show_error_message_on_infobar(
                self.ui.txt_name,
                _('The service name is missing'))
        elif '\'' in name or '\\' in name or '/' in name or ',' in name:
            # Show error for invalid service name
            show_error_message_on_infobar(
                self.ui.txt_name,
                _('The service name is invalid'))
        elif self.model.get_iter(name) not in (None, self.selected_iter):
            # Show error for existing service name
            show_error_message_on_infobar(
                self.ui.txt_name,
                _('A service with that name already exists'))
        elif len(description) == 0:
            # Show error for missing service description
            show_error_message_on_infobar(
                self.ui.txt_description,
                _('The service description is missing'))
        elif '\'' in description or '\\' in description:
            # Show error for invalid service description
            show_error_message_on_infobar(
                self.ui.txt_description,
                _('The service description is invalid'))
        else:
            self.ui.dialog_edit_service.response(Gtk.ResponseType.OK)

    def on_infobar_error_message_response(self, widget, response_id):
        """Close the infobar"""
        if response_id == Gtk.ResponseType.CLOSE:
            self.ui.infobar_error_message.set_visible(False)

    def on_txt_name_changed(self, widget):
        """Check the service name field"""
        check_invalid_input(widget, False, False, False)

    def on_txt_description_changed(self, widget):
        """Check the service description field"""
        check_invalid_input(widget, False, True, False)
        self.ui.txt_numeric_oid.set_text(
            snmp.snmp.translate(widget.get_text().strip()) or 
            _('Unkown OID'))
