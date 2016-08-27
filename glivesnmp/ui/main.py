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
import json

from gi.repository import Gtk
from gi.repository import Gdk

from glivesnmp.constants import (
    APP_NAME,
    FILE_SETTINGS, FILE_WINDOWS_POSITION, FILE_SERVICES, FILE_DEVICES,
    DIR_HOSTS)
from glivesnmp.functions import (
    get_ui_file, get_treeview_selected_row, show_popup_menu, text, _)
import glivesnmp.preferences as preferences
import glivesnmp.settings as settings
import glivesnmp.snmp as snmp
from glivesnmp.gtkbuilder_loader import GtkBuilderLoader

import glivesnmp.models.services as model_services
import glivesnmp.models.devices as model_devices
from glivesnmp.models.device_info import DeviceInfo
from glivesnmp.models.service_info import ServiceInfo
from glivesnmp.models.host_info import HostInfo
from glivesnmp.models.hosts import ModelHosts
from glivesnmp.models.group_info import GroupInfo
from glivesnmp.models.groups import ModelGroups

from glivesnmp.ui.about import UIAbout
from glivesnmp.ui.services import UIServices
from glivesnmp.ui.devices import UIDevices
from glivesnmp.ui.groups import UIGroups
from glivesnmp.ui.host import UIHost
from glivesnmp.ui.snmp_values import UISNMPValues
from glivesnmp.ui.message_dialog import (
    show_message_dialog, UIMessageDialogNoYes, UIMessageDialogClose)

SECTION_WINDOW_NAME = 'main'
# Options for services
OPTION_SERVICE_DESCRIPTION = 'description'
# Options for devices
OPTION_DEVICE_DESCRIPTION = 'description'
OPTION_DEVICE_SERVICES = 'services'
# Section and options for host
SECTION_HOST = 'host'
OPTION_HOST_NAME = 'name'
OPTION_HOST_DESCRIPTION = 'description'
OPTION_HOST_PROTOCOL = 'protocol'
OPTION_HOST_ADDRESS = 'address'
OPTION_HOST_PORT = 'port'
OPTION_HOST_VERSION = 'version'
OPTION_HOST_COMMUNITY = 'community'
OPTION_HOST_DEVICE = 'device'
OPTION_HOST_REQUESTS = 'requests'


