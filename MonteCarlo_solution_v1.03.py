import numpy as np
import copy
import math
from scipy.stats import lognorm
import pandas as pd
import random
from collections import deque
random.seed(12345)
np.random.seed(12345)

def data_input(df):
    #как закончу надо все эти штуки сделать неизменяемыми, чтоб случайно не изменить
    main_data = pd.read_excel(df, ['Общие параметры'])['Общие параметры']
    uplifts_count = int(main_data.loc[0, 'Значение'])

    recon_stats = dict()
    recon_data = pd.read_excel(df, ['ГРР'])['ГРР']
    recon_stats['cost'] = recon_data.loc[1, 'Разведка']
    recon_stats['teams'] = main_data.loc[1, 'Значение']
    recon_stats['duration'] = recon_data.loc[1, 'Unnamed: 1'] #месяцев

    tax_data = pd.read_excel(df, ['Экономика'])['Экономика']
    tax_stats = dict()
    tax_stats['tax'] = tax_data.loc[4, 'Ставка дисконтирования (%)']  # величина налога НДД
    tax_stats['r'] = tax_data.loc[0, 'Ставка дисконтирования (%)']  # коэф в DCF

    recon_stats = dict()
    recon_data = pd.read_excel(df, ['ГРР'])['ГРР']
    recon_stats['cost'] = recon_data.loc[1, 'Разведка']
    recon_stats['teams'] = main_data.loc[1, 'Значение']
    recon_stats['duration'] = recon_data.loc[1, 'Unnamed: 1']  # месяцев

    infra_data = pd.read_excel(df, ['Инфра'])['Инфра']
    well_stats = dict()
    well_stats['cost'] = infra_data.loc[1, 'Инфраструктура по сбору нефти для поднятия']  # тыс. рублей
    well_stats['duration'] = infra_data.loc[1, 'Unnamed: 1']  # месяцев

    pipe_stats = dict()
    pipe_stats['cost_multi'] = infra_data.loc[
        6, 'Инфраструктура по сбору нефти для поднятия']  # тыс. рублей / тыс. тонн #было 50000
    pipe_stats['cost_add'] = infra_data.loc[6, 'Unnamed: 1']  # тыс. рублей
    pipe_stats['oper_cost_multi'] = infra_data.loc[
        10, 'Инфраструктура по сбору нефти для поднятия']  # тыс. рублей/ тыс. тонн
    pipe_stats['oper_cost_add'] = infra_data.loc[10, 'Unnamed: 1']  # рублей
    pipe_stats['duration'] = infra_data.loc[13, 'Инфраструктура по сбору нефти для поднятия']  # месяцев
    pipe_stats['limit'] = infra_data.loc[
        16, 'Инфраструктура по сбору нефти для поднятия']  # тонн в месяц, ограничение по добычи в месяц, МЕНЯЕТСЯ

    cars_stats = dict()
    cars_stats['oper_cost_multi'] = infra_data.loc[
        21, 'Инфраструктура по сбору нефти для поднятия']  # тыс. рублей/ тыс. тонн #было 1000
    cars_stats['oper_cost_add'] = infra_data.loc[21, 'Unnamed: 1']  # тыс. рублей/ тыс. тонн
    cars_stats['limit'] = infra_data.loc[
        24, 'Инфраструктура по сбору нефти для поднятия']  # тыс. тонн в месяц, ограничение по добычи в месяц

    oil_stats = dict()
    oil_stats['netback'] = tax_data.loc[8, 'Ставка дисконтирования (%)']  # тыс. рублей/ тыс. тонн нефти 25000

    uplifts = []
    uplifts_data = pd.read_excel(df, ['Геология'])['Геология']
    for i in range(uplifts_count):
        now = dict()
        now['id'] = i
        now['probability'] = uplifts_data.loc[i, 'Шанс геологического успеха']
        now['mu'] = uplifts_data.loc[i, 'Параметр mu для извлекаемых запасов нефти']
        now['sigma'] = uplifts_data.loc[i, 'Параметр sigma для извлекаемых запасов нефти']
        now['oil_expectations'] = now['probability'] * lognorm.stats(now['sigma'], moments = 'm', scale = np.exp(now['mu']))

        now['money_expectations'] = dict()
        now['money_expectations']['pipe'] = (oil_stats['netback'] - pipe_stats['oper_cost_multi']) * now['oil_expectations'] \
                                    - recon_stats['cost'] - well_stats['cost']
        now['money_expectations']['cars'] = (oil_stats['netback'] - cars_stats['oper_cost_multi']) * now['oil_expectations'] \
                                    - recon_stats['cost'] - well_stats['cost']
        now['recon_rating'] = 0
        now['oil'] = 0  # количество нефти после разведки, если она там есть
        now['going_to_recon'] = False
        now['recon_already_planed'] = False
        now['reconed'] = False
        now['recon_time'] = 10 ** 8

        now['money'] = dict()
        now['money']['pipe'] = -10 ** 8
        now['money']['cars'] = -10 ** 8
        now['going_to_build'] = False
        now['build_already_planed'] = False
        uplifts.append(copy.deepcopy(now))

    return uplifts_count, recon_stats, uplifts, recon_stats, well_stats, pipe_stats, cars_stats, tax_stats, oil_stats

