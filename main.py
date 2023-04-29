import requests

import hashlib
import hmac

import time
import settings

def form_table(data):
    coins = {}
    for elem in data:
        if elem['from_coin'] not in coins:
            coins[elem['from_coin']] = []
        if elem['to_coin'] not in coins:
            coins[elem['to_coin']] = []

    for coin in coins:
        for elem in data:
            if coin == elem['from_coin'] or coin == elem['to_coin']:
                coins[coin].append(elem)

    return coins

def ask_or_bid(a):
    if a == 'from_coin':
        return 'ask'
    else:
        return 'bid'

def get_procent(s, a, bid, ask):
    if a == 'from_coin':
        return round(s / float(ask), 6)
    else:
        return round(s * float(bid), 6)

def msort2(x):
    if len(x) < 2:
        return x
    result = []
    mid = int(len(x) / 2)
    y = msort2(x[:mid])
    z = msort2(x[mid:])
    while (len(y) > 0) and (len(z) > 0):
        if y[0][0] < z[0][0]:
            result.append(z[0])
            z.pop(0)
        else:
            result.append(y[0])
            y.pop(0)
    result += y
    result += z
    return result

def form_top1(data:dict):
    for elem in data:
        print(data[elem])



def form_top(data:dict):
    list_data = []
    for coin in list(data.keys()):
        for elem in data[coin]:
            if elem['from_coin'] == coin:
                a0 = 'to_coin'
            else: 
                a0 = 'from_coin'
            for i in data[elem[a0]]:
                if a0 == 'from_coin':
                    a1 = 'to_coin'
                else:
                    a1 = 'from_coin'
                if i[a1] != coin:
                    if (i['from_coin'], i['to_coin']) != (elem['from_coin'], elem['to_coin']):
                        for j in data[i[a1]]:
                            if a1 == 'from_coin':
                                a2 = 'to_coin'
                            else:
                                a2 = 'from_coin'
                            if j[a2] == coin:
                                if (j['from_coin'], j['to_coin']) != (elem['from_coin'], elem['to_coin']) != (i['from_coin'], i['to_coin']):
                                    s = 10000
                                    s = get_procent(s, a0, elem['bid'], elem['ask'])
                                    s = get_procent(s, a1, i['bid'], i['ask'])
                                    s = get_procent(s, a2, j['bid'], j['ask'])
                                    summ = round( 100 * (s - 10000) / 10000, 5)
                                    if summ > 0:
                                        list_data.append([ summ, elem[a0], i[a1], j[a2], elem[a0], i[ask_or_bid(a1)], j[ask_or_bid(a2)], elem[ask_or_bid(a0)], i[f'volume_{ask_or_bid(a1)}'], j[f'volume_{ask_or_bid(a1)}'], elem[f'volume_{ask_or_bid(a1)}'], ask_or_bid(a1), ask_or_bid(a2), ask_or_bid(a0)])
    return list(msort2(list_data)[:settings.top_limit])

coins_data = []

def get_data():
    url = f"{settings.api_urls['main']}/api/v3/exchangeInfo"
    req = requests.get(url=url)
    exchange_info = req.json()
    couples = []
    # print(exchange_info)
    for s in exchange_info['symbols']:
        if s['status'] == 'TRADING' and s['symbol'] != 'AXSBIDR' and 'NBT' not in s['symbol'] and 'BRL' not in s['symbol']:
            couples.append([s['symbol'], s['baseAsset'], s['quoteAsset']])
    url = f"{settings.api_urls['main']}/api/v3/ticker/bookTicker"
    req = requests.get(url=url, headers={'symbols' : str(['BTCUSDT', 'ETHUSDT'])})
    res = req.json()
    # list_data = []
    for elem in res:
            for i in couples:
                if elem['symbol'] == i[0]:
                    coins_data.append({ 'symbol' : elem['symbol'], 'from_coin' : i[1], 'to_coin' : i[2], 'bid' : elem['bidPrice'], 'ask' :elem['askPrice'], 'volume_bid': elem['bidQty'], 'volume_ask': elem['askQty']})

         


def set_sign():
    timestamp = round(time.time() * 1000)
    sec_key = settings.secret_key
    query = f"timestamp={timestamp}&recvWindow=50000"
    signature = hmac.new(sec_key.encode(), query.encode(), hashlib.sha256).hexdigest()
    return query, signature

def find_active_coin():
    api_key = settings.api_key
    base_url = settings.api_urls['main']
    end_point = "/api/v3/account"
    query, signature = set_sign()
    active_coins = []
    r = requests.get(f"{base_url}{end_point}?{query}&signature={signature}", headers={'X-MBX-APIKEY': api_key})
    for elem in r.json()['balances']:
        if float(elem['free']) > 0:
            # print(elem['asset'], elem['free'])
            print(elem)

