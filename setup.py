#!/usr/bin/env python

"""
Automated docker service installer.
Author: Nimeshka Srimal
Date: Feb 2019
"""

import sys
import time
import json
import curses
from curses.panel import new_panel
from os import system, popen, path
from curses.textpad import Textbox, rectangle


class Installer(object):

    def __init__(self, services):
        
        self.config = None
        self.ins_type = None
        self.repository = None
        self.version_tag = None
        self.go_version_tag = None
        self.repository_ipurl = None
        self.window_height, self.window_width = [int(i) for i in popen('stty size', 'r').read().split()]
        
        self.services = services
        
        self.editor = {
            'screen': None,
            'window': None,
            'textbox': None,
            'statusbar': None,
            'help_window': None,
            'current_item': None
            
        }

        self.data_sources = ['mongodb', 'rabbitmq', 'redis', 'database']

    def init_editor(self, stdscr, section, text=""):

        self.editor['screen'] = stdscr
        self.editor['screen'].clear()
        self.editor['screen'].addstr(0, 1, ' [' + section + '] ', curses.A_REVERSE)
        
        # set the current section of the edit window, (used in listener to verify test connection method.)
        self.editor['current_item'] = section

        width = self.window_width-4
        height = self.window_height-4

        self.editor['screen'].addstr(0, width - 12, ' Help [Ctrl-?] ', curses.A_REVERSE)

        self.editor['window'] = curses.newwin(height,width, 2,1)

        # add seperation line below title.
        self.editor['screen'].addstr(1, 1, '-' * width)

        # editor textbox
        self.editor['window'].addstr(0, 0, text)

        self.editor['textbox'] = Textbox(self.editor['window'], insert_mode=False)

        # status bar
        self.editor['statusbar'] = self.editor['screen'].subwin(1, self.window_width, self.window_height - 1,0)
        self.editor['statusbar'].bkgd(curses.A_REVERSE)

        if section in self.data_sources:
            self.editor['statusbar'].addstr(0, (width - 38) , "Save [Ctrl-G] / Test Connection [Ctrl-T]")
        else:
            self.editor['statusbar'].addstr(0, (width - 10), "Save [Ctrl-G]")

        self.editor['screen'].refresh()

        # help Window
        try:
            # We can only create the help window if there's enough space, otherwise we'll ignore it.
            self.make_help_window()
        except:
            pass

        self.editor['textbox'].edit(self.key_listener)

        # return the text entered in the textbox
        return self.editor['textbox'].gather()


    def make_help_window(self):
        
        # region make_help_window
        help_window = curses.newwin(25, 85, 5, 5)
        h, w = help_window.getmaxyx()
        title = help_window.subwin(2, w, 5,5)
        title.bkgd(curses.A_REVERSE)
        title.addstr(1,2, "HELP")
        title.addstr(1,title.getmaxyx()[1] - 12, "q = close")
    
        help_window.addstr(2,1, 
        """
    * Format = "property": "value",
    
    The following controls are available in the editor!

    +-----------+--------------------------------------------------------------+
    | Key       | Action                                                       |
    +-----------+--------------------------------------------------------------+
    | Control-A | Go to left edge of window.                                   |
    | Control-D | Delete character under cursor.                               |
    | Control-E | Go to right edge or end of line.                             |
    | Control-K | If line is blank, delete it, otherwise clear to end of line. |
    | Control-O | Insert a blank line at cursor location.                      |
    |           |                                                              |
    | Control-T | Validate / Test data source connections.                     |
    | Control-G | Save current config and move to next.                        |
    +-----------+--------------------------------------------------------------+

    Press 'q' to close this window.

        """
        )

        help_window.box()
        help_window.refresh()
        
        self.editor['help_window'] = new_panel(help_window)
        self.editor['help_window'].hide()
        
        curses.panel.update_panels()

        return True
        # endregion


    def show_help_window(self):

        if self.editor['help_window'] is not None:
            
            curses.curs_set(0)            
            self.editor['help_window'].show()
            curses.panel.update_panels()
            self.editor['screen'].refresh()
            
            while True:
                key = self.editor['help_window'].window().getch()

                # press q to close window.
                if key == 113:
                    self.editor['help_window'].hide()
                    curses.panel.update_panels()
                    break

            curses.curs_set(2)
            self.editor['window'].move(2,2)
            
            # reset the textbox content to current state!
            current_text = self.editor['textbox'].gather()
            self.editor['window'].clear()
            self.editor['window'].addstr(0, 0, current_text)
            self.editor['window'].refresh()

            return True

    def print_msg(self, text):

        text = "| {} |".format(text)
        border = "-" * len(text)
        print "{} \n {} \n {}".format(border, text, border)

    def key_listener(self, ch):

        if ch == 20 and self.editor['current_item'] in self.data_sources:
            self.editor['statusbar'].addstr(0, 1, "Method not implemented!")
            self.editor['statusbar'].refresh()
            return True

        elif ch == 31:
            # [ Ctrl + ? ] help menu!
            self.show_help_window()

        elif ch == 10:
            # [ Ctrl + m ] Reserved Key controller for future!
            pass

        else:
            return ch    

    def set_install_type(self):

        self.ins_type = popen('whiptail --title "Advanced Menu" --notags --menu "Choose an option" 15 60 4 \
                    "1" "Install all Services" \
                    "2" "Custom Installation" 3>&1 1>&2 2>&3'
                    ).read()

        return self.ins_type

    @property
    def install_type(self):
        if self.ins_type is not None:
            return self.ins_type
        else:
            return self.set_install_type()

    # returns list []
    def get_installation_list(self):

        servicelist = self.services.keys()
        servicelist.sort()

        servicelist_str = ''
        
        for service in servicelist:
            padded_srv = service + " "* (self.window_width-25 - len(service))
            servicelist_str += " '{}' '{}' off".format(service, padded_srv)

        w_cmd = '''
                whiptail \
                    --title "Select the Services" \
                    --notags \
                    --separate-output \
                    --checklist \
                    " " \
                    {} {} {} {} \
                    3>&1 1>&2 2>&3
                '''.format(
                        self.window_height-10, 
                        self.window_width-10,
                        self.window_height-20, 
                        servicelist_str
                    )
                    
        install_list = popen(w_cmd).read().splitlines()

        return install_list

    
    def exit_installer(self, msg="exiting installer"):
        # Do any tear down work here...for now we'll just exit.
        sys.exit(msg)
    

    def run(self):

        # load sample configs, we use this to replace missing sections (keys), or if there's no config file.
        with open("config.sample.json") as f:
            conf_sample = json.load(f)

        # this is the config we are holding all configs for the current installer session.
        new_conf = {}

        # This is to hold the content of user's current config file..
        current_conf = None

        if self.install_type == "":
            self.exit_installer("nothing selected!")

        elif self.install_type == "1":
            # set the new config to sample, because we don't have any at the moment.
            new_conf = conf_sample

        elif self.install_type == "2":
            # get only the required sections from the config.ini.sample file and prompt the user to edit.
            install_list = self.get_installation_list()

            # EXIT the installer because selected nothing!
            if len(install_list) == 0:
                self.exit_installer("nothing to install")

            # ***************************************** 
            required_configs = []

            for service_ in install_list:
                required_configs += self.services[service_]['configs']
                
            # get all the configs we need from user and remove duplicates from it.
            required_configs = set(required_configs)

            if path.exists('config.json'):
                # get users's current configuration
                # check if current config file is valid, if so, we get a new instance of it.
                try:
                    with open("config.json") as f:
                        current_conf = json.load(f)
                except ParsingError as e:
                    self.exit_installer("Invalid configuration found. Please fix the config and retry")

                for _sect in required_configs:
                    new_conf[_sect] = {}

                    if _sect in current_conf:
                        # user already have this section
                        # add all options from user's current config to the new temp config.
                        for _opt, _val in current_conf[_sect].items():
                            new_conf[_sect][_opt] = _val
                    else:
                        # user does not have section, get all options from sample.
                        for _opt, _val in conf_sample[_sect].items():
                            new_conf[_sect][_opt] = _val

            else:
                # config file doesn't exist! so we get all the sections from the sample and prepare the config edit box!
                new_conf = conf_sample
                removeable_confs = set(new_conf.keys()) - required_configs
                
                # remove sections (keys) which are not needed for current session!
                map(lambda _sect: new_conf.pop(_sect, None), removeable_confs)

        # Edit the config and set it as the current installer session config.
        self.config = self.edit_configuration(new_conf)

        # Write the updated new configuration to the user's real config.
        self.write_to_config(self.config, current_conf)

        # docker service installation process starts from here.
        print self.config

    def write_to_config(self, new_conf, current_conf=None):

        if current_conf is not None:
            for _temp_sect in new_conf.keys():                
                # if the current conf doesn't have this section, we add it.
                if _temp_sect not in current_conf:
                    current_conf[_temp_sect] = {}

                for key, val in new_conf[_temp_sect].items():
                    current_conf[_temp_sect][key] = val
        else:
            current_conf = new_conf

        with open("config.json", "w+") as f:
            f.write(json.dumps(current_conf, sort_keys=True, indent=4))

    """
    @params
    config_inst = An instance of a valid configuration object,
    
    returns: updated configuration instance
    """

    def edit_configuration(self, config_inst):
        config = {}

        for _sec in config_inst.keys():  
            
            conf_invalid = True

            while conf_invalid:
                e_txt = ""

                for index, (key, value) in enumerate(config_inst[_sec].iteritems()):
                    delimiter = "," if index != (len(config_inst[_sec]) - 1) else ""
                    e_txt += '"{}": "{}"{}\n'.format(key, value, delimiter)
        
                e_txt = curses.wrapper(self.init_editor, _sec, e_txt)
                e_txt = "{{ {} }}".format(e_txt)
                e_txt = e_txt.replace('\n', '')

                try:
                    config[_sec] = json.loads(e_txt)
                    conf_invalid = False
                except Exception, e:
                    confirmation = system('whiptail --title "Invalid configuration." --no-button "Exit Installer" --yesno " \
                                                \n\nDo you want to edit [{}] section again?" 15 60'.format(_sec))
                    
                    if confirmation != 0:
                        self.exit_installer()
                        # break

        return config
    
    def _print(self, text):

        text = "| {} |".format(text)
        border = "-" * len(text)
        print "{}\n{}\n{}".format(border, text, border)