def data_printer(df):
    uplifts_count, recon_stats, uplifts, recon_stats, pipe_stats, cars_stats, tax_stats, oil_stats = data_input(df)
    print('uplifts_count:', uplifts_count)
    print()

    print('uplifts :')
    for uplift in uplifts:
        print(uplift)
    print()

    print('recon_stats:')
    print(recon_stats)
    print()

    print('pipe_stats:')
    print(pipe_stats)
    print()

    print('cars_stats')
    print(cars_stats)
    print()

    print('tax_stats')
    print(tax_stats)
    print()

    print('oil_stats')
    print(oil_stats)
    print()

def lognormal(uplift):
    return np.random.lognormal(uplift['mu'], uplift['sigma'])

def timeline_creation(n):
    timeline = []
    for i in range(n):
        now = dict()
        now['timeline_pointer'] = i
        now['recon_started'] = []
        now['recon_finished'] = []
        now['build_started'] = []
        now['build_finished'] = []
        now['pipe_build_started_this_month'] = False
        now['pipe_build_finished_this_month'] = False
        now['pipe_destroyed'] = False
        timeline.append(copy.deepcopy(now))
    return timeline

def recon_rating_create(uplifts, delivery_type):
    for uplift in uplifts:
        uplift['recon_rating'] = uplift['money_expectations'][delivery_type] / uplift['sigma']
    return uplifts

def recon_queue_create(recon_stats, timeline, uplifts):
    uplifts.sort(key = lambda uplift: uplift['recon_rating'], reverse = True)
    recon_queue = deque()
    for i in range(len(uplifts)):
        if uplifts[i]['going_to_recon']:
            recon_queue.append(uplift[i]['id'])
    uplifts.sort(key = lambda uplift: uplift['id'])
    return recon_queue