class UIMain(object):
    def __init__(self, application):
        self.application = application
        snmp.snmp = snmp.SNMP()
        # Load settings
        settings.settings = settings.Settings(FILE_SETTINGS, False)
        settings.positions = settings.Settings(FILE_WINDOWS_POSITION, False)
        settings.services = settings.Settings(FILE_SERVICES, False)
        settings.devices = settings.Settings(FILE_DEVICES, False)
        preferences.preferences = preferences.Preferences()
        # Load services
        for key in settings.services.get_sections():
            model_services.services[key] = ServiceInfo(
                name=key,
                description=settings.services.get(
                    key, OPTION_SERVICE_DESCRIPTION))
        # Load devices
        for key in settings.devices.get_sections():
            model_devices.devices[key] = DeviceInfo(
                name=key,
                description=settings.devices.get(
                    key, OPTION_DEVICE_DESCRIPTION),
                services=settings.devices.get_list(
                    key, OPTION_DEVICE_SERVICES))
        self.loadUI()
        self.model_hosts = ModelHosts(self.ui.store_hosts)
        self.model_groups = ModelGroups(self.ui.store_groups)
        # Load the groups and hosts list
        self.hosts = {}
        self.reload_groups()
        # Sort the data in the models
        self.model_groups.model.set_sort_column_id(
            self.ui.column_group.get_sort_column_id(),
            Gtk.SortType.ASCENDING)
        self.model_hosts.model.set_sort_column_id(
            self.ui.column_name.get_sort_column_id(),
            Gtk.SortType.ASCENDING)
        # Automatically select the first host if any
        self.ui.tvw_groups.set_cursor(0)
        if self.model_hosts.count() > 0:
            self.ui.tvw_connections.set_cursor(0)
        # Restore the saved size and position
        settings.positions.restore_window_position(
            self.ui.win_main, SECTION_WINDOW_NAME)

    def loadUI(self):
        """Load the interface UI"""
        self.ui = GtkBuilderLoader(get_ui_file('main.glade'))
        self.ui.win_main.set_application(self.application)
        self.ui.win_main.set_title(APP_NAME)
        # Initialize actions
        for widget in self.ui.get_objects_by_type(Gtk.Action):
            # Connect the actions accelerators
            widget.connect_accelerator()
            # Set labels
            widget.set_label(text(widget.get_label()))
        # Initialize tooltips
        for widget in self.ui.get_objects_by_type(Gtk.ToolButton):
            action = widget.get_related_action()
            if action:
                widget.set_tooltip_text(action.get_label().replace('_', ''))
        # Initialize column headers
        for widget in self.ui.get_objects_by_type(Gtk.TreeViewColumn):
            widget.set_title(text(widget.get_title()))
        # Set list items row height
        icon_size = preferences.ICON_SIZE
        self.ui.cell_name.props.height = preferences.get(icon_size)
        self.ui.cell_group_name.props.height = preferences.get(icon_size)
        # Set groups visibility
        self.ui.scroll_groups.set_visible(
            preferences.get(preferences.GROUPS_SHOW))
        # Add a Gtk.Headerbar, only for GTK+ 3.10.0 and higher
        if (not Gtk.check_version(3, 10, 0) and
                not preferences.get(preferences.HEADERBARS_DISABLE)):
            self.load_ui_headerbar()
            if preferences.get(preferences.HEADERBARS_REMOVE_TOOLBAR):
                # This is only for development, it should always be True
                # Remove the redundant toolbar
                self.ui.toolbar_main.destroy()
            # Flatten the Gtk.ScrolledWindows
            self.ui.scroll_groups.set_shadow_type(Gtk.ShadowType.NONE)
            self.ui.scroll_connections.set_shadow_type(Gtk.ShadowType.NONE)
        # Connect signals from the glade file to the module functions
        self.ui.connect_signals(self)

    def load_ui_headerbar(self):
        """Add a Gtk.HeaderBar to the window with buttons"""
        def create_button_from_action(action):
            """Create a new Gtk.Button from a Gtk.Action"""
            if isinstance(action, Gtk.ToggleAction):
                new_button = Gtk.ToggleButton()
            else:
                new_button = Gtk.Button()
            new_button.set_use_action_appearance(False)
            new_button.set_related_action(action)
            # Use icon from the action
            icon_name = action.get_icon_name()
            if preferences.get(preferences.HEADERBARS_SYMBOLIC_ICONS):
                icon_name += '-symbolic'
            # Get desired icon size
            icon_size = (Gtk.IconSize.BUTTON
                         if preferences.get(preferences.HEADERBARS_SMALL_ICONS)
                         else Gtk.IconSize.LARGE_TOOLBAR)
            new_button.set_image(Gtk.Image.new_from_icon_name(icon_name,
                                                              icon_size))
            # Set the tooltip from the action label
            new_button.set_tooltip_text(action.get_label().replace('_', ''))
            return new_button
        # Add the Gtk.HeaderBar
        header_bar = Gtk.HeaderBar()
        header_bar.props.title = self.ui.win_main.get_title()
        header_bar.set_show_close_button(True)
        self.ui.win_main.set_titlebar(header_bar)
        # Add buttons to the left side
        for action in (self.ui.action_new, self.ui.action_edit,
                       self.ui.action_connect, self.ui.action_delete):
            header_bar.pack_start(create_button_from_action(action))
        # Add buttons to the right side (in reverse order)
        for action in reversed((self.ui.action_services,
                                self.ui.action_devices,
                                self.ui.action_groups,
                                self.ui.action_about)):
            header_bar.pack_end(create_button_from_action(action))

    def run(self):
        """Show the UI"""
        self.ui.win_main.show_all()

    def on_win_main_delete_event(self, widget, event):
        """Save the settings and close the application"""
        settings.positions.save_window_position(
            self.ui.win_main, SECTION_WINDOW_NAME)
        settings.positions.save()
        settings.services.save()
        settings.devices.save()
        settings.settings.save()
        self.application.quit()

    def on_action_about_activate(self, action):
        """Show the about dialog"""
        dialog = UIAbout(self.ui.win_main)
        dialog.show()
        dialog.destroy()

    def on_action_quit_activate(self, action):
        """Close the application by closing the main window"""
        event = Gdk.Event()
        event.key.type = Gdk.EventType.DELETE
        self.ui.win_main.event(event)

    def on_action_services_activate(self, action):
        """Edit services"""
        selected_row = get_treeview_selected_row(self.ui.tvw_connections)
        if selected_row:
            iter_parent = self.ui.store_hosts.iter_parent(selected_row)
            selected_path = self.model_hosts.model[selected_row].path
            # Get the path of the host
            if iter_parent is None:
                tree_path = self.model_hosts.model[selected_row].path
            else:
                tree_path = self.model_hosts.model[iter_parent].path
        dialog_services = UIServices(parent=self.ui.win_main)
        # Load services list
        dialog_services.model.load(model_services.services)
        dialog_services.show()
        # Get the new services list, clear and store the list again
        model_services.services = dialog_services.model.dump()
        dialog_services.destroy()
        settings.services.clear()
        for key in model_services.services.iterkeys():
            settings.services.set(
                section=key,
                option=OPTION_SERVICE_DESCRIPTION,
                value=model_services.services[key].description)
        self.reload_hosts()
        if selected_row:
            # Automatically select again the previously selected row
            self.ui.tvw_connections.set_cursor(path=selected_path,
                                               column=None,
                                               start_editing=False)

    def on_action_devices_activate(self, action):
        """Edit devices"""
        selected_row = get_treeview_selected_row(self.ui.tvw_connections)
        if selected_row:
            iter_parent = self.ui.store_hosts.iter_parent(selected_row)
            selected_path = self.model_hosts.model[selected_row].path
            # Get the path of the host
            if iter_parent is None:
                tree_path = self.model_hosts.model[selected_row].path
            else:
                tree_path = self.model_hosts.model[iter_parent].path
        dialog_devices = UIDevices(parent=self.ui.win_main)
        # Load devices list
        dialog_devices.model.load(model_devices.devices)
        dialog_devices.show()
        # Get the new devices list, clear and store the list again
        model_devices.devices = dialog_devices.model.dump()
        dialog_devices.destroy()
        settings.devices.clear()
        for key in model_devices.devices.iterkeys():
            settings.devices.set(
                section=key,
                option=OPTION_DEVICE_DESCRIPTION,
                value=model_devices.devices[key].description)
            settings.devices.set(
                section=key,
                option=OPTION_DEVICE_SERVICES,
                value=','.join(model_devices.devices[key].services))
        self.reload_hosts()
        if selected_row:
            # Automatically select again the previously selected row
            self.ui.tvw_connections.set_cursor(path=selected_path,
                                               column=None,
                                               start_editing=False)

    def reload_hosts(self):
        """Load hosts from the settings files"""
        self.model_hosts.clear()
        self.hosts.clear()
        hosts_path = self.get_current_group_path()
        # Fix bug where the groups model isn't yet emptied, resulting in
        # being still used after a clear, then an invalid path
        if not os.path.isdir(hosts_path):
            return
        for filename in os.listdir(hosts_path):
            # Skip folders, used for groups
            if os.path.isdir(os.path.join(hosts_path, filename)):
                continue
            settings_host = settings.Settings(
                filename=os.path.join(hosts_path, filename),
                case_sensitive=True)
            host = HostInfo(
                name=settings_host.get(SECTION_HOST, OPTION_HOST_NAME),
                description=settings_host.get(SECTION_HOST,
                                              OPTION_HOST_DESCRIPTION),
                protocol=settings_host.get(SECTION_HOST, OPTION_HOST_PROTOCOL),
                address=settings_host.get(SECTION_HOST, OPTION_HOST_ADDRESS),
                port_number=settings_host.get_int(SECTION_HOST,
                                                  OPTION_HOST_PORT),
                version=settings_host.get_int(SECTION_HOST,
                                              OPTION_HOST_VERSION),
                community=settings_host.get(SECTION_HOST,
                                            OPTION_HOST_COMMUNITY),
                device=settings_host.get(SECTION_HOST, OPTION_HOST_DEVICE),
                requests=settings_host.get_int(SECTION_HOST,
                                               OPTION_HOST_REQUESTS))
            self.add_host(host, False)

    def add_host(self, host, update_settings):
        """Add a new host along as with its destinations"""
        # Add the host to the data and to the model
        self.hosts[host.name] = host
        treeiter = self.model_hosts.add_data(host)
        # Update settings file if requested
        if update_settings:
            hosts_path = self.get_current_group_path()
            settings_host = settings.Settings(
                filename=os.path.join(hosts_path, '%s.conf' % host.name),
                case_sensitive=True)
            # Add host information
            settings_host.set(SECTION_HOST, OPTION_HOST_NAME, host.name)
            settings_host.set(SECTION_HOST, OPTION_HOST_DESCRIPTION,
                              host.description)
            settings_host.set(SECTION_HOST, OPTION_HOST_PROTOCOL,
                              host.protocol)
            settings_host.set(SECTION_HOST, OPTION_HOST_ADDRESS, host.address)
            settings_host.set_int(SECTION_HOST, OPTION_HOST_PORT,
                                  host.port_number)
            settings_host.set_int(SECTION_HOST, OPTION_HOST_VERSION,
                                  host.version)
            settings_host.set(SECTION_HOST, OPTION_HOST_COMMUNITY,
                              host.community)
            settings_host.set(SECTION_HOST, OPTION_HOST_DEVICE, host.device)
            settings_host.set_int(SECTION_HOST, OPTION_HOST_REQUESTS,
                                  host.requests)
            # Save the settings to the file
            settings_host.save()

    def remove_host(self, name):
        """Remove a host by its name"""
        hosts_path = self.get_current_group_path()
        filename = os.path.join(hosts_path, '%s.conf' % name)
        if os.path.isfile(filename):
            os.unlink(filename)
        self.hosts.pop(name)
        self.model_hosts.remove(self.model_hosts.get_iter(name))

    def reload_groups(self):
        """Load groups from hosts folder"""
        self.model_groups.clear()
        # Always add a default group
        self.model_groups.add_data(GroupInfo('', _('Default group')))
        for filename in os.listdir(DIR_HOSTS):
            if os.path.isdir(os.path.join(DIR_HOSTS, filename)):
                # For each folder add a new group
                self.model_groups.add_data(GroupInfo(filename, filename))

    def on_action_new_activate(self, action):
        """Define a new host"""
        dialog = UIHost(parent=self.ui.win_main,
                        hosts=self.model_hosts)
        response = dialog.show(name='',
                               description='',
                               protocol='UDP',
                               address='',
                               port_number=161,
                               version=1,
                               community='public',
                               device='',
                               requests=0,
                               title=_('Add a new host'),
                               treeiter=None)
        if response == Gtk.ResponseType.OK:
            host = HostInfo(dialog.name, dialog.description, dialog.protocol,
                            dialog.address, dialog.port_number, dialog.version,
                            dialog.community, dialog.device, dialog.requests)
            self.add_host(host=host,
                          update_settings=True)
            # Automatically select the newly added host
            self.ui.tvw_connections.set_cursor(
                path=self.model_hosts.get_path_by_name(dialog.name),
                column=None,
                start_editing=False)
        dialog.destroy()

    def on_action_edit_activate(self, action):
        """Define a new host"""
        selected_row = get_treeview_selected_row(self.ui.tvw_connections)
        if selected_row:
            dialog = UIHost(parent=self.ui.win_main,
                            hosts=self.model_hosts)
            # Show the edit host dialog
            model = self.model_hosts
            name = model.get_key(selected_row)
            selected_iter = model.get_iter(name)
            response = dialog.show(
                name=name,
                description=model.get_description(selected_row),
                protocol=model.get_protocol(selected_row),
                address=model.get_address(selected_row),
                port_number=model.get_port_number(selected_row),
                version=model.get_version(selected_row),
                community=model.get_community(selected_row),
                device=model.get_device(selected_row),
                requests=model.get_requests(selected_row),
                title=_('Edit host'),
                treeiter=selected_iter)
            if response == Gtk.ResponseType.OK:
                # Remove older host and add the newer
                host = HostInfo(dialog.name, dialog.description,
                                dialog.protocol, dialog.address,
                                dialog.port_number, dialog.version,
                                dialog.community, dialog.device,
                                dialog.requests)
                self.remove_host(name)
                self.add_host(host=host,
                              update_settings=True)
                # Get the path of the host
                tree_path = self.model_hosts.get_path_by_name(dialog.name)
                # Automatically select again the previously selected host
                self.ui.tvw_connections.set_cursor(path=tree_path,
                                                   column=None,
                                                   start_editing=False)

    def on_tvw_connections_row_activated(self, widget, treepath, column):
        """Edit the selected row on activation"""
        selected_row = get_treeview_selected_row(self.ui.tvw_connections)
        if selected_row:
            # Start host connection
            self.ui.action_connect.activate()

    def on_action_delete_activate(self, action):
        """Remove the selected host"""
        selected_row = get_treeview_selected_row(self.ui.tvw_connections)
        if selected_row and show_message_dialog(
                class_=UIMessageDialogNoYes,
                parent=self.ui.win_main,
                message_type=Gtk.MessageType.QUESTION,
                title=None,
                msg1=_("Remove host"),
                msg2=_("Remove the selected host?"),
                is_response_id=Gtk.ResponseType.YES):
            self.remove_host(self.model_hosts.get_key(selected_row))

    def on_action_copy_activate(self, action):
        """Copy the selected host to another"""
        selected_row = get_treeview_selected_row(self.ui.tvw_connections)
        if selected_row:
            name = self.model_hosts.get_key(selected_row)
            description = self.model_hosts.get_description(selected_row)
            selected_iter = self.model_hosts.get_iter(name)
            dialog = UIHost(parent=self.ui.win_main,
                            hosts=self.model_hosts)
            # Show the edit host dialog
            response = dialog.show(name=_('Copy of %s') % name,
                                   description='',
                                   title=_('Copy host'),
                                   treeiter=None)
            if response == Gtk.ResponseType.OK:
                host = HostInfo(dialog.name, dialog.description,
                                dialog.protocol, dialog.address,
                                dialog.port_number, dialog.version,
                                dialog.community, dialog.device,
                                dialog.requests)
                self.add_host(host=host,
                              update_settings=True)
                # Get the path of the host
                tree_path = self.model_hosts.get_path_by_name(dialog.name)
                # Automatically select again the previously selected host
                self.ui.tvw_connections.set_cursor(path=tree_path,
                                                   column=None,
                                                   start_editing=False)

    def on_tvw_connections_cursor_changed(self, widget):
        """Set actions sensitiveness for host and connection"""
        if get_treeview_selected_row(self.ui.tvw_connections):
            self.ui.actions_connection.set_sensitive(True)
            self.ui.actions_host.set_sensitive(True)

    def on_action_connect_activate(self, action):
        """Establish the connection for the destination"""
        selected_row = get_treeview_selected_row(self.ui.tvw_connections)
        if selected_row:
            model = self.model_hosts
            dialog = UISNMPValues(
                parent=self.ui.win_main,
                host=HostInfo(name=model.get_key(selected_row),
                              description=model.get_description(selected_row),
                              protocol=model.get_protocol(selected_row),
                              address=model.get_address(selected_row),
                              port_number=model.get_port_number(selected_row),
                              version=model.get_version(selected_row),
                              community=model.get_community(selected_row),
                              device=model.get_device(selected_row),
                              requests=model.get_requests(selected_row))
            )
            dialog.show()

    def get_current_group_path(self):
        """Return the path of the currently selected group"""
        selected_row = get_treeview_selected_row(self.ui.tvw_groups)
        group_name = self.model_groups.get_key(selected_row) if selected_row \
            else ''
        return os.path.join(DIR_HOSTS, group_name) if group_name else DIR_HOSTS

    def on_tvw_groups_cursor_changed(self, widget):
        """Set actions sensitiveness for host and connection"""
        if get_treeview_selected_row(self.ui.tvw_groups):
            self.reload_hosts()
            # Automatically select the first host for the group
            self.ui.tvw_connections.set_cursor(0)

    def on_action_groups_activate(self, widget):
        """Edit groups"""
        dialog_groups = UIGroups(parent=self.ui.win_main)
        dialog_groups.model = self.model_groups
        dialog_groups.ui.tvw_groups.set_model(self.model_groups.model)
        dialog_groups.show()
        dialog_groups.destroy()

    def on_tvw_groups_button_release_event(self, widget, event):
        """Show groups popup menu on right click"""
        if event.button == Gdk.BUTTON_SECONDARY:
            show_popup_menu(self.ui.menu_groups, event.button)

    def on_tvw_connections_button_release_event(self, widget, event):
        """Show connections popup menu on right click"""
        if event.button == Gdk.BUTTON_SECONDARY:
            show_popup_menu(self.ui.menu_connections, event.button)

    def on_action_group_previous_activate(self, action):
        """Move to the previous group"""
        selected_row = get_treeview_selected_row(self.ui.tvw_groups)
        new_iter = self.model_groups.model.iter_previous(selected_row)
        if new_iter:
            # Select the newly selected row in the groups list
            new_path = self.model_groups.get_path(new_iter)
            self.ui.tvw_groups.set_cursor(new_path)

    def on_action_group_next_activate(self, action):
        """Move to the next group"""
        selected_row = get_treeview_selected_row(self.ui.tvw_groups)
        new_iter = self.model_groups.model.iter_next(selected_row)
        if new_iter:
            # Select the newly selected row in the groups list
            new_path = self.model_groups.get_path(new_iter)
            self.ui.tvw_groups.set_cursor(new_path)
