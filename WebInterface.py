import copy
import json
from multiprocessing import Event
from multiprocessing import Queue

from remi import App, start

from UIPanels import *

cmdQueue: Queue
dataQueue: Queue
ui_is_active: Event

# liveConfig is the config file currently running on the ArtnetRouter
liveConfig: dict

# configDatabase is a local copy that we can work on in our editors
configDatabase: dict


def make_unique_tag(data: dict):
    """
    Given a dictionary, return a unique stringified integer tag that is not in the dictionary.
    :param data:
    :return: tag
    """
    n = len(data)
    while True:
        tag = str(n)
        if tag not in data:
            return tag
        n += 1


class RemiWrapper:
    def __init__(self, cfgDb, cmdQ, dataQ, ui_flag):
        global cmdQueue
        cmdQueue = cmdQ

        global dataQueue
        dataQueue = dataQ

        global ui_is_active
        ui_is_active = ui_flag

        global liveConfig
        liveConfig = cfgDb

        global configDatabase
        configDatabase = copy.deepcopy(cfgDb)

        webIp = cfgDb['system'].get('ipWebInterface')
        webPort = int(cfgDb['system'].get('portWebInterface'))

        start(Flamecaster, address=webIp, port=webPort, start_browser=False, update_interval=0.1, debug=False)


