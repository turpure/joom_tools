#! usr/bin/python
# coding:utf8

"""fetch products using request"""

import requests
from common.color import get_color_dict

color_dict = get_color_dict()


def fetch__products(base_url):
    headers = {
        'authorization': ('Bearer SEV0001MTUxOTcwOTIyM3xFWmJvMklNTEhiak00bmR'
                          'faTlHR3hvVFZjQ0FnM1J0Y2lRaTBjZjBYYzZNZk1UdGV6bmxj'
                          'SXY3dHpmbHdhcjhnTzFIaXVtY0JHdFNScVJRbThta2hnRFI5d'
                          'GstOG1RQTV1NzhIUHNDa2R5QVBqcXh4c0FJcnk4MzkzMGNrVG'
                          'xIaW5CY21kQTZLeWdhRzIxaUQ5NHFBeHpjZTkxMjhRdTJyNmd'
                          'adW1mSE43bDg9fGilWmQI8Z_gEFrC6nNCvX6CFqh0zT21rhbk'
                          'xiuioDfU'),
        'user-agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                       'AppleWebKit/537.36 (KHTML, like Gecko) '
                       'Chrome/64.0.3282.186 Safari/537.36'),
    }
    session = requests.Session()
    r = session.get(base_url, headers=headers)
    return r.json()


def parse_response(data):
    wanted_info = dict()
    if data is not None:
        main_info = dict()
        pro_info = data['payload']
        extra_images = pro_info['gallery']
        main_info['proId'] = pro_info['id']
        main_info['description'] = pro_info['engDescription']
        main_info['proName'] = pro_info['engName']
        main_info['categoryId'] = pro_info['categoryId']
        main_info['mainImage'] = pro_info['lite']['mainImage']['images'][-1]['url']
        for image in extra_images:
            main_info['extra_image' + str(extra_images.index(image))] = image['payload']['images'][-1]['url']
        pro_variants = pro_info['variants']

        for var in pro_variants:
            variants = dict()
            try:
                variants['colors'] = color_dict['#' + var['colors'][0]['rgb']]
            except:
                variants['colors'] = ''
            try:
                variants['size'] = var['size']
            except:
                variants['size'] = ''
            variants['msrPrice'] = var['msrPrice']
            variants['shipping'] = var['shipping']['price']
            variants['shippingTime'] = '-'.join([str(var['shipping']['minDays']), str(var['shipping']['maxDays'])])
            variants['price'] = var['price']
            try:
                variants['shippingWeight'] = var['shippingWeight']
            except:
                variants['shippingWeight'] = ''
            variants['varMainImage'] = var['mainImage']['images'][-1]['url']
            variants['quantity'] = var['inventory']
            wanted_info = dict(main_info, **variants)
            yield wanted_info


if __name__ == "__main__":
    base_url = 'https://api.joom.com/1.1/products/1504779018437136151-176-1-26193-2505906393'
    raw_data = fetch__products(base_url)
    for row in parse_response(raw_data):
        print row

