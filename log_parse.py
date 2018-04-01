# -*- encoding: utf-8 -*-
import re
import collections
from datetime import datetime


def check_urls(request, ignore_urls):
    # На случай если в преданном url есть параметры
    ignore_urls = list(map(lambda x: division(x)['request'], ignore_urls))
    # На случай если в преданный url начинается с https
    ignore_urls = list(map(lambda x: x.replace('https', 'http', 1) if x.startswith('https') else x, ignore_urls))
    try:
        ignore_urls.index(request)
        return -1
    except ValueError:
        return 1


def interval(start_at, stop_at, date):
    if start_at:
        if date < start_at:
            return 1  # continue

    if stop_at:
        if date > stop_at:
            return -1  # break


def division(line) -> dict:
    log_structure = {}
    pattern = re.compile(r'(https?:\/\/)([\da-z\.-]+)\.([a-z\.]{2,6})([\/\w\.-]*)*\/?')  # паттерн для ulr
    date_pattern = re.compile(r'(\d{1,2}/?[a-zA-Z]+/?\d{1,4} \d{2}:\d{2}:\d{2})')  # для даты
    request_type_pattern = re.compile(r'([A-Z]*)\ (https?:\/\/)')  # тип запроса (GET,PUT, POST)
    queries_pattern = re.compile(r'[\d]+$')  # время выполнеия
    ignore_file_pattern = re.compile(r'\.[a-z]*$')  # Формат файла

    log_structure['request'] = pattern.search(line).group()
    log_structure['file'] = ignore_file_pattern.search(line)
    log_structure['date'] = datetime.strptime(date_pattern.search(line).group(), "%d/%b/%Y %H:%M:%S")
    log_structure['request_type'] = request_type_pattern.search(line).group()
    log_structure['queries'] = queries_pattern.search(line).group()
    return log_structure


def parse(
        ignore_files=False,
        ignore_urls=[],
        start_at=None,
        stop_at=None,
        request_type=None,
        ignore_www=False,
        slow_queries=False
):
    result = collections.defaultdict(list)
    with open('log.log', 'r') as r:
        for line in r.readlines():
            try:
                log_structure = division(line)
                request = log_structure['request']

                if ignore_files:
                    file = log_structure['file']
                    if file is not None:
                        continue

                if request.startswith('https'):
                    request = request.replace('https', 'http', 1)

                if ignore_www:
                    if request.split('://')[1].startswith('www'):
                        request = 'http://{}'.format(request.split('://')[1].replace('www.', '', 1))
                # Обработка логов в заданном интервале
                if interval(start_at, stop_at, log_structure['date']) == 1:
                    continue
                elif interval(start_at, stop_at, log_structure['date']) == -1:
                    break
                # Обработка запросов заданого типа (PUT,GET,POST)
                if request_type:
                    if log_structure['request_type'](' ')[0] != request_type:
                        continue

                if ignore_urls:
                    if check_urls(request, ignore_urls) < 0:
                        continue

                if result.get(request):
                    result[request][0] += 1  # если ключ есть инкрементируем
                else:
                    result[request].append(1)  # если данного ключа нет, то определяем два элемна для этого ключа
                    result[request].append(0)

                if slow_queries:
                    q = int(log_structure['queries'])
                    result[request][1] += q

            except AttributeError:
                continue

    if slow_queries:
        # получаем среднее значение запроса
        return sorted([item[1] // item[0] for item in list(result.values())], reverse=True)[:5]
    else:
        # преобразуем result[[],[],[]] -> [, , ,]
        return sorted([item[0] for item in list(result.values())], reverse=True)[:5]
