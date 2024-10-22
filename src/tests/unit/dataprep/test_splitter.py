# Copyright (C) 2024 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

from comps.dataprep.utils.splitter import Splitter

def test_text_splitter():
    text = "Marry had a little lamb"
    s = Splitter(chunk_size=5, chunk_overlap=3)
    splitted_text = s.split_text(text)

    assert len(splitted_text) == 6
    assert splitted_text == ['Marry', 'had', 'a', 'litt', 'ittle', 'lamb']

def test_html_splitter():
    text = "<html><body><h1>Header 1</h1><p>hello</p><h2>Header 2</h2><p>world</p><h3>Header 3</h3></body></html>"
    s = Splitter(chunk_size=5, chunk_overlap=3)
    splitted_text = s.split_html(text)

    assert splitted_text == ['hello', 'world']
