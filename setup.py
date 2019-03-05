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
import os
import re
import time
from curses.panel import new_panel
from os import system, popen, path
from curses.textpad import Textbox, rectangle
import subprocess
from textwrap import wrap


class Installer(object):

    def __init__(self, services):
        self.config = None
        self.repository = None
        self.install_type = None
        self.go_version_tag = None
        self.version_tag = None
        self.deploy_mode = None
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

        with open('env_meta.json') as f:
            self.env_meta = json.load(f)

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

    def get_version_tag(self, type="nodejs"):

        if type == "nodejs":
            if self.version_tag is not None:
                    return self.version_tag
            else:
                return self.set_version_tag()
        elif type == "go":
            if self.go_version_tag is not None:
                    return self.go_version_tag
            else:
                return self.set_version_tag(type="go")

    def set_repository_ipurl(self):

        if self.repository_ipurl is None or self.repository_ipurl == "":
            self.repository_ipurl = popen('whiptail --title "Facetone Service Installer" --inputbox "\nPlease enter the repository IP / URL:" 15 60'
                        ' 3>&1 1>&2 2>&3'.format(type)).read()
        
        return self.repository_ipurl
            
    def set_version_tag(self, type="nodejs"):
        input = popen('whiptail --title "Facetone Service Installer" --inputbox "\nPlease enter {} version tag:" 15 60'
                      ' 3>&1 1>&2 2>&3'.format(type)).read()
        
        if type == "nodejs":
            self.version_tag = input
            return self.version_tag
        elif type == "go":
            self.go_version_tag = input
            return self.go_version_tag

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
    * Configuration should be valid json!
    
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

            # reformat the text
            current_text = json.dumps(json.loads(current_text), indent=4)

            self.editor['window'].clear()
            self.editor['window'].addstr(0, 0, current_text)
            self.editor['window'].refresh()

            return True

    def _print(self, text):
        lines = ''
        for line in wrap(text, self.window_width - 4):
            lines += "| " + line.ljust(self.window_width-4) + " |\n"
                
        border = "+{}+\n".format("-" * (self.window_width - 2))

        print border + lines + border

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

    def set_deploy_mode(self):
        self.deploy_mode = popen('whiptail --title "Facetone Service Installer" --notags --menu "" 15 60 4 \
                                    "instance" "Instance" \
                                    "swarm" "Swarm Cluster" 3>&1 1>&2 2>&3'
                                ).read()

        return self.deploy_mode


    def set_install_repository(self):
        self.repository = popen('whiptail --title "Facetone Service Installer" --notags --menu "\nSelect the repository'
                                ' source." 15 60 4 \
                                "local" "Local" \
                                "github" "GitHub" \
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

        for _sec in config_inst.keys():  
            
            conf_invalid = True

            while conf_invalid:
                e_txt = json.dumps(config_inst[_sec], indent=4)
                e_txt = curses.wrapper(self.init_editor, _sec, e_txt)
                
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

    # method to expand all placeholder values in the configuration value and return final output
    def expand_conf_placeholder(self, str, conf_block):
        placeholders = re.findall(r'{(.*?)}', str)
        
        if len(placeholders) != 0:
            # split the placeholder by arrow notation (->),
            for _c in placeholders:
                p_holders_arr = _c.split('->')

                # there are no sub sections, will directly return the corresponding config value for the given key.
                if len(p_holders_arr) == 1:
                    str = str.replace('{' + _c + '}', conf_block[_c])
                else:
                    # there are sub sections, so we will go through the keys and get the value..
                    _v = self.config
                    for sub_sect in p_holders_arr:
                        _v = _v[sub_sect]

                    str = str.replace('{' + _c + '}', _v)

        return str

    def command(self, cmd):
        shell = True
        
        if isinstance(cmd, list):
            shell = False

        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True, shell=shell)
        success, error = p.communicate()

        if p.returncode != 0:
            raise Exception("Error running command! " + error)
        else:
            return True


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
            install_list = self.services.keys()

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

        # """"""""""""""""""""""""""""""""""""""""""""""""""""
        # docker service installation process starts from here
        # """"""""""""""""""""""""""""""""""""""""""""""""""""

        # prompt the user to select the repository.
        self.set_install_repository()

        # set version tags (go and nodejs)
        self.set_version_tag("nodejs")
        self.set_version_tag("go")

        self.set_deploy_mode()
 
        # process = subprocess.Popen(["whiptail", "--title", "Progress", "--gauge", "Installing..", "6", "80", "0"], stdin=subprocess.PIPE)

        count = len(install_list)
        percent = 0

        os.chdir('/usr/src/')
        ghub_regex = re.compile(r"github.com/DuoSoftware/(.*?).git")

        try:
            for i, _service in enumerate(install_list):
                
                service_conf = self.config[_service]

                # # ********************************************************************************
                # process.stdin.write(b'XXX\n{}\nInstalling {} \nXXX\n'.format(percent, _service))
                # time.sleep(1)
                # # ********************************************************************************

                if self.services[_service]['type'] == "nodejs":
                    clone_v_tag = self.version_tag
                    exec_command = "node /usr/local/src/%s/app.js" % _service
                elif self.services[_service]['type'] == "go":
                    clone_v_tag = self.go_version_tag
                    exec_command = "go run *.go"

                # raise execption if the tag is empty!
                if clone_v_tag == "":
                    raise Exception("Error while Installing {} : {} version tag cannot be empty!".format(_service, self.services[_service]['type']))

                if self.repository == "github":
                    repo_dir_name = ghub_regex.findall(self.services[_service]['github_url'])[0]

                    if not os.path.isdir(repo_dir_name):
                        self.command(["git", "clone", "-b", clone_v_tag, self.services[_service]['github_url']])
                elif self.repository == "local":
                    self.set_repository_ipurl()

                    self.command('docker pull {repo_ipurl}:5000/{service}:{v_tag};'.format(repo_ipurl=self.repository_ipurl, service=_service, v_tag=clone_v_tag))
                    self.command('docker tag {repo_ipurl}:5000/{service}:{v_tag} {service}:{v_tag};'.format(repo_ipurl=self.repository_ipurl, service=_service, v_tag=clone_v_tag))
                    self.command('docker rmi -f {repo_ipurl}:5000/{service}:{v_tag};'.format(repo_ipurl=self.repository_ipurl, service=_service, v_tag=clone_v_tag))

                elif self.repository == "dockerhub":
                    self.command('docker pull facetone/{}:{}'.format(_service, clone_v_tag))
                
                
                os.chdir(repo_dir_name)

                build_cmd = 'docker build --build-arg VERSION_TAG={version_tag} -t {service_name}:{version_tag} .;'.format(version_tag = clone_v_tag, service_name=_service)

                self.command(build_cmd)

                os.chdir('/usr/src/')

                run_cmd = 'docker run -d -t -v /etc/localtime:/etc/localtime:ro '

                # merge the default docker params dict with the user provided docker params..
                # If user wants to override the defaults, can pass them in config..
                default_docker_params = {
                    "--log-opt max-size": "10m", 
                    "--log-opt max-file": "10", 
                    "--restart": "always", 
                    "--memory": "512m"
                }

                service_conf['DOCKER_PARAMS'].update(default_docker_params)

                # append all docker parameters to the run command..
                for key, val in service_conf['DOCKER_PARAMS'].iteritems():
                    run_cmd += '{}="{}" '.format(key, self.expand_conf_placeholder(val, service_conf))

                # remove the docker params key from the config since we don't need to anymore
                del service_conf['DOCKER_PARAMS']

                # append all required env variable parameters to the run command..
                required_configs = self.services[_service]['configs']

                for r_conf in required_configs:
                    # get config key value pairs for all required configs from the current session's config object..                    
                    for key, val in self.config[r_conf].iteritems():
                        # get all the session variables set for each config item using env_meta
                        if key in self.env_meta:
                        
                            # set each environment variable
                            for env_var in self.env_meta[key]:
                                run_cmd += '--env="{}={}" '.format(env_var, self.expand_conf_placeholder(val, service_conf))
                            
                            run_cmd += '--env="VERSION_TAG={}" --env="COMPOSE_DATE={}" '.format(clone_v_tag, self.date)

                # append the name and executable params.
                run_cmd += '--name {service_name} {service_name}:{v_tag} {_exec}; '.format(service_name=_service, v_tag=clone_v_tag, _exec=exec_command)
                
                self.command(run_cmd)

                # # ********************************************************************************
                # percent = int(float(i + 1) / count * 100)
                # process.stdin.write(b'{}\nXXX\n{}\nInstalling {} - Done\nXXX\n'.format(percent, percent, _service))
                # time.sleep(1)
                # # ********************************************************************************
            

            # ********************************************************************************
            # process.stdin.close()
            # ********************************************************************************

        except Exception as e:
                    self.exit_installer('Installation failed! Error "{}" in service: {}, {}'.format(type(e).__name__, _service, e))
        finally:
            # process.stdin.close()
            pass

        time.sleep(2)
        
            
        
        print "======== end ============"

if __name__ == "__main__":
    try:
        with open('services.json', 'r') as js:
            services = json.load(js)
    except Exception, e:
        print "Error: There was an error parsing the services.json file. \n[{}]".format(e.message)
        sys.exit()  

    Installer(services).run()