def recon_set(recon_stats, timeline, uplifts, start_pointer, finish_pointer, recon_teams_free_time, first_free_recon_team_pointer):
    for team_id in range(recon_stats['teams']):
        recon_teams_free_time[team_id] = max(recon_teams_free_time[team_id], start_pointer)

    uplifts.sort(key=lambda uplift: uplift['recon_rating'], reverse=True)
    for i in range(len(uplifts)):
        #print(recon_teams_free_time)
        if recon_teams_free_time[first_free_recon_team_pointer] < finish_pointer and uplifts[i]['going_to_recon'] and not uplifts[i]['recon_already_planed']:
            recon_start_time = recon_teams_free_time[first_free_recon_team_pointer]
            #timeline_pointer[recon_start_time] = (i // recon_stats['teams']) * recon_stats['duration']
            timeline[recon_start_time]['recon_started'].append(uplifts[i]['id'])
            #print(recon_start_time)
            timeline[recon_start_time + recon_stats['duration']]['recon_finished'].append(uplifts[i]['id'])

            uplifts[i]['recon_time'] = recon_start_time + recon_stats['duration']
            uplifts[i]['recon_already_planed'] = True

            recon_teams_free_time[first_free_recon_team_pointer] += recon_stats['duration']
            first_free_recon_team_pointer += 1
            first_free_recon_team_pointer %= recon_stats['teams']
            #print(recon_teams_free_time)
    uplifts.sort(key=lambda uplift: uplift['id'])
    return uplifts, recon_teams_free_time, first_free_recon_team_pointer

def timeline_build_update(timeline, uplifts, last_well_build_and_recon_finish_time, start_time): #после выбора всех скважин, где будем бурить
    #print('ujshgujshgjhsjghsujhg')
    for uplift in uplifts:
        if uplift['going_to_build'] and not uplift['build_already_planed']:
            #print(start_time, uplift['recon_time'])
            build_start = max(start_time, uplift['recon_time'])
            #print(build_start)
            #print(uplift['id'])
            timeline[build_start]['build_started'].append(uplift['id'])
            timeline[build_start + well_stats['duration']]['build_finished'].append(uplift['id'])
            uplift['build_already_planed'] = True

            last_well_build_and_recon_finish_time = max(last_well_build_and_recon_finish_time, build_start + well_stats['duration'])
    return timeline, last_well_build_and_recon_finish_time

def printer(timeline):
    for i in timeline:
        print(i)
    return

def income_per_month(timeline_pointer, timeline, oil_stats, oper_stats, pipe_stats, cars_stats, oil_avalible, delivery_type):
    multi = oper_stats['multi']
    add = oper_stats['add']
    limit = oper_stats['limit']

    oil_for_sale = min(oil_avalible, limit)
    operating_costs = oil_for_sale * multi + add
    if oil_for_sale == 0 and delivery_type == 'cars':
        operating_costs -= add
    income = oil_for_sale * oil_stats['netback'] - operating_costs
    oil_avalible -= oil_for_sale
    #print(income, oil_avalible, 'imcome, oil_avalible')
    return income, oil_avalible


def expenses_per_month(timeline_pointer, timeline, recon_stats, pipe_stats, well_stats, uplifts):
    expenses = 0
    new_oil = 0
    for uplift_id in timeline[timeline_pointer]['recon_started']:
        expenses -= recon_stats['cost']
    for uplift_id in timeline[timeline_pointer]['build_started']:
        expenses -= well_stats['cost']
    if timeline[timeline_pointer]['pipe_build_started_this_month']:
        expenses -= (pipe_stats['cost_multi'] * pipe_stats['limit'] + pipe_stats['cost_add'])
    for uplift_id in timeline[timeline_pointer]['build_finished']:
        new_oil += uplifts[uplift_id]['oil']
    return expenses, new_oil

def fcf_and_oil_avalible_per_month(timeline_pointer, timeline, recon_stats, oil_stats, oper_stats, pipe_stats, cars_stats, well_stats, oil_avalible, fcf, uplifts, delivery_type):
    #print(oper_stats, 'q')
    income, oil_avalible = income_per_month(timeline_pointer, timeline, oil_stats, oper_stats, pipe_stats, cars_stats, oil_avalible, delivery_type)
    expenses, new_oil = expenses_per_month(timeline_pointer, timeline, recon_stats, pipe_stats, well_stats, uplifts)
    fcf += income + expenses
    oil_avalible = oil_avalible + new_oil
    return fcf, oil_avalible

def uplifts_update_per_month(uplifts, timeline_pointer, timeline):
    for uplift_id in timeline[timeline_pointer]['recon_finished']:
        uplifts[uplift_id]['reconed'] = True
        uplifts[uplift_id]['oil'] = recon_results(uplift)
    return uplifts


