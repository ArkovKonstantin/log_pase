# -*- encoding: utf-8 -*-
import re
import collections
from datetime import datetime


def check_urls(request, ignore_urls, pattern):
    ignore_urls = list(map(lambda x: pattern.search(x).group(), ignore_urls))
    ignore_urls = list(
        map(lambda x: x.replace('https', 'http', 1) if x.startswith('https') else x, ignore_urls))
    try:
        ignore_urls.index(request)
        return -1
    except ValueError:
        return 1


def interval(start_at, stop_at, date_pattern, line):
    if start_at:
        date_string = date_pattern.search(line).group()
        dt = datetime.strptime(date_string, "%d/%b/%Y %H:%M:%S")
        if dt < start_at:
            return 1  # continue

    if stop_at:
        date_string = date_pattern.search(line).group()
        dt = datetime.strptime(date_string, "%d/%b/%Y %H:%M:%S")
        if dt > stop_at:
            return -1  # break


def parse(
        ignore_files=False,
        ignore_urls=[],
        start_at=None,
        stop_at=None,
        request_type=None,
        ignore_www=False,
        slow_queries=False
):
    pattern = re.compile(r'(https?:\/\/)([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w\.-]*)*\/?')  # паттерн для ulr
    date_pattern = re.compile(r'(\d{1,2}/?[a-zA-Z]+/?\d{1,4} \d{2}:\d{2}:\d{2})')  # для даты
    request_type_pattern = re.compile(r'([A-Z]*)\ (https?:\/\/)')  # тип запроса (GET,PUT, POST)
    queries_pattern = re.compile(r'[\d]+$')  # время выполнеия
    ignore_file_pattern = re.compile(r'\.[a-z]*$')  # Формат файла
    result = collections.defaultdict(list)
    with open('log.log', 'r') as r:
        for line in r.readlines():
            try:
                request = pattern.search(line).group()

                if ignore_files:
                    file = ignore_file_pattern.search(line)
                    if file is not None:
                        continue

                if request.startswith('https'):
                    request = request.replace('https', 'http', 1)

                if ignore_www:
                    if request.split('://')[1].startswith('www'):
                        request = 'http://{}'.format(request.split('://')[1].replace('www.', '', 1))
                # Обработка логов в заданном интервале
                if interval(start_at, stop_at, date_pattern, line) == 1:
                    continue
                elif interval(start_at, stop_at, date_pattern, line) == -1:
                    break
                # Обработка запросов заданого типа (PUT,GET,POST)
                if request_type:
                    rt = request_type_pattern.search(line).group()
                    if rt.split(' ')[0] != request_type:
                        continue

                if ignore_urls:
                    if check_urls(request, ignore_urls, pattern) < 0:
                        continue

                if result.get(request):
                    result[request][0] += 1  # если ключ есть инкрементируем
                else:
                    result[request].append(1)  # если данного ключа нет, то определяем два элемна для этого ключа
                    result[request].append(0)

                if slow_queries:
                    queries = queries_pattern.search(line).group()
                    q = int(queries)
                    result[request][1] += q

            except AttributeError:
                continue

    if slow_queries:
        return sorted(
            [item[1] // item[0] for item in sorted(list(result.values()), key=lambda x: x[1], reverse=True)[:5]],
            reverse=True)  # получаем среднее значение запроса и преобразуем result[[],[],[]] -> [, , ,]
    else:
        return [item[0] for item in sorted(list(result.values()), reverse=True)[:5]]  # сортируем result
