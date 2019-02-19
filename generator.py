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

# First get all the services and add to the services dict.
with open('conf.txt') as f:
    lines = f.readlines()
    section = ''
    section_strp = ''
    last_match = ''

    for line in lines:
        match = re.match(r"^\"(.*)\"\).*$",line.strip())
        if match:

            if section_strp != "":
                service_type = "nodejs"
                envvars = re.findall(r"(\$GO_VERSION_TAG)",section_strp)

                if envvars:
                    service_type = "go"

                # print '"{}": {{ type: "{}", configs: [] }}, '.format(last_match, service_type)

                services[last_match] = {
                    "type" : service_type,
                    "configs": [ "general", last_match]
                }

                # we need to grab the github urls from the list as well...
                github_url = re.findall(r"https://github.com/(.*?).git", section_strp)
                services[last_match]['github_url'] = "https://github.com/" + github_url[0] + ".git"

            section_strp = ''
            last_match = match.group(1)

        else:
            section_strp += line.strip()

# now we will add remaining dependencies...

config = ConfigParser.RawConfigParser()
config.read("config.ini.full.backup")

for _section in config.sections():
    configs = dict(config.items(_section))

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
    print '"{}": {},'.format(e, services[e])

# print json.dumps(services, indent=4)          