def end_of_year(npv, fcf, losses, tax_stats, year):
    k = year - 2021
    if fcf + losses > 0:
        fcf *= tax_stats['tax']
    dcf = (fcf / ((1 + tax_stats['r']) ** k))
    losses = min(fcf + losses, 0)
    npv += dcf
    return npv, losses

def oil_expectation_with_considering_reconed_wells(uplifts):
    for uplift in uplifts:
        if not uplift['reconed']:
            #print(uplift['id'], 'not reconed')
            uplift['oil'] = uplift['oil_expectations']
    return uplifts

def oil_generation_with_considering_reconed_wells(uplifts):
    for uplift in uplifts:
        if not uplift['reconed']:
            if random.random() <= uplift['probability']:
                uplift['oil'] = lognormal(uplift)
            else:
                uplift['oil'] = 0
    return uplifts

#главное отличие между def choose_wells_to_build и choose_wells_to_recon, что первое из низ мы выбираем из броска точек в монтекарло, а второе из матожидания
def choose_wells_to_recon(uplifts, delivery_type):
    for uplift in uplifts:
        if uplift['money_expectations'][delivery_type] > 0:
            uplift['going_to_recon'] = True
    return uplifts

def choose_wells_to_build(uplifts, delivery_type):
    for uplift in uplifts:
        if uplift['money'][delivery_type] > 0 and uplift['recon_already_planed']:
            uplift['going_to_build'] = True
    return uplifts

def uplifts_money_update(uplifts, oil_stats, pipe_stats, cars_stats):
    for uplift in uplifts:
        uplift['money']['pipe'] = (oil_stats['netback'] - pipe_stats['oper_cost_multi']) * uplift['oil'] - \
                               well_stats['cost']
        uplift['money']['cars'] = (oil_stats['netback'] - cars_stats['oper_cost_multi']) * uplift['oil'] - \
                               well_stats['cost']
    return uplifts

def timeline_pipe_build_update(timeline, pipe_build_year, pipe_build_month, pipe_stats):
    timeline_pointer = (pipe_build_year - 2021) * 12 + pipe_build_month
    timeline[timeline_pointer]['pipe_build_started_this_month'] = True
    pipe_build_finished_time = timeline_pointer + pipe_stats['duration']
    for time in range(pipe_build_finished_time, len(timeline)):
        timeline[time]['pipe_build_finished'] = True
    timeline[pipe_build_finished_time]['pipe_build_finished_this_month'] = True
    return timeline

def add_multi_oper_stats_update_type(pipe_stats, cars_stats, delivery_type):
    oper_stats = dict()
    if delivery_type == 'pipe':
        oper_stats['multi'] = pipe_stats['oper_cost_multi']
        oper_stats['add'] = pipe_stats['oper_cost_add']
        oper_stats['limit'] = pipe_stats['limit']
    elif delivery_type == 'cars':
        oper_stats['multi'] = cars_stats['oper_cost_multi']
        oper_stats['add'] = cars_stats['oper_cost_add']
        oper_stats['limit'] = cars_stats['limit']
    else:
        oper_stats['multi'] = 0
        oper_stats['add'] = 0
        oper_stats['limit'] = 0
    return oper_stats

def last_well_build_and_recon_finish_time_update(now_pointer, timeline, last_well_build_and_recon_finish_time):
    for timeline_pointer in range(now_pointer, len(timeline)):
        if len(timeline[timeline_pointer]['recon_finished']) != 0 or len(timeline[timeline_pointer]['build_finished']) != 0:
            last_well_build_and_recon_finish_time = timeline_pointer
    return last_well_build_and_recon_finish_time

