#!/usr/bin/env python

#   The Gedit XML Tools plugin provides many useful tools for XML development.
#   Copyright (C) 2008  Simon Wenner, Copyright (C) 2012  Jono Finger
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.

from gi.repository import Gtk, Gedit, GObject
from lxml import etree

# Tools menu items
ui_str = """<ui>
  <menubar name="MenuBar">
    <menu name="ToolsMenu" action="Tools">
      <placeholder name="ToolsOps_2">
        <menuitem name="XMLTools1" action="XMLvalidate"/>
        <menuitem name="XMLTools2" action="XMLrelaxng"/>
        <menuitem name="XMLTools3" action="XMLxpath"/>
      </placeholder>
    </menu>
  </menubar>
</ui>
"""

def validateXML(xml_string):

    try:
        etree.clear_error_log()
        parser = etree.XMLParser()
        xml = etree.fromstring(xml_string, parser)
        return xml
    except etree.XMLSyntaxError as e:
        error_list = []
        for error in e.error_log:
            error_list.append((error.line, error.message))
        return error_list
    except Exception as e:
        error_list = []
        error_list.append((0, "unknown error " + str(e)))
        return error_list

def validateRelaxNG(xml):

    try:
        rng = etree.RelaxNG(xml)
        return rng
    except etree.RelaxNGError as e:
        error_list = []
        for error in e.error_log:
            error_list.append((error.line, error.message))
        return error_list
    except Exception as e:
        error_list = []
        error_list.append((0, "unknown error " + str(e)))
        return error_list

def runXpath(xml, xpath_query):

    result = ""
    try:
        xRes = xml.xpath(xpath_query)

        for x in xRes:
            result += etree.tostring(x) + "\n"
    except Exception as e:
        result = "XPath syntax error: " + str(e) + "\n"
    return result


class XMLToolsWindowHelper:
        
    def __init__(self, plugin, window):

        self._window = window
        self._plugin = plugin
        
        # add bottom panel field
        self._scroll_field = Gtk.ScrolledWindow()
        self._panel_field = Gtk.TextView()
        self._output_buffer = self._panel_field.get_buffer()
        self._scroll_field.add_with_viewport(self._panel_field)
        
        # set properties of panel field
        self._panel_field.set_editable(False)
        self._scroll_field.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self._scroll_field.show_all()
        
        panel = window.get_bottom_panel()
        image = Gtk.Image()
        image.set_from_stock(Gtk.STOCK_DND_MULTIPLE, Gtk.IconSize.BUTTON)
        panel.add_item(self._scroll_field, "XML Tools", "XML Tools", image)

        # Insert menu items
        self._insert_menu()

    def deactivate(self):
        # Remove any installed menu items
        self._remove_menu()
        
        panel = self._window.get_bottom_panel()
        panel.remove_item(self._scroll_field)
        self._scroll_field = None

        self._window = None
        self._plugin = None
        self._action_group = None

    def _insert_menu(self):

        manager = self._window.get_ui_manager()

        self._action_group = Gtk.ActionGroup("XMLToolsPyPluginActions")
        self._action_group.add_actions([("XMLvalidate", None, _("Validate XML"),
                                        'F5', _("Validate an XML file"),
                                        self.validate_document)])
        self._action_group.add_actions([("XMLrelaxng", None, _("Validate RelaxNG"),
                                        None, _("Validate an RelaxNG file"),
                                        self.validate_relaxng)])
        self._action_group.add_actions([("XMLxpath", None, _("Run XPath query"),
                                        None, _("XPath query editor"),
                                        self.create_xpath_query_editor)])                             

        manager.insert_action_group(self._action_group, -1)

        self._ui_id = manager.add_ui_from_string(ui_str)

    def _remove_menu(self):
        manager = self._window.get_ui_manager()
        manager.remove_ui(self._ui_id)
        manager.remove_action_group(self._action_group)
        manager.ensure_update()

    def update_ui(self):
        self._action_group.set_sensitive(self._window.get_active_document() != None)

    def create_xpath_query_editor(self, action):
        qwin = XMLQueryWindow(self)
        
    def validate_document(self, action):
        doc = self._window.get_active_document()
        if not doc:
            return
        
        buff = "Validating: " + doc.get_uri_for_display() + "\n"

        xmlText = doc.get_text(doc.get_start_iter(), doc.get_end_iter(), True)
        validateResult = validateXML(xmlText)

        if type(validateResult) is etree._Element :
            buff += "XML is valid!"
        else:
            buff += "XML is NOT valid!\n"
            for t in validateResult:
                buff += "Error on line: " + str(t[0]) + " -- " + t[1] + "\n"

        self._output_buffer.set_text(buff)
        panel = self._window.get_bottom_panel()
        panel.activate_item(self._scroll_field)
        panel.set_property("visible", True)
    
    def validate_relaxng(self, action):
        doc = self._window.get_active_document()
        if not doc:
            return
        
        buff = "Validating: " + doc.get_uri_for_display() + "\n"

        xmlText = doc.get_text(doc.get_start_iter(), doc.get_end_iter(), True)
        validateXmlResult = validateXML(xmlText)

        if type(validateXmlResult) is etree._Element :
            validateRngResult = validateRelaxNG(validateXmlResult)

            if type(validateRngResult) is etree.RelaxNG :
                buff += "RelaxNG is valid!"
            else:
                buff += "RelaxNG is NOT valid!\n"
                for t in validateRngResult:
                    buff += "Error on line: " + str(t[0]) + " -- " + t[1] + "\n"

        else:
            buff += "XML is NOT valid!\n"
            for t in validateXmlResult:
                buff += "Error on line: " + str(t[0]) + " -- " + t[1] + "\n"
                
        self._output_buffer.set_text(buff)
        panel = self._window.get_bottom_panel()
        panel.activate_item(self._scroll_field)
        panel.set_property("visible", True)
    
    def xpath_query_on_document(self, xpath_string):
        doc = self._window.get_active_document()
        if not doc:
            return

        buff = "XPath result:\n"

        xmlText = doc.get_text(doc.get_start_iter(), doc.get_end_iter(), True)
        validateXmlResult = validateXML(xmlText)
        
        if type(validateXmlResult) is etree._Element :
            buff += runXpath(validateXmlResult, xpath_string)
        else:
            buff += "XML is NOT valid!\n"
            for t in validateXmlResult:
                buff += "Error on line: " + str(t[0]) + " -- " + t[1] + "\n"
        
        # show result
        self._output_buffer.set_text(buff)
        panel = self._window.get_bottom_panel()
        panel.activate_item(self._scroll_field)
        panel.set_property("visible", True)
        

