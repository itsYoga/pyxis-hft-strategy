"""
OKX Trading Utilities
=====================
提供 OKX REST API 下單、撤單、查詢等功能
"""

import aiohttp
import json
import time
import hmac
import base64
import hashlib
import os


def generate_signature(timestamp, method, request_path, body='', secret_key=''):
    """Generate OKX API signature"""
    message = timestamp + method + request_path + body
    mac = hmac.new(
        bytes(secret_key, encoding='utf8'),
        bytes(message, encoding='utf-8'),
        digestmod='sha256'
    )
    return base64.b64encode(mac.digest()).decode()


async def place_order(session, inst_id, side, price, size, order_type='limit', 
                     api_key='', secret_key='', passphrase='', rest_url='https://www.okx.com'):
    """
    Place an order via OKX REST API
    
    Args:
        session: aiohttp.ClientSession
        inst_id: Instrument ID (e.g., 'BTC-USDT-SWAP')
        side: 'buy' or 'sell'
        price: Order price
        size: Order size
        order_type: 'limit' or 'market'
        api_key: OKX API Key
        secret_key: OKX Secret Key
        passphrase: OKX Passphrase
        rest_url: OKX REST API URL
        
    Returns:
        dict: Order response
    """
    timestamp = str(int(time.time()))
    request_path = '/api/v5/trade/order'
    
    body = json.dumps({
        'instId': inst_id,
        'tdMode': 'cross',  # Cross margin
        'side': side,
        'ordType': order_type,
        'sz': str(size),
        'px': str(price) if order_type == 'limit' else '',
    })
    
    signature = generate_signature(timestamp, 'POST', request_path, body, secret_key)
    
    headers = {
        'OK-ACCESS-KEY': api_key,
        'OK-ACCESS-SIGN': signature,
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': passphrase,
        'Content-Type': 'application/json'
    }
    
    if os.getenv('SANDBOX', 'true').lower() == 'true':
        headers['x-simulated-trading'] = '1'
    
    url = rest_url + request_path
    
    try:
        async with session.post(url, headers=headers, data=body) as response:
            result = await response.json()
            return result
    except Exception as e:
        return {'code': '-1', 'msg': str(e), 'data': []}


async def cancel_order(session, inst_id, ord_id, api_key='', secret_key='', 
                      passphrase='', rest_url='https://www.okx.com'):
    """
    Cancel an order via OKX REST API
    
    Args:
        session: aiohttp.ClientSession
        inst_id: Instrument ID
        ord_id: Order ID
        api_key: OKX API Key
        secret_key: OKX Secret Key
        passphrase: OKX Passphrase
        rest_url: OKX REST API URL
        
    Returns:
        dict: Cancel response
    """
    timestamp = str(int(time.time()))
    request_path = '/api/v5/trade/cancel-order'
    
    body = json.dumps({
        'instId': inst_id,
        'ordId': ord_id,
    })
    
    signature = generate_signature(timestamp, 'POST', request_path, body, secret_key)
    
    headers = {
        'OK-ACCESS-KEY': api_key,
        'OK-ACCESS-SIGN': signature,
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': passphrase,
        'Content-Type': 'application/json'
    }
    
    if os.getenv('SANDBOX', 'true').lower() == 'true':
        headers['x-simulated-trading'] = '1'
    
    url = rest_url + request_path
    
    try:
        async with session.post(url, headers=headers, data=body) as response:
            result = await response.json()
            return result
    except Exception as e:
        return {'code': '-1', 'msg': str(e), 'data': []}


async def get_order_status(session, inst_id, ord_id, api_key='', secret_key='', 
                          passphrase='', rest_url='https://www.okx.com'):
    """
    Get order status via OKX REST API
    
    Args:
        session: aiohttp.ClientSession
        inst_id: Instrument ID
        ord_id: Order ID
        api_key: OKX API Key
        secret_key: OKX Secret Key
        passphrase: OKX Passphrase
        rest_url: OKX REST API URL
        
    Returns:
        dict: Order status
    """
    timestamp = str(int(time.time()))
    request_path = f'/api/v5/trade/order?instId={inst_id}&ordId={ord_id}'
    
    signature = generate_signature(timestamp, 'GET', request_path, '', secret_key)
    
    headers = {
        'OK-ACCESS-KEY': api_key,
        'OK-ACCESS-SIGN': signature,
        'OK-ACCESS-TIMESTAMP': timestamp,
        'OK-ACCESS-PASSPHRASE': passphrase,
    }
    
    if os.getenv('SANDBOX', 'true').lower() == 'true':
        headers['x-simulated-trading'] = '1'
    
    url = rest_url + request_path
    
    try:
        async with session.get(url, headers=headers) as response:
            result = await response.json()
            return result
    except Exception as e:
        return {'code': '-1', 'msg': str(e), 'data': []}

