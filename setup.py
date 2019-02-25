#!/usr/bin/env python

"""
Automated docker service installer.
Author: Nimeshka Srimal
Date: Feb 2019
"""

import sys
from datetime import datetime
import json
import curses
from curses.panel import new_panel
from os import system, popen, path
from curses.textpad import Textbox, rectangle


class Installer(object):

    def __init__(self, services):
        self.config = None
        self.repository = None
        self.install_type = None
        self._go_version_tag = None
        self._version_tag = None
        self.repository_ipurl = None
        self.window_height, self.window_width = [int(i) for i in popen('stty size', 'r').read().split()]
        
        self.services = services
        
        self.editor = {
            'screen': None,
            'window': None,
            'help_window': None,
            'textbox': None,
            'statusbar': None,
            'current_item': None
        }

        self.data_sources = ['mongodb', 'rabbitmq', 'redis', 'database']

        self.date = datetime.now()

    def get_install_type(self):
        if self.install_type is not None:
            return self.install_type
        else:
            return self.set_install_type()

    def get_repository(self):
        if self.repository is not None:
                return self.repository
        else:
            return self.set_install_repository()

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

        self.editor['textbox'] = Textbox(self.editor['window'], insert_mode=True)

        self.editor['textbox'].stripspaces = True

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

        self.editor['textbox'].edit(self.listen_keys)

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

            # reformat the text to fit the textbox (when new lines are present in the original text, a blank line will be added if we leave it alone)
            reformatted_text = ""
            for line in current_text.splitlines():
                    eol =  "\n" if line.strip()[-1:] == "," else ""
                    reformatted_text += line + eol

            self.editor['window'].clear()
            self.editor['window'].addstr(0, 0, reformatted_text)
            self.editor['window'].refresh()

            return True

    def _print(self, text):

        text = "| {} |".format(text)
        border = "+{}+".format("-" * (len(text) - 2))
        print "{}\n{}\n{}".format(border, text, border)

    def listen_keys(self, ch):
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
        self.install_type = popen('whiptail --title "Facetone Service Installer" --notags --menu "" 15 60 4 \
                    "1" "Install all Services" \
                    "2" "Custom Installation" 3>&1 1>&2 2>&3'
                    ).read()

        return self.install_type

    def set_install_repository(self):
        self.repository = popen('whiptail --title "Facetone Service Installer" --notags --menu "\nSelect the repository source." 15 60 4 \
                    "github" "Github" \
                    "dockerhub" "Docker Hub" 3>&1 1>&2 2>&3'
                    ).read()

        if self.repository == "":
            self.exit_installer()
            
        return self.repository

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
        self._print(msg)
        sys.exit()
        
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
    config_inst = An instance of a valid configuration object.
    returns: updated configuration instance
    """
    def edit_configuration(self, config_inst):
        config = {}

        def gen_line(section_vals, indent=0):

            e_txt = "";

            for index, (key, value) in enumerate(section_vals.iteritems()):
                delimiter = "," if index != (len(section_vals) - 1) else ""
                if type(value) is not dict:
                    char_indent = " " * indent
                    e_txt += '{}"{}": "{}"{}\n'.format(char_indent, key, value, delimiter)
                else:
                    # recursively generate the second level configurations
                    sub_text = gen_line(value, 4)
                    e_txt += '"{}": {{\n{}}}{}\n'.format(key, sub_text, delimiter)
            return e_txt
            
    

        for _sec in config_inst.keys():  
            
            conf_invalid = True

            while conf_invalid:
                e_txt = gen_line(config_inst[_sec])
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

    def run(self):
        # load sample configs, we use this to replace missing sections (keys), or if there's no config file.
        with open("config.sample.json") as f:
            conf_sample = json.load(f)

        # this is the config we are holding all configs for the current installer session.
        new_conf = {}

        # This is to hold the content of user's current config file..
        current_conf = None

        # prompt the user to select the installation type.
        self.get_install_type()

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

        # self.set_install_repository()

        # prompt the uset to select the repository.
        self.get_repository()

        print self.repository

        print self.config

       
if __name__ == "__main__":
    try:
        with open('services.json', 'r') as js:
            services = json.load(js)
    except Exception, e:
        print "Error: There was an error parsing the services.json file. \n[{}]".format(e.message)
        sys.exit()  

    Installer(services).run()