def algorithm_chech_volume(elem:list, swap_list:list):
    n = 0
    dict_swap_in_usdt = {}
    if 'USDT' in elem:
        n = elem.index('USDT')
    else:
        for coin in swap_list:
            if coin['from_coin'] in elem:
                n = elem.index(coin['from_coin'])
                dict_swap_in_usdt = coin
                break
            elif coin['to_coin'] in elem:
                n = elem.index(coin['to_coin'])
                dict_swap_in_usdt = coin
                break
    # print(dict_swap_in_usdt)

    if n == 0:
        return []


    if n == 1:
        i1,i2,i3 = 1,2,3 
    elif n == 2:
        i1,i2,i3 = 2,3,1
    else:
        i1,i2,i3 = 3,1,2


    s = 10_000_000_000
    #       0       1  2  3  4       5    6    7       8    9    10      11  12  13
    #    0.0844    AN  UP EL AN    10.0  0.75  2.0    3.0  50.0  1.0    ask ask bid
    if elem[10 + i1] == 'ask':
        s_1 = min( s, float(elem[9]) * float(elem[6]) )
        s = min( s, float(elem[7 + i1]) * float(elem[4 + i1]) ) / float(elem[4 + i1])
    else:
        s_1 = min( s, float(elem[9]))
        s = min( s, float(elem[7 + i1]) ) * float(elem[4 + i1])
    # print(f"Обменяли {s_1} {elem[i1]} на {s} {elem[i2]}")
    if elem[10 + i2] == 'ask':
        s_2 = min( s, float(elem[10]) * float(elem[7]) )
        s = min( s, float(elem[7 + i2]) * float(elem[4 + i2]) ) / float(elem[4 + i2])
    else:
        s_2 = min( s, float(elem[10]) )
        s = min( s, float(elem[7 + i2]) ) * float(elem[4 + i2])
    # print(f"Обменяли {s_2} {elem[i2]} на {s} {elem[i3]}")
    if elem[10 + i3] == 'ask':
        s_3 = min( s, float(elem[8]) * float(elem[5]) )
        s = min( s, float(elem[7 + i3]) * float(elem[4 + i3]) ) / float(elem[4 + i3])
    else:
        s_3 = min( s, float(elem[8]) )
        s = min( s, float(elem[7 + i3]) ) * float(elem[4 + i3])
    # print(f"Обменяли {s_3} {elem[i3]} на {s} {elem[i1]}")
    
    if 'USDT' in elem:
        a = round(s, 6)
    else:
        if dict_swap_in_usdt['from_coin'] == 'USDT':
            a = round(s / float(dict_swap_in_usdt['ask']), 6)
        else:
            a = round(s * float(dict_swap_in_usdt['bid']), 6)

    # return elem[:5] + elem[-3:] + [s_1, s, a]
    return elem + [a]



def check_volume(data:list, swap_list:list):
    new_data = []
    for i in range(0, len(data)):
        data[i] = algorithm_chech_volume(data[i], swap_list)
    print(data[0])
    print(data[1])
    print(data[2])
    for elem in data:
        if float(elem[0]) > 0.3 and elem[-1] > 10:
            new_data.append(elem)
    return new_data

def swap_coins():
    pass

def pass_circle():
    pass
    

def main():
    try:
        start_time = time.time()
        get_data()
        middle_time = time.time()
        table = form_table(coins_data)
        data = form_top(table)
        data = check_volume(data, table['USDT'])
        coins_data.clear()
        end_time = time.time()
        for elem in data:
            with open('data01.txt', 'a+') as f:
                for i in elem:
                    f.write(f"{i} ")
                f.write(f"TIME: {(int(end_time % 86400 // 3600)+3):02}:{int(end_time % 3600 // 60):02}:{int(end_time % 60):02} {round(middle_time-start_time, 4)} {round(end_time-middle_time, 4)} {round(end_time - start_time, 4)}\n")
            break
        print(f"Start time: {(int(start_time % 86400 // 3600)+3):02}:{int(start_time % 3600 // 60):02}:{int(start_time % 60):02} Time now: {(int(end_time % 86400 // 3600)+3):02}:{int(end_time % 3600 // 60):02}:{int(end_time % 60):02} Request time: {round(middle_time-start_time, 4)}s. Processing time: {round(end_time-middle_time, 4)}s. Full time: {round(end_time - start_time, 4)}s")
    except Exception as e:
        print(e)



if __name__ == '__main__':
    while True:    
        main()
    