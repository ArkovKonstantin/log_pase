# -*- encoding: utf-8 -*-
import re
import collections
from datetime import datetime


def parse(
        ignore_files=False,
        ignore_urls=[],
        start_at=None,
        stop_at=None,
        request_type=None,
        ignore_www=False,
        slow_queries=False
):
    pattern = re.compile(r'(https?:\/\/)([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w\.-]*)*\/?')
    date_pattern = re.compile(r'(\d{1,2}/?[a-zA-Z]+/?\d{1,4} \d{2}:\d{2}:\d{2})')
    request_type_pattern = re.compile(r'([A-Z]*)\ (https?:\/\/)')
    queries_pattern = re.compile(r'[\d]+$')
    ignore_file_pattern = re.compile(r'\.[a-z]*$')

    c = collections.Counter()
    data = collections.Counter()

    with open('log.log', 'r') as r:
        for line in r.readlines():
            try:
                request = pattern.search(line).group()

                if ignore_files:
                    file = ignore_file_pattern.search(line)
                    if file is not None:
                        return []

                if request.startswith('https'):
                    request = request.replace('https', 'http', 1)

                if ignore_www:
                    if request.split('://')[1].startswith('www'):
                        request = request.split('://')[0] + '://' + request.split('://')[1].replace('www.', '', 1)

                if start_at:
                    date_string = date_pattern.search(line).group()
                    dt = datetime.strptime(date_string, "%d/%b/%Y %H:%M:%S")
                    if dt < start_at:
                        continue

                if stop_at:
                    date_string = date_pattern.search(line).group()
                    dt = datetime.strptime(date_string, "%d/%b/%Y %H:%M:%S")
                    if dt > stop_at:
                        break

                if request_type:
                    rt = request_type_pattern.search(line).group()
                    if rt.split(' ')[0] != request_type:
                        continue

                if ignore_urls:
                    ignore_urls = list(map(lambda x: pattern.search(x).group(), ignore_urls))
                    ignore_urls = list(
                        map(lambda x: x.replace('https', 'http', 1) if x.startswith('https') else x, ignore_urls))
                    try:
                        ignore_urls.index(request)
                        continue
                    except ValueError:
                        pass

                if slow_queries:
                    queries = queries_pattern.search(line).group()
                    q = int(queries)
                    data[request] += q

                c[request] += 1

            except AttributeError:
                continue

    result = []
    if slow_queries:
        for i in data:
            for j in c:
                if i == j:
                    result.append(data[i] // c[j])
        return sorted(result, reverse=True)[:5]

    return sorted(list(dict(c).values()), reverse=True)[:5]