class XMLQueryWindow:
    def __init__(self, window_helper):
        self._window_helper = window_helper

        self._window = Gtk.Window()
        self._window.set_title("XPath query editor")
        self._window.set_border_width(10)
        self._window.set_position(Gtk.WindowPosition.CENTER)
        
        self._window.connect("delete_event", self.delete_event)
        
        self.field = Gtk.ScrolledWindow()
        self.tv = Gtk.TextView()
        self.field.add_with_viewport(self.tv)
        self.field.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.field.set_size_request(400, 100)
        
        vbox = Gtk.VBox(False, 10)
        vbox.pack_start(self.field, True, True, 0)
        hbox = Gtk.HBox(False, 0)
        
        button = Gtk.Button(None, Gtk.STOCK_EXECUTE)
        button.connect("clicked", self.query_event, None)
        hbox.pack_start(button, False, False, 0)
        
        button = Gtk.Button(None, Gtk.STOCK_CLEAR)
        button.connect("clicked", self.clear_event, None)
        hbox.pack_start(button, False, False, 0)
        
        button = Gtk.Button(None, Gtk.STOCK_CLOSE)
        button.connect("clicked", self.delete_event, None)
        hbox.pack_end(button, False, False, 0)
        
        vbox.pack_start(hbox, False, False, 0)  
        self._window.add(vbox)
    
        self._window.show_all()

    def delete_event(self, widget, event, data=None):
        self._window.destroy()
        return False
        
    def query_event(self, widget, event, data=None):
        buff = self.tv.get_buffer()
        self._window_helper.xpath_query_on_document(buff.get_text(buff.get_start_iter(), buff.get_end_iter(), True))
        return False
        
    def clear_event(self, widget, event, data=None):
        self.tv.set_buffer(Gtk.TextBuffer())
        return False


class WindowActivatable(GObject.Object, Gedit.WindowActivatable):

    window = GObject.property(type=Gedit.Window)

    def __init__(self):
        GObject.Object.__init__(self)
        self._instances = {}

    def do_activate(self):
        self._instances[self.window] = XMLToolsWindowHelper(self, self.window)

    def do_deactivate(self):
        self._instances[self.window].deactivate()
        del self._instances[self.window]

    def update_ui(self):
        self._instances[self.window].update_ui()
