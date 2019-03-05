#!/usr/bin/env python

"""
Utility script to parse the installation script and generate list of services and dependencies
Author: Nimeshka Srimal
"""

import sys
import re
import json
import ConfigParser

services = {}

config = ConfigParser.RawConfigParser()
config.read("config.sample.ini")

# sections = config.sections()

with open('config.sample.json', 'r') as f:
    _conf = json.load(f)
    sections = _conf.keys()

# print sections 
# sys.exit()

# First get all the services and add to the services dict.
with open('conf.txt') as f:
    lines = f.readlines()
    section = ''
    section_strp = ''
    last_match = ''

    # regex to identify uppercase env variables.
    regx = re.compile(r"\$([A-Z_]+)")

    for line in lines:
        match = re.match(r"^\"(.*)\"\).*$",line.strip())
        if match:

            if section_strp != "":

                

                release_from = "version_tag"
                if re.findall(r'[^#]docker build -t ".*?:latest" .;',section_strp):
                    release_from = "latest"

                docker_run_cmd = ""

                cmd_match = re.findall(r';(docker run .*?);',section_strp)

                if cmd_match:
                    docker_run_cmd = regx.sub(r"{\1}", cmd_match[0]).replace('"', "'")               
                
                # print docker_run_cmd
                # sys.exit()
                
                
                service_type = "nodejs"
                envvars = re.findall(r"(\$GO_VERSION_TAG)",section_strp)

                if envvars:
                    service_type = "go"

                # print '"{}": {{ type: "{}", configs: [] }}, '.format(last_match, service_type)

                services[last_match] = {
                    "type" : service_type,
                    "release_from": release_from,
                    # "run_cmd": docker_run_cmd,
                    "configs": [ "general"]
                }

                if last_match in sections:
                    services[last_match]["configs"].append(last_match)
                

                # we need to grab the github urls from the list as well...
                github_url = re.findall(r"https://github.com/(.*?).git", section_strp)
                services[last_match]['github_url'] = "https://github.com/" + github_url[0] + ".git"

            section_strp = ''
            last_match = match.group(1)

        else:
            section_strp += line.strip()

# now we will add remaining dependencies...

config2 = ConfigParser.RawConfigParser()
config2.read("config.ini.full.backup")

# print config2.sections()

for _section in config2.sections():
    configs = dict(config2.items(_section))

    # print _section
    # print configs

    if "database_host" in configs:
        services[_section]['configs'].append("database")

    if "mongo_host" in configs:
        services[_section]['configs'].append("mongodb")

    if "rabbitmq_host" in configs:
        services[_section]['configs'].append("rabbitmq")

    if "redis_host" in configs:
        services[_section]['configs'].append("redis")

    if "sms_server" in configs:
        services[_section]['configs'].append("sms")

    if "smtp_host" in configs:
        services[_section]['configs'].append("smtp")

    if "couch_host" in configs:
        services[_section]['configs'].append("couch")  

for i, e in enumerate(services):
    print '"{}": {},'.format(e, json.dumps(services[e]))



    # print '"{}": {},'.format(e, services[e])

# print json.dumps(services, indent=4)