#функция, котоаря возвращает результаты разведки
#предварительно мы сами их генерируем зная распределение
#на самом деле просто после каждой разведки должна штука человеком заполняться
def recon_results_create(uplifts):
    recon_results = [-1 for i in range(len(uplifts))]
    for i in range(len(uplifts)):
        if random.random() <= uplifts[i]['probability']:
            recon_results[i] = lognormal(uplifts[i])
        else:
            recon_results[i] = 0
    return recon_results

def uplifts_oil_update_generation_with_considering_reconed_wells(uplifts, recon_results):
    for uplift in uplifts:
        if uplift['reconed']:
            uplift['oil'] = recon_results[uplift['id']]
        else:
            uplift['oil'] = lognormal(uplift)
    return uplifts


def uplifts_reconed_update(timeline, uplifts, pipe_build_year, pipe_build_month):
    pipe_build_timeline_pointer = (pipe_build_year - 2021) * 12 + pipe_build_month
    for timeline_pointer in range(pipe_build_timeline_pointer):
        for uplift_id in timeline[timeline_pointer]['recon_finished']:
            uplifts[uplift_id]['reconed'] = True                                      #тут тоже указатель а не индекс надо по-хорошему
    return uplifts



#это функция, которая считает "максимальный" доход всего проекта, если мы построим трубопровод в день x
#в последтсвии можно ее будет обобжить для бОльшей ситуации
def simulation_cars_pipe(timeline, uplifts, pipe_build_year, pipe_build_month, tax_stats, pipe_stats, cars_stats, recon_teams_free_time, first_free_recon_team_pointer, last_well_build_and_recon_finish_time):
    # помечаем участок таймлайна, который надо дозаполнить
    pipe_build_timeline_pointer = (pipe_build_year - 2021) * 12 + pipe_build_month
    start_pointer = pipe_build_timeline_pointer
    finish_pointer = len(timeline)

    #разведка
    delivery_type = 'pipe'
    uplifts = recon_rating_create(uplifts, delivery_type)
    uplifts = choose_wells_to_recon(uplifts, delivery_type)

    # наносим на таймлайн разведку
    uplifts, recon_teams_free_time, first_free_recon_team_pointer = recon_set(recon_stats, timeline, uplifts,
                                                                              start_pointer, finish_pointer,
                                                                              recon_teams_free_time,
                                                                              first_free_recon_team_pointer)

    # выбираем скважины которые построим
    #printer(uplifts)
    uplifts = choose_wells_to_build(uplifts, delivery_type)

    # наносим их на timeline
    last_well_build_and_recon_finish_time = 0
    timeline, last_well_build_and_recon_finish_time = timeline_build_update(timeline, uplifts, last_well_build_and_recon_finish_time, start_pointer)

    #постройка трубопровода в таймлайне
    pipe_build_timeline_pointer = (pipe_build_year - 2021) * 12 + pipe_build_month
    timeline = timeline_pipe_build_update(timeline, pipe_build_year, pipe_build_month, pipe_stats)
    #printer(timeline)

    #обновим переменную, где лежит дата окончания последний разведки
    last_well_build_and_recon_finish_time = last_well_build_and_recon_finish_time_update(0, timeline,
                                                                                         last_well_build_and_recon_finish_time)

    #теперь по таймлайну считаем деньги
    delivery_type = 'cars'
    npv = 0
    losses = 0
    oil_avalible = 0
    for year in range(2021, 2051):
        fcf = 0
        for month in range(0, 12):
            #print(oper_stats, delivery_type, year, month, oil_avalible)
            timeline_pointer = (year - 2021) * 12 + month

            #строим трубопровод и начинаем возить им
            if timeline[timeline_pointer]['pipe_build_finished_this_month']:
                delivery_type = 'pipe'
                oper_stats = add_multi_oper_stats_update_type(pipe_stats, cars_stats, delivery_type)
                uplifts = choose_wells_to_build(uplifts, delivery_type) #достроим скважины, по котрым выгодно качать трубой
                start_pointer = timeline_pointer
                timeline = timeline, last_well_build_and_recon_finish_time = timeline_build_update(timeline, uplifts, last_well_build_and_recon_finish_time, start_pointer)
                #printer(timeline)

                # запоминаем день, когда предварительно планируем построить последнюю скважину и разведать последнюю скважину (чтобы потом сломать трубопровод)
                last_well_build_and_recon_finish_time = last_well_build_and_recon_finish_time_update(0, timeline, last_well_build_and_recon_finish_time)

            if timeline_pointer > last_well_build_and_recon_finish_time and oil_avalible == 0 and delivery_type == 'pipe':
                #for i in range(20):
                #    print(timeline_pointer)
                #print(timeline_pointer)
                timeline[timeline_pointer]['pipe_destroyed'] = True
                delivery_type = 'cars'
                oper_stats = add_multi_oper_stats_update_type(pipe_stats, cars_stats, delivery_type)

            oper_stats = add_multi_oper_stats_update_type(pipe_stats, cars_stats, delivery_type)
            fcf, oil_avalible = fcf_and_oil_avalible_per_month(timeline_pointer, timeline, recon_stats, oil_stats, oper_stats, pipe_stats, cars_stats, well_stats, oil_avalible, fcf, uplifts, delivery_type)
            #print(timeline_pointer, fcf, oil_avalible, 'fcf', 'oil_avalible')
            #print(income, 'income')
        #print(npv, 'before', fcf)
        #print(last_well_build_and_recon_finish_time, 'last_well_build_and_recon_finish_time')
        npv, losses = end_of_year(npv, fcf, losses, tax_stats, year)

        #print(npv, losses, 'npv, losses')
    #print(last_well_build_and_recon_finish_time, oil_avalible, delivery_type)
    return npv

