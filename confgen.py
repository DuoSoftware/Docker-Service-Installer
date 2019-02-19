#!/usr/bin/env python

"""
Utitlity script to generate dependent environment variables for each service using the service installer file.
Author: Nimeshka Srimal
"""

import sys
import re


with open('conf.txt') as f:
    lines = f.readlines()
    section = ''
    section_strp = ''
    last_match = ''

    for a in lines:

        match = re.match(r"^\"(.*)\"\).*$",a.strip())
        if match:
            if section_strp != "":
                print '[' + last_match + ']'
                envvars = re.findall(r"(\$[A-Z_]+)",section_strp)
                if envvars:
                    envvars = list(set(envvars))
                    for i in envvars:
                        print i[1:] + ':'
                else:
                    print 'No vars'

            print "\n"
            section_strp = ''
            last_match = match.group(1)
        else:
            section_strp += a.strip()