#!/bin/python3
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import defusedxml.ElementTree as ET
import os
import sys

def strip_tags(t):
    t = elem.tag
    idx = t.rfind("}")
    if idx != -1:
        t = t[idx + 1:]
    return t

events = ("start", "end")
splited_file_size_bytes = 8388608 # 8 megabytes

wiki_path = sys.argv[1]
out_dir = sys.argv[2]
num = 0
fname = os.path.join(out_dir, "wiki" + '{:04d}'.format(num) + ".txt")
out_file = open(fname, "wb")

for event, elem in ET.iterparse(wiki_path, events=events):
    if event == 'end':
        tname = strip_tags(elem.tag)
        if tname == 'text':
            if elem.text:
                line = elem.text.replace("[","").replace("]","").replace("{","").replace("}","") + "\n"
                out_file.write(line.encode('utf-8-sig', 'replace'))
                out_file.flush()
                if os.stat(fname).st_size > splited_file_size_bytes:
                    out_file.close()
                    num = num + 1
                    fname = os.path.join(out_dir, "wiki" + '{:04d}'.format(num) + ".txt")
                    out_file = open(fname, "wb")
    elem.clear()
out_file.close()