def simulation_cars_cars(timeline, uplifts, pipe_build_year,
                                                pipe_build_month, tax_stats, cars_stats, recon_teams_free_time,
                                                first_free_recon_team_pointer):
    #помечаем участок таймлайна, который надо дозаполнить
    pipe_build_timeline_pointer = (pipe_build_year - 2021) * 12 + pipe_build_month
    start_pointer = pipe_build_timeline_pointer
    finish_pointer = len(timeline)

    #разведка
    delivery_type = 'cars'
    uplifts = recon_rating_create(uplifts, delivery_type)
    uplifts = choose_wells_to_recon(uplifts, delivery_type)

    # наносим разведку на таймлайн разведку
    uplifts, recon_teams_free_time, first_free_recon_team_pointer = recon_set(recon_stats, timeline, uplifts,
                                                                              start_pointer, finish_pointer,
                                                                              recon_teams_free_time,
                                                                              first_free_recon_team_pointer)

    # выбираем скважины которые построим
    #printer(uplifts)
    uplifts = choose_wells_to_build(uplifts, delivery_type)

    #наносим их на timeline
    last_well_build_and_recon_finish_time = 0  # он не нужен, но я просто не хочу лишнюю функцию писать
    timeline, last_well_build_and_recon_finish_time = timeline_build_update(timeline, uplifts, last_well_build_and_recon_finish_time, start_pointer)

    #printer(timeline)

    npv = 0
    losses = 0
    oil_avalible = 0
    #printer(uplifts)
    for year in range(2021, 2051):
        fcf = 0
        for month in range(0, 12):
            #print(oper_stats, delivery_type, year, month, oil_avalible)
            timeline_pointer = (year - 2021) * 12 + month

            oper_stats = add_multi_oper_stats_update_type(pipe_stats, cars_stats, delivery_type)
            fcf, oil_avalible = fcf_and_oil_avalible_per_month(timeline_pointer, timeline, recon_stats, oil_stats, oper_stats, [], cars_stats, well_stats, oil_avalible, fcf, uplifts, delivery_type)
            #print(timeline_pointer, fcf, oil_avalible, 'fcf', 'oil_avalible')
            #print(income, 'income')
        #print(npv, 'before', fcf)
        #print(last_well_build_and_recon_finish_time, 'last_well_build_and_recon_finish_time')
        npv, losses = end_of_year(npv, fcf, losses, tax_stats, year)

        #print(npv, losses, 'npv, losses')
    return npv

