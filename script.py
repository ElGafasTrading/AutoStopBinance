import configparser
from binance.client import Client
import math
import time
import config

print("")
print("##################################")
print("        -CRYPTO SPARTANS-         ")
print("     -STOP LOSS AUTOMATICO-       ")
print("##################################")
print("                 By ElgafasTrading")
print("")

tick = ""
entryPrice = 0.0
positionAMT = 0.0
stopLoss = 0

tick_size = 0.0

client = Client(config.API_KEY, config.API_SECRET, tld='com')


def get_quantity_precision(current_symbol):
    global step_size
    global tick_size
    while True:
        try:
            info = client.futures_exchange_info()
        except Exception as e_rror:
            print(e_rror)
            archivo_e = open("log.txt", "a")
            mensaje_e = time.strftime('%d-%m-%Y %H:%M:%S', time.localtime()) + ' ERROR: ' + str(e_rror) + "\n"
            archivo_e.write(mensaje_e)
            archivo_e.close()
            time.sleep(2)
        else:
            break
    info = info['symbols']
    for x in range(len(info)):
        if info[x]['symbol'] == current_symbol:
            for f in info[x]['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    step_size = float(f['stepSize'])
                if f['filterType'] == 'PRICE_FILTER':
                    tick_size = float(f['tickSize'])
            return info[x]['pricePrecision'], info[x]['quantityPrecision']
    return None


def positionInfo(tick):
    while True:
        try:
            currentPosition = client.futures_position_information(symbol=tick)
        except Exception as e:
            print(e)
            archivo = open("log.txt", "a")
            mensaje = time.strftime('%d-%m-%Y %H:%M:%S',
                                    time.localtime()) + ' ERROR: ' + str(
                e) + "\n"
            archivo.write(mensaje)
            archivo.close()
            time.sleep(2)
        else:
            break
    return currentPosition


def getStopPrice(entryPrice, porcentaje, tick, side):
    pricePrecision = get_quantity_precision(tick)
    stopPrice = round(float(entryPrice + (entryPrice * porcentaje / 100)), pricePrecision[0])
    if side == 'SELL':
        stopPrice = round(float(entryPrice - (entryPrice * porcentaje / 100)), pricePrecision[0])
    stopPrice = "{:0.0{}f}".format(stopPrice, pricePrecision[0])
    precision = int(round(-math.log(tick_size, 10), 0))
    stopPrice = float(round(float(stopPrice), precision))

    return stopPrice


while True:
    while len(tick) == 0:
        tick = input("INGRESE EL TICK: ").upper()
        tick = tick + 'USDT'
    if stopLoss == 0:
        while True:
            try:
                stopLoss = float(input("INGRESE EL VALOR DE STOP LOSS EN DOLARES: "))
                break
            except:
                print("VALOR INVALIDO, INGRESE UN NUMERO VALIDO")
    info = positionInfo(tick)
    if float(info[0].get('positionAmt')) != 0:
        print("positionAmt: " + str(info[0].get('positionAmt')) + " entryPrice: " + str(
            info[0].get('entryPrice')) + " leverage: " + str(info[0].get('leverage')))
        if entryPrice != float(info[0].get('entryPrice')) or positionAMT != float(info[0].get('positionAmt')):
            entryPrice = float(info[0].get('entryPrice'))
            positionAMT = float(info[0].get('positionAmt'))
            openOrders = client.futures_get_open_orders(symbol=tick)
            if len(openOrders) > 0:
                orderID = 0
                for order in openOrders:
                    if order['type'] == 'STOP_MARKET':
                        orderID = order['orderId']
                if orderID != 0:
                    client.futures_cancel_order(symbol=tick, orderId=orderID)
                    print("ORDEN STOP LOSS CANCELADA")
            side = 'BUY'
            if positionAMT > 0:
                side = 'SELL'
                positionAMT2 = positionAMT
            else:
                positionAMT2 = positionAMT * -1
            porcentaje = (stopLoss * 100) / (entryPrice * positionAMT2)
            print(porcentaje)
            stopPrice = getStopPrice(entryPrice, porcentaje, tick, side)
            print("STOP LOSS: " + str(stopPrice))
            if stopPrice < 0:
                print('Stop Loss menor que 0')
            else:
                while True:
                    try:
                        client.futures_create_order(
                            symbol=tick,
                            type='STOP_MARKET',
                            side=side,
                            stopPrice=stopPrice,
                            closePosition=True
                        )
                    except Exception as e:
                        print(e)
                        archivo = open("log.txt", "a")
                        mensaje = time.strftime('%d-%m-%Y %H:%M:%S',
                                                time.localtime()) + ' ERROR: ' + str(
                            e) + "\n"
                        archivo.write(mensaje)
                        archivo.close()
                        time.sleep(2)
                    else:
                        break
    else:
        print("NO HAY POSICIONES ABIERTAS EN: " + tick)
        openOrders = client.futures_get_open_orders(symbol=tick)
        if len(openOrders) > 0:
            orderID = 0
            for order in openOrders:
                if order['type'] == 'STOP_MARKET':
                    orderID = order['orderId']
            if orderID != 0:
                client.futures_cancel_order(symbol=tick, orderId=orderID)
                print("ORDEN STOP LOSS CANCELADA")
        tick = ""
        stopLoss = 0
        entryPrice = 0.0
        positionAMT = 0.0

    time.sleep(2)
