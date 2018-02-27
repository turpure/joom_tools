#! usr/bin/python
# coding:utf8

import csv
import requests
from common.token import get_token


def get_all_products(alias_name, token):
    api = 'https://api-merchant.joom.com/api/v2/product/multi-get'
    parameters = {
        'access_token': token,
        'start': 0,
        'limit': 300,
    }
    session = requests.Session()
    r = session.get(api, params=parameters)
    ret = r.json()
    if isinstance(ret, dict):
        products = ret['data']
        for pro in products:
            yield pro['Product']['id']
        paging = ret['paging']
        while paging.has_key('next'):
            next_page = paging['next']
            res = session.get(next_page).json()
            if isinstance(res, dict):
                products = res['data']
                for pro in products:
                    yield pro['Product']['id']
                paging = res['paging']


def get_single_product(product_id, token):
    api = 'https://api-merchant.joom.com/api/v2/product'
    parameters = {
        'access_token': token,
        'id': product_id
    }
    session = requests.Session()

    try:
        ret = session.get(api, params=parameters).json()
        images = ret['data']['Product']['extra_images']
        return product_id, images
    except Exception as why:
        print why


if __name__ == "__main__":
    alias_name = 'Joom01-YHBaby'
    token = get_token(alias_name)
    with open('D:\joom_images.csv', 'wb') as f:
        writer = csv.writer(f)
        for pro in get_all_products(alias_name, token):
            row = get_single_product(pro, token)
            print "writing %s" % pro
            writer.writerow(row)