def simulation_cars_none(timeline, uplifts, pipe_build_year, pipe_build_month, tax_stats, cars_stats, recon_teams_free_time, first_free_recon_team_pointer):
    #после момента принятия решения закрываем проект, поэтому на таймлайн ничего больше наносить не нужно
    delivery_type = 'cars'
    losses = 0
    oil_avalible = 0
    npv = 0
    for year in range(2021, pipe_build_year + 1):
        fcf = 0
        this_year_last_month = 12
        if year == pipe_build_year:
            this_year_last_month = pipe_build_month
        for month in range(0, this_year_last_month):
            #print(oper_stats, delivery_type, year, month, oil_avalible)
            timeline_pointer = (year - 2021) * 12 + month

            oper_stats = add_multi_oper_stats_update_type(pipe_stats, cars_stats, delivery_type)
            fcf, oil_avalible = fcf_and_oil_avalible_per_month(timeline_pointer, timeline, recon_stats, oil_stats, oper_stats, [], cars_stats, well_stats, oil_avalible, fcf, uplifts, delivery_type)
            #print(timeline_pointer, fcf, oil_avalible, 'fcf', 'oil_avalible')
            #print(income, 'income')
        #print(npv, 'before', fcf)
        #print(last_well_build_and_recon_finish_time, 'last_well_build_and_recon_finish_time')
        npv, losses = end_of_year(npv, fcf, losses, tax_stats, year)

        #print(npv, losses, 'npv, losses')
    #printer(timeline)
    return npv