if __name__ == "__main__":

    services = {
                # "agentdialerservice": {'github_url': 'https://github.com/DuoSoftware/DVP-AgentDialerService.git', 'configs': ['general', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "agentdialerservice": {'github_url': 'https://github.com/DuoSoftware/DVP-AgentDialerService.git', 'configs': ['general'], 'type': 'nodejs'},
                "appregistry": {'github_url': 'https://github.com/DuoSoftware/DVP-APPRegistry.git', 'configs': ['general', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "ardsliteroutingengine": {'github_url': 'https://github.com/DuoSoftware/DVP-ARDSLiteRoutingEngine.git', 'configs': ['general', 'ardsliteroutingengine', 'mongodb', 'rabbitmq', 'redis'], 'type': 'go'},
                "ardsliteroutingengineimproved": {'github_url': 'https://github.com/DuoSoftware/DVP-ARDSLiteRoutingEngineImproved.git', 'configs': ['general', 'ardsliteroutingengineimproved', 'mongodb', 'rabbitmq', 'redis'], 'type': 'go'},
                "ardsliteservice": {'github_url': 'https://github.com/DuoSoftware/DVP-ARDSLiteService.git', 'configs': ['general', 'ardsliteservice', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "ardsliteserviceimproved": {'github_url': 'https://github.com/DuoSoftware/DVP-ARDSLiteServiceImproved.git', 'configs': ['general', 'ardsliteserviceimproved', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "ardsmonitoring": {'github_url': 'https://github.com/DuoSoftware/DVP-ARDSMonitoring.git', 'configs': ['general', 'ardsmonitoring', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "ardsslotcalculator": {'github_url': 'https://github.com/DuoSoftware/DVP-ARDSSlotCalculator.git', 'configs': ['general', 'redis'], 'type': 'nodejs'},
                "autoattendant": {'github_url': 'https://github.com/DuoSoftware/DVP-AutoAttendant.git', 'configs': ['general', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "billingservice": {'github_url': 'https://github.com/DuoSoftware/DVP-Billing.git', 'configs': ['general', 'billingservice', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "callbackservice": {'github_url': 'https://github.com/DuoSoftware/DVP-CallBackService.git', 'configs': ['general', 'callbackservice', 'mongodb', 'rabbitmq', 'redis'], 'type': 'go'},
                "campaignmanager": {'github_url': 'https://github.com/DuoSoftware/DVP-CampaignManager.git', 'configs': ['general', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "carrierprovider": {'github_url': 'https://github.com/DuoSoftware/DVP-CarrierProvider.git', 'configs': ['general'], 'type': 'nodejs'},
                "cdrengine": {'github_url': 'https://github.com/DuoSoftware/DVP-CDREngine.git', 'configs': ['general', 'cdrengine', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "cdreventlistner": {'github_url': 'https://github.com/DuoSoftware/DVP-CDREventListner.git', 'configs': ['general', 'cdreventlistner', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "cdrgenerator": {'github_url': 'https://github.com/DuoSoftware/DVP-CDRGenerator.git', 'configs': ['general', 'cdrgenerator', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "cdrprocessor": {'github_url': 'https://github.com/DuoSoftware/DVP-CDRProcessor.git', 'configs': ['general', 'cdrprocessor', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "clusterconfig": {'github_url': 'https://github.com/DuoSoftware/DVP-ClusterConfiguration.git', 'configs': ['general', 'clusterconfig', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "conference": {'github_url': 'https://github.com/DuoSoftware/DVP-Conference.git', 'configs': ['general', 'conference', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "contactbasednumberdialingservice": {'github_url': 'https://github.com/DuoSoftware/DVP-ContactBasedNumberDialingService.git', 'configs': ['general', 'mongodb', 'redis'], 'type': 'nodejs'},
                "contacts": {'github_url': 'https://github.com/DuoSoftware/DVP-Contacts.git', 'configs': ['general', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "crmintegrations": {'github_url': 'https://github.com/DuoSoftware/DVP-CRMIntegrations.git', 'configs': ['general', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "csatservice": {'github_url': 'https://github.com/DuoSoftware/DVP-CSATService.git', 'configs': ['general', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "dashboard": {'github_url': 'https://github.com/DuoSoftware/DVP-DashBoard.git', 'configs': ['general', 'dashboard', 'mongodb', 'rabbitmq', 'redis'], 'type': 'go'},
                "dashboarddataprocessor": {'github_url': 'https://github.com/DuoSoftware/DVP-DashboardDataProcessor.git', 'configs': ['general', 'dashboarddataprocessor', 'mongodb', 'rabbitmq'], 'type': 'go'},
                "dashboardservice": {'github_url': 'https://github.com/DuoSoftware/DVP-DashBoardService.git', 'configs': ['general', 'dashboardservice', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "dialerapi": {'github_url': 'https://github.com/DuoSoftware/DVP-DialerAPI.git', 'configs': ['general', 'dialerapi', 'mongodb', 'rabbitmq', 'redis'], 'type': 'go'},
                "diameterclient": {'github_url': 'https://github.com/DuoSoftware/DVP-DiameterClient.git', 'configs': ['general', 'diameterclient', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "diameterrelay": {'github_url': 'https://github.com/DuoSoftware/DVP-DiameterRelay.git', 'configs': ['general', 'diameterrelay', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "diameterserver": {'github_url': 'https://github.com/DuoSoftware/DVP-DiameterServer.git', 'configs': ['general', 'diameterserver', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "dynamicconfigurationgenerator": {'github_url': 'https://github.com/DuoSoftware/DVP-DynamicConfigurationGenerator.git', 'configs': ['general', 'dynamicconfigurationgenerator', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "engagementservice": {'github_url': 'https://github.com/DuoSoftware/DVP-Engagement.git', 'configs': ['general', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "eventmonitor": {'github_url': 'https://github.com/DuoSoftware/DVP-EventMonitor.git', 'configs': ['general', 'eventmonitor', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "eventservice": {'github_url': 'https://github.com/DuoSoftware/DVP-EventService.git', 'configs': ['general', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "eventsink": {'github_url': 'https://github.com/DuoSoftware/DVP-EventSink.git', 'configs': ['general', 'eventsink', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "filearchiveservice": {'github_url': 'https://github.com/DuoSoftware/DVP-FileArchiveService.git', 'configs': ['general', 'filearchiveservice'], 'type': 'go'},
                "fileservice": {'github_url': 'https://github.com/DuoSoftware/DVP-FileService.git', 'configs': ['general', 'fileservice', 'mongodb', 'rabbitmq', 'redis', 'couch'], 'type': 'nodejs'},
                "httpprogrammingapi": {'github_url': 'https://github.com/DuoSoftware/DVP-HTTPProgrammingAPI.git', 'configs': ['general', 'httpprogrammingapi', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "httpprogrammingapidebug": {'github_url': 'https://github.com/DuoSoftware/DVP-HTTPProgrammingAPIDEBUG.git', 'configs': ['general', 'httpprogrammingapidebug', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "httpprogrammingmonitorapi": {'github_url': 'https://github.com/DuoSoftware/DVP-HTTPProgrammingMonitorAPI.git', 'configs': ['general', 'mongodb', 'redis'], 'type': 'nodejs'},
                "integrationapi": {'github_url': 'https://github.com/DuoSoftware/DVP-IntegrationAPI.git', 'configs': ['general', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "interactions": {'github_url': 'https://github.com/DuoSoftware/DVP-Interactions.git', 'configs': ['general', 'interactions', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "ipmessagingservice": {'github_url': 'https://github.com/DuoSoftware/DVP-IPMessagingService.git', 'configs': ['general', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "limithandler": {'github_url': 'https://github.com/DuoSoftware/DVP-LimitHandler.git', 'configs': ['general', 'limithandler', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "liteticket": {'github_url': 'https://github.com/DuoSoftware/DVP-LiteTicket.git', 'configs': ['general', 'liteticket', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "mailreceiver": {'github_url': 'https://github.com/DuoSoftware/DVP-MailReceiver.git', 'configs': ['general', 'mongodb', 'rabbitmq', 'redis', 'sms', 'smtp'], 'type': 'nodejs'},
                "mailsender": {'github_url': 'https://github.com/DuoSoftware/DVP-MailSender.git', 'configs': ['general', 'mongodb', 'rabbitmq', 'redis', 'sms', 'smtp'], 'type': 'nodejs'},
                "monitorrestapi": {'github_url': 'https://github.com/DuoSoftware/DVP-MonitorRestAPI.git', 'configs': ['general', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "notificationservice": {'github_url': 'https://github.com/DuoSoftware/DVP-NotificationService.git', 'configs': ['general', 'notificationservice', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "pbxservice": {'github_url': 'https://github.com/DuoSoftware/DVP-PBXService.git', 'configs': ['general', 'pbxservice', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "phonenumbertrunkservice": {'github_url': 'https://github.com/DuoSoftware/DVP-PhoneNumberTrunkService.git', 'configs': ['general', 'phonenumbertrunkservice', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "productivityservice": {'github_url': 'https://github.com/DuoSoftware/DVP-ProductivityService.git', 'configs': ['general', 'productivityservice', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "qamodule": {'github_url': 'https://github.com/DuoSoftware/DVP-QAModule.git', 'configs': ['general', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "queuemusic": {'github_url': 'https://github.com/DuoSoftware/DVP-QueueMusic.git', 'configs': ['general', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "reportqueryfilters": {'github_url': 'https://github.com/DuoSoftware/DVP-ReportQueryFilters.git', 'configs': ['general', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "resourceservice": {'github_url': 'https://github.com/DuoSoftware/DVP-ResourceService.git', 'configs': ['general', 'resourceservice', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "ruleservice": {'github_url': 'https://github.com/DuoSoftware/DVP-RuleService.git', 'configs': ['general', 'ruleservice', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "scheduleworker": {'github_url': 'https://github.com/DuoSoftware/DVP-ScheduleWorker.git', 'configs': ['general', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "sipuserendpointservice": {'github_url': 'https://github.com/DuoSoftware/DVP-SIPUserEndpointService.git', 'configs': ['general', 'sipuserendpointservice', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "skypebot": {'github_url': 'https://github.com/DuoSoftware/DVP-SkypeBot.git', 'configs': ['general', 'skypebot'], 'type': 'nodejs'},
                "smppclient": {'github_url': 'https://github.com/DuoSoftware/DVP-SMPPClient.git', 'configs': ['general', 'smppclient', 'mongodb', 'rabbitmq', 'redis', 'sms'], 'type': 'nodejs'},
                "socialconnector": {'github_url': 'https://github.com/DuoSoftware/DVP-SocialConnector.git', 'configs': ['general', 'socialconnector', 'mongodb', 'rabbitmq', 'redis', 'sms', 'smtp'], 'type': 'nodejs'},
                "templates": {'github_url': 'https://github.com/DuoSoftware/DVP-Templates.git', 'configs': ['general', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "todolistservice": {'github_url': 'https://github.com/DuoSoftware/DVP-ToDoListService.git', 'configs': ['general', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "twitterreciver": {'github_url': 'https://github.com/DuoSoftware/DVP-TwitterReciver.git', 'configs': ['general', 'twitterreciver', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "userservice": {'github_url': 'https://github.com/DuoSoftware/DVP-UserService.git', 'configs': ['general', 'userservice', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "voxboneapi": {'github_url': 'https://github.com/DuoSoftware/DVP-VoxboneAPI.git', 'configs': ['general', 'voxboneapi', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
                "walletservice": {'github_url': 'https://github.com/DuoSoftware/DVP-Wallet.git', 'configs': ['general', 'mongodb', 'rabbitmq', 'redis'], 'type': 'nodejs'},
        }

    Installer(services).run()


