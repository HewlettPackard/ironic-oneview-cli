# -*- encoding: utf-8 -*-
#
# Copyright 2015 Hewlett-Packard Development Company, L.P.
# Copyright 2015 Universidade Federal de Campina Grande
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from itertools import zip_longest
import json
from math import floor
from matplotlib import use
use('PS')
import matplotlib.pyplot as plt
import pandas as pd
import sys


def grouper(iterable, n, fillvalue=None):
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def parse_raw_data(filename):
    metrics_names = ['start_time', 'end_time']
    result = {key: [] for key in metrics_names}
    with open(filename, 'r') as file:
        for request_line, response_line in grouper(file, 2):
            if not response_line:
                break

            request = json.loads(request_line)
            response = json.loads(response_line)

            assert request.get('method') == response.get('method'), \
                'not parsing a pair'

            parse_metrics(result, request, response)
    return dict_to_df(result)


def parse_metrics(dict, request, response):
    dict.get('start_time').append(request.get('time'))
    dict.get('end_time').append(response.get('time'))


def dict_to_df(metrics_dict):
    df = pd.DataFrame(metrics_dict)
    df['start_time'] = pd.to_datetime(df.pop('start_time'), utc=True)
    df.index = df['start_time']

    df['end_time'] = pd.to_datetime(df.pop('end_time'), utc=True)
    df['response_time'] = df['end_time'] - df['start_time']

    return df


def calc_time_shift(min_time):
    day_shift = floor(min_time / 86400) * 86400
    min_shift = floor(min_time / 60) * 60
    return day_shift - min_shift


def plot_arrival_rate(df):

    resampled_df = df.start_time.resample('s').count().fillna(0)
    resampled_df.index = resampled_df.index.tz_localize('UTC')
    time_shift = calc_time_shift(min(resampled_df.index).timestamp())
    resampled_df = resampled_df.tshift(time_shift, freq='s')
    resampled_df.to_csv('arrival_rate.csv')

    plt.figure()
    resampled_df.plot(title='Requests arrival rate at OneView API')
    plt.xlabel('Elapsed Time (hh:mm)')
    plt.ylabel('Arrival Rate (request/s)')
    plt.savefig('arrival_rate.png')

    resampled_df = resampled_df.resample('min').mean()
    resampled_df.to_csv('avg_arrival_rate.csv')

    plt.figure()
    resampled_df.plot(
        title='Requests average arrival rate per minute at OneView API')
    plt.xlabel('Elapsed Time (hh:mm)')
    plt.ylabel('Average Arrival Rate (request/s)')
    plt.savefig('avg_arrival_rate.png')


if __name__ == "__main__":
    plot_arrival_rate(parse_raw_data(sys.argv[1]))