#пока не работает
#сначала надо симуляцию переписать так, чтобы мы получали ввод после разведки и меняли свое решение
def main(uplifts_count, uplifts, pipe_build_year, pipe_build_month, tax_stats, pipe_stats, cars_stats, well_stats):
    # помечаем участок таймлайна, который надо дозаполнить
    pipe_build_timeline_pointer = (pipe_build_year - 2021) * 12 + pipe_build_month
    start_pointer = 0
    finish_pointer = pipe_build_timeline_pointer

    #создаем timeline
    timeline = timeline_creation(12 * 30)

    # пусть это результаты разведки на момент принятия решения, по-идее их должен вводить человек
    # те он должен вводить только те, которые разведал
    recon_results = recon_results_create(uplifts)

    #до момента принятия решения разведуем только скважины, прибыльные с доставкой машиной
    delivery_type = 'cars'
    uplifts = choose_wells_to_recon(uplifts, delivery_type)
    uplifts = recon_rating_create(uplifts, delivery_type)

    #наносим разведку на таймлайн, помечаем, если успели начать разведывать
    recon_teams_free_time = [0 for i in range(recon_stats['teams'])]
    first_free_recon_team_pointer = 0
    uplifts, recon_teams_free_time, first_free_recon_team_pointer = recon_set(recon_stats, timeline, uplifts, start_pointer, finish_pointer, recon_teams_free_time, first_free_recon_team_pointer)
    #print(first_free_recon_team_pointer)
    #print(recon_teams_free_time)
    #print()

    #пометим те поднятия, которые на момент принятия решения мы разведали, чтоб не менять число нефти в них при броске точек
    #помечаем, если уже получили результат разведки
    uplifts = uplifts_reconed_update(timeline, uplifts, pipe_build_year, pipe_build_month)

    #print('qqqqqqqqqqqqqqqqqqqq')
    #printer(uplifts)
    #print('qqqqqqqqqqqqqqqqqqqq')

    # будем считать очки за каждую симуляцию
    points = dict()
    points['cars_pipe'] = 0
    points['cars_cars'] = 0
    points['cars_none'] = 0

    # паралельно будем считать сумму npv каждой симуляции одного типа
    sum_npv = dict()
    sum_npv['cars_pipe'] = 0
    sum_npv['cars_cars'] = 0
    sum_npv['cars_none'] = 0

    #теперь сами симуляции
    sim_count = 100
    for sim_number in range(sim_count):
        #генерируем число нефти в скважине учитвая, что мы знаем, сколько нефти в уже разведомых
        uplifts = uplifts_oil_update_generation_with_considering_reconed_wells(uplifts, recon_results)

        # обновляем число денег которое принесет каждая скважина при таком броске точек
        uplifts = uplifts_money_update(uplifts, oil_stats, pipe_stats, cars_stats)
        #print(uplifts)
        #printer(uplifts)
        #print('mmmmmmmmmmmmmmmmmmmmmmmmmmmm')

        #нанаосим на таймлайн скважины, которые в любом случае построили бы
        uplifts = choose_wells_to_build(uplifts, 'cars')
        last_well_build_and_recon_finish_time = pipe_build_timeline_pointer
        start_time = 0
        timeline, last_well_build_and_recon_finish_time = timeline_build_update(timeline, uplifts, last_well_build_and_recon_finish_time, start_time)
        #printer(timeline)
        #printer(uplifts)
        #for i in range(30):
        #    print('------------------')

        npv = dict()
        npv['cars_none'] = simulation_cars_none(copy.deepcopy(timeline), copy.deepcopy(uplifts), pipe_build_year,
                                                pipe_build_month, tax_stats, cars_stats, copy.deepcopy(recon_teams_free_time),
                                                first_free_recon_team_pointer)
        npv['cars_cars'] = simulation_cars_cars(copy.deepcopy(timeline), copy.deepcopy(uplifts), pipe_build_year,
                                                pipe_build_month, tax_stats, cars_stats, copy.deepcopy(recon_teams_free_time),
                                                first_free_recon_team_pointer)
        npv['cars_pipe'] = simulation_cars_pipe(copy.deepcopy(timeline), copy.deepcopy(uplifts), pipe_build_year,
                                                pipe_build_month, tax_stats, pipe_stats, cars_stats, copy.deepcopy(recon_teams_free_time),
                                                first_free_recon_team_pointer, last_well_build_and_recon_finish_time)
        #print(npv)
        max_npv = max(npv['cars_pipe'], npv['cars_cars'], npv['cars_none'])
        for sim_type in points.keys():
            sum_npv[sim_type] += npv[sim_type]
            if npv[sim_type] == max_npv:
                points[sim_type] += 1

        # print(points)
    max_points = max(points['cars_pipe'], points['cars_cars'], points['cars_none'])
    if points['cars_none'] == max_points:
        average_npv = sum_npv['cars_none'] / sim_count
        print('Shut down the project in the', pipe_build_year, 'year in the', pipe_build_month, 'month')
        print('project emv = ', average_npv)
    elif points['cars_cars'] == max_points:
        average_npv = sum_npv['cars_cars'] / sim_count
        print('Keep using cars delivery and do not build a pipiline in the', pipe_build_year, 'year in the',
              pipe_build_month, 'month')
        print('project emv = ', average_npv)
    elif points['cars_pipe'] == max_points:
        average_npv = sum_npv['cars_pipe'] / sim_count
        print('The construction of the pipeline should begin in the', pipe_build_year, 'year in the', pipe_build_month,
              'month')
        print('project emv = ', average_npv)
    return sum_npv



data_frame = pd.ExcelFile('Датасет.xlsx')
pipe_build_year, pipe_build_month = 2021, 6

uplifts_count, recon_stats, uplifts, recon_stats, well_stats, pipe_stats, cars_stats, tax_stats, oil_stats = data_input(data_frame)

print(main(uplifts_count, uplifts, pipe_build_year, pipe_build_month, tax_stats, pipe_stats, cars_stats, well_stats))