# noinspection PyUnusedLocal
class Flamecaster(App):
    status_table = None
    devices = {}
    baseContainer = None
    statusPanel = None
    systemPanel = None
    devicesPanel = None
    universesPanel = None

    def __init__(self, *args):
        super(Flamecaster, self).__init__(*args)
        self.devices = dict()

    def idle(self):
        if not ui_is_active.is_set():
            ui_is_active.set()
        if not dataQueue.empty():
            # get the JSON status strings from the queue
            msg = json.loads(dataQueue.get())
            # if top level key is "name", it's a device status message
            if 'name' in msg:
                # update the device dictionary with the new status
                self.devices[msg['name']] = msg

            # reconfigure the status table for the updated device list
            # leave the top row for labels.  The bottom row is blank
            # because it will expand to fill any remaining space in the
            #
            self.status_table.set_row_count(3 + len(self.devices))
            self.fill_status_table()
            self.status_table.redraw()

    def main(self):

        # The root Container
        baseContainer = Container()
        baseContainer.attributes['class'] = "Container  "
        baseContainer.attributes['editor_baseclass'] = "Container"
        baseContainer.attributes['editor_varname'] = "baseContainer"
        baseContainer.attributes['editor_tag_type'] = "widget"
        baseContainer.attributes['editor_newclass'] = "False"
        baseContainer.attributes['editor_constructor'] = "()"
        baseContainer.style['position'] = "absolute"
        baseContainer.style['overflow'] = "auto"
        baseContainer.style['left'] = "0px"
        baseContainer.style['top'] = "0px"
        baseContainer.style['margin'] = "0px"
        baseContainer.style['border-style'] = "solid"
        baseContainer.style['width'] = "670px"
        baseContainer.style['display'] = "block"
        baseContainer.style['border-width'] = "1px"
        baseContainer.style['height'] = "550px"

        # The menuContainer on the left side - holds the buttons to switch between the contentWidgets
        menuContainer = Container()
        menuContainer.attributes['class'] = "Container"
        menuContainer.attributes['editor_baseclass'] = "Container"
        menuContainer.attributes['editor_varname'] = "menuContainer"
        menuContainer.attributes['editor_tag_type'] = "widget"
        menuContainer.attributes['editor_newclass'] = "False"
        menuContainer.attributes['editor_constructor'] = "()"
        menuContainer.style['position'] = "absolute"
        menuContainer.style['overflow'] = "auto"
        menuContainer.style['left'] = "10px"
        menuContainer.style['top'] = "10px"
        menuContainer.style['margin'] = "0px"
        menuContainer.style['border-style'] = "solid"
        menuContainer.style['width'] = "180px"
        menuContainer.style['display'] = "block"
        menuContainer.style['border-width'] = "1px"
        menuContainer.style['height'] = "500px"

        btnStatus = Button('Status')
        btnStatus.attributes['class'] = "Button"
        btnStatus.attributes['editor_baseclass'] = "Button"
        btnStatus.attributes['editor_varname'] = "btnStatus"
        btnStatus.attributes['editor_tag_type'] = "widget"
        btnStatus.attributes['editor_newclass'] = "False"
        btnStatus.attributes['editor_constructor'] = "('Status')"
        btnStatus.style['position'] = "absolute"
        btnStatus.style['overflow'] = "auto"
        btnStatus.style['left'] = "5px"
        btnStatus.style['top'] = "10px"
        btnStatus.style['margin'] = "0px"
        btnStatus.style['width'] = "150px"
        btnStatus.style['display'] = "block"
        btnStatus.style['height'] = "30px"
        menuContainer.append(btnStatus, 'btnStatus')

        btnSystem = Button('System')
        btnSystem.attributes['class'] = "Button"
        btnSystem.attributes['editor_baseclass'] = "Button"
        btnSystem.attributes['editor_varname'] = "btnSystem"
        btnSystem.attributes['editor_tag_type'] = "widget"
        btnSystem.attributes['editor_newclass'] = "False"
        btnSystem.attributes['editor_constructor'] = "('System')"
        btnSystem.style['position'] = "absolute"
        btnSystem.style['overflow'] = "auto"
        btnSystem.style['left'] = "5px"
        btnSystem.style['top'] = "60px"
        btnSystem.style['margin'] = "0px"
        btnSystem.style['width'] = "150px"
        btnSystem.style['display'] = "block"
        btnSystem.style['height'] = "30px"
        menuContainer.append(btnSystem, 'btnSystem')

        btnDevices = Button('Pixelblazes')
        btnDevices.attributes['class'] = "Button"
        btnDevices.attributes['editor_baseclass'] = "Button"
        btnDevices.attributes['editor_varname'] = "btnDevices"
        btnDevices.attributes['editor_tag_type'] = "widget"
        btnDevices.attributes['editor_newclass'] = "False"
        btnDevices.attributes['editor_constructor'] = "('Pixelblazes')"
        btnDevices.style['position'] = "absolute"
        btnDevices.style['overflow'] = "auto"
        btnDevices.style['left'] = "5px"
        btnDevices.style['top'] = "110px"
        btnDevices.style['margin'] = "0px"
        btnDevices.style['width'] = "150px"
        btnDevices.style['display'] = "block"
        btnDevices.style['height'] = "30px"
        menuContainer.append(btnDevices, 'btnDevices')

        # Add the menuContainer to the baseContainer and define the listeners for the menu elements
        baseContainer.append(menuContainer, 'menuContainer')
        baseContainer.children['menuContainer'].children['btnSystem'].onclick.do(self.onclick_btnSystem)
        baseContainer.children['menuContainer'].children['btnStatus'].onclick.do(self.onclick_btnStatus)
        baseContainer.children['menuContainer'].children['btnDevices'].onclick.do(self.onclick_btnDevices)

        # The contentContainer
        contentContainer = Container()
        contentContainer.attributes['class'] = "Container"
        contentContainer.attributes['editor_baseclass'] = "Container"
        contentContainer.attributes['editor_varname'] = "contentContainer"
        contentContainer.attributes['editor_tag_type'] = "widget"
        contentContainer.attributes['editor_newclass'] = "False"
        contentContainer.attributes['editor_constructor'] = "()"
        contentContainer.style['position'] = "absolute"
        contentContainer.style['overflow'] = "auto"
        contentContainer.style['left'] = "200px"
        contentContainer.style['top'] = "10px"
        contentContainer.style['margin'] = "0px"
        contentContainer.style['border-style'] = "solid"
        contentContainer.style['width'] = "450px"
        contentContainer.style['display'] = "block"
        contentContainer.style['border-width'] = "1px"
        contentContainer.style['height'] = "500px"

        # Create top Level instances for the content Widgets.
        # By defining these as top Level the Widgets live even if they are not shown

        self.statusPanel = StatusContainer()
        # get a reference to the table in the screen1 Widget
        self.status_table = self.statusPanel.children['status_table']

        self.systemPanel = SystemSettingsContainer()
        self.systemPanel.set_system_text(configDatabase.get('system', {}))

        self.devicesPanel = DevicesContainer()
        self.devicesPanel.set_devices_text(configDatabase.get('devices', {}))

        self.universesPanel = UniversesContainer()
        self.universesPanel.set_universes_text({})

        # event handlers for the system panel
        self.systemPanel.children['maxFps'].onchange.do(self.on_system_setting_changed)
        self.systemPanel.children['updateInterval'].onchange.do(self.on_system_setting_changed)
        self.systemPanel.children['artNetIp'].onchange.do(self.on_system_setting_changed)
        self.systemPanel.children['artNetPort'].onchange.do(self.on_system_setting_changed)
        self.systemPanel.children['webIp'].onchange.do(self.on_system_setting_changed)
        self.systemPanel.children['webPort'].onchange.do(self.on_system_setting_changed)

        # event handlers for devices panel
        self.devicesPanel.children['pb_table'].ondblclick.do(self.ondblclick_pixelblaze_table)
        self.devicesPanel.children['btnEdit'].onclick.do(self.ondblclick_pixelblaze_table)
        self.devicesPanel.children['btnAdd'].onclick.do(self.onclick_btnAddDevice)
        self.devicesPanel.children['btnRemove'].onclick.do(self.onclick_btnRemoveDevice)
        self.devicesPanel.children['pb_table'].on_item_changed.do(self.on_device_setting_changed)

        # event handlers for universes table
        self.universesPanel.children['btnBack'].onclick.do(self.onclick_btnUniverseBack)
        self.universesPanel.children['btnAdd'].onclick.do(self.onclick_btnAddUniverse)
        self.universesPanel.children['btnRemove'].onclick.do(self.onclick_btnRemoveUniverse)
        self.universesPanel.children['u_table'].on_item_changed.do(self.on_universe_setting_changed)

        # Add the initial content to the contentContainer
        contentContainer.append(self.statusPanel, 'statusPanel')

        # Add the contentContainer to the baseContainer
        baseContainer.append(contentContainer, 'contentContainer')

        # Make the local "baseContainer" a class member of the App
        self.baseContainer = baseContainer

        # return the baseContainer as root Widget
        return self.baseContainer

    def on_system_setting_changed(self, widget, newValue):
        # find key for this widget in systemPanel
        for key in self.systemPanel.children:
            if self.systemPanel.children[key] == widget:
                break
        print('System setting for ' + key + ' changed to: ' + newValue)

    def on_device_setting_changed(self, table, item, new_value, row, column):
        """Event callback for table item change.

        Args:
            table (TableWidget): The emitter of the event.
            item (TableItem): The TableItem instance.
            new_value (str): New text content.
            row (int): row index.
            column (int): column index.
        """
        print("Devices table item changed: ", new_value, row, column)

    def on_universe_setting_changed(self, table, item, new_value, row, column):
        """Event callback for table item change.

        Args:
            table (TableWidget): The emitter of the event.
            item (TableItem): The TableItem instance.
            new_value (str): New text content.
            row (int): row index.
            column (int): column index.
        """
        print("Universes table item changed: ", new_value, row, column)

    def fill_status_table(self):
        # add information from the devices dictionary to the table
        # print(self.devices)

        lastRow = 2 + len(self.devices)
        for n in range(5):
            self.status_table.item_at(0, n).style['height'] = uiTextHeight
            self.status_table.item_at(lastRow, n).set_text("  ")

        for i, key in enumerate(self.devices):

            # the first row is reserved for the column headers
            i = i + 1
            db = self.devices[key]
            self.status_table.item_at(i, 0).set_text(key)
            self.status_table.item_at(i, 1).set_text(str(db.get('ip', '')))
            self.status_table.item_at(i, 2).set_text(str(db.get('inPps', 0)))
            self.status_table.item_at(i, 3).set_text(str(db.get('outFps', 0)))

            if db.get('connected', "false") == "true":
                self.status_table.item_at(i, 4).css_color = "rgb(0,0,0)"
                self.status_table.item_at(i, 4).set_text("Yes")
            else:
                self.status_table.item_at(i, 4).css_color = "rgb(255,0,0)"
                self.status_table.item_at(i, 4).set_text("No")

            for n in range(5):
                self.status_table.item_at(i, n).style['height'] = uiTextHeight

    def start_universe_editor(self):
        # if we're already showing the status panel, don't do anything
        if 'universesPanel' in self.baseContainer.children['contentContainer'].children.keys():
            return

        self.remove_current_content()

        # Add the status panel to the contentWidget
        self.baseContainer.children['contentContainer'].append(self.universesPanel, 'universesPanel')

    def remove_current_content(self):
        # remove the current content from the contentContainer
        # currentContent = self.baseContainer.children['contentContainer'].children
        currentContent = list(self.baseContainer.children['contentContainer'].children.values())[0]
        self.baseContainer.children['contentContainer'].remove_child(currentContent)

    # switch to the status panel
    def onclick_btnStatus(self, emitter):
        # if we're already showing the status panel, don't do anything
        if 'statusPanel' in self.baseContainer.children['contentContainer'].children.keys():
            return

        self.remove_current_content()

        # Add the status panel to the contentWidget
        self.baseContainer.children['contentContainer'].append(self.statusPanel, 'statusPanel')

    def onclick_btnSystem(self, emitter):
        # if we're already showing the system panel, don't do anything
        if 'systemPanel' in self.baseContainer.children['contentContainer'].children.keys():
            return

        self.remove_current_content()

        # Add the system panel to the contentWidget
        self.baseContainer.children['contentContainer'].append(self.systemPanel, 'systemPanel')

    def onclick_btnDevices(self, emitter):
        # if we're already showing the devices panel, don't do anything
        if 'devicesPanel' in self.baseContainer.children['contentContainer'].children.keys():
            return

        self.remove_current_content()

        # Add the status panel to the contentWidget
        self.baseContainer.children['contentContainer'].append(self.devicesPanel, 'devicesPanel')

    def onclick_btnAddDevice(self, emitter):
        # to add a device, we add it at the end of the configDatabase devices list,
        # rebuild the table, and redraw it
        data = configDatabase.get('devices', {})

        # generate a unique tag for the new device
        devTag = make_unique_tag(data)

        # add the new device to the database
        data[devTag] = {'name': '*New*', 'ip': '0.0.0.0', 'pixelCount': 0, 'maxFps': 30, 'renderPattern': '@preset'}
        # append an empty "data" dictionary to the device
        data[devTag]['data'] = {}
        configDatabase['devices'] = data
        self.devicesPanel.set_devices_text(data)
        self.devicesPanel.children['pb_table'].redraw()

    def onclick_btnRemoveDevice(self, emitter):
        # to remove a device, we remove it in configDatabase and rebuild the table
        table = self.devicesPanel.children['pb_table']
        if table.last_clicked_row is not None:
            devTag = table.get_row_key(table.last_clicked_row)
            data = configDatabase.get('devices', {})
            data.pop(devTag, None)
            configDatabase['devices'] = data
            self.devicesPanel.set_devices_text(data)
            table.redraw()

    def onclick_btnAddUniverse(self, emitter):
        table = self.universesPanel.children['u_table']
        devTag = self.universesPanel.deviceTag
        data = configDatabase.get('devices', {}).get(devTag, {}).get('data', {})
        uTag = make_unique_tag(data)

        # add reasonable defaults for the new universe to the device
        # TODO - let's be smarter about filling in universe details based on the
        # TODO - device's pixel count and the number of universes already defined
        data[uTag] = {"net": 0, "subnet": 0, "universe": 1, "startChannel": 0, "destIndex": 0,
                      "pixelCount": 170}

        configDatabase['devices'][devTag]['data'] = data
        self.universesPanel.set_universes_text(data)
        table.redraw()

    def onclick_btnRemoveUniverse(self, emitter):
        table = self.universesPanel.children['u_table']
        devTag = self.universesPanel.deviceTag

        if table.last_clicked_row is not None:
            uTag = table.get_row_key(table.last_clicked_row)
            data = configDatabase.get('devices', {}).get(devTag, {}).get('data', {})
            data.pop(uTag, None)

            configDatabase['devices'][devTag]['data'] = data
            self.universesPanel.set_universes_text(data)
            table.redraw()

    def onclick_btnUniverseBack(self, emitter):
        self.onclick_btnDevices(emitter)

    def onclick_pixelblaze_table(self, table):
        pass

    def ondblclick_pixelblaze_table(self, table):
        """Called when the Widget gets double clicked by the user with the left mouse button."""
        table = self.devicesPanel.children['pb_table']

        # only react to clicks on a valid, selected data row
        if table.last_clicked_row is not None:
            devTag = table.get_row_key(table.last_clicked_row)
            data = configDatabase.get('devices', {})
            data = data.get(devTag, {})
            name = data.get('name', '')
            data = data.get('data', {})

            self.universesPanel.set_universes_text(data, name, devTag)
            self.start_universe_editor()
        return
