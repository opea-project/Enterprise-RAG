#!/bin/python3
# Copyright (C) 2025 Intel Corporation
# SPDX-License-Identifier: Apache-2.0

import fnmatch
import os
import sys
import pandas as pd

path = sys.argv[1]
files = fnmatch.filter(os.listdir(path), "bench_*.csv")
outputs = []
for file in files:
    users = file.split('_')[2].split('-')[1]
    delay = float(file.split('_')[3].split('-')[1].split('s')[0])
    try:
        df = pd.read_csv(os.path.join(path, file), header=None)
        df = df.set_axis(['Inputs','Outputs','First','Last','Err','Code'], axis=1)
        df['Next'] = ( df['Last'] - df ['First'] ) / df['Outputs']
        im = df['Inputs'].mean()
        i90 = df['Inputs'].quantile(0.9)
        om = df['Outputs'].mean()
        o90 = df['Outputs'].quantile(0.9)
        fm = df['First'].mean()
        f90 = df['First'].quantile(0.9)
        lm = df['Last'].mean()
        l90 = df['Last'].quantile(0.9)
        nm = df['Next'].mean()
        n90 = df['Next'].quantile(0.9)
        tps = 1 / nm * int(users)
        row = f'{users};{delay:.2f};{im:.2f};{i90:.2f};{om:.2f};{o90:.2f};{fm:.2f};{f90:.2f};{lm:.2f};{l90:.2f};{nm:.4f};{n90:.4f};{tps:.2f}'
        outputs.append(row)
    except Exception:
        pass

outputs = sorted(outputs, key=lambda x:int(x.split(';')[0]))
print("users;user_delay_sec;input_token_mean;input_token_p90;output_token_mean;output_token_p90;first_token_lat_mean;first_token_lat_p90;last_token_lat_mean;last_token_lat_p90;next_token_lat_mean;next_token_lat_p90;tokens_per_sec")
for out in outputs:
    print(out)
