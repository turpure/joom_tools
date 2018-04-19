#! usr/bin/python
# coding:utf8

"""fetch products using request"""

from sys import stdout

import requests
from common.color import get_color_dict
from common.db import Redis, MsSQL
from common.logger import log


color_dict = get_color_dict()
redis = Redis().redis()
ms_sql = MsSQL()

logger = log('Joom-crawler', 'fetching.log')


def fetch__products(pro_id):
    api = 'https://api.joom.com/1.1/products/'
    if not pro_id:
        raise Exception('Invalid pro ID', pro_id)
    base_url = api + pro_id

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
        try:
            tags_info = pro_info['nameExt']['tags']
            tags = ','.join([name['nameEng'] for name in tags_info])
        except:
            tags = ''
        main_info['tags'] = tags
        extra_images = pro_info['gallery']
        main_info['proId'] = pro_info['id']
        main_info['description'] = pro_info['engDescription']
        main_info['proName'] = pro_info['engName']
        try:
            main_info['categoryId'] = pro_info['categoryId']
        except:
            main_info['categoryId'] = ''
        main_info['mainImage'] = pro_info['lite']['mainImage']['images'][-1]['url']
        for image in extra_images:
            main_info['extra_image' + str(extra_images.index(image))] = image['payload']['images'][-1]['url']
        for i in range(0, 11-len(extra_images)):
            main_info['extra_image' + str(11-i-1)] = ''
        pro_variants = pro_info['variants']

        for var in pro_variants:
            variants = dict()
            try:
                try:
                    variants['color'] = color_dict['#' + var['colors'][0]['rgb']]
                except:
                    variants['color'] = var['colors'][0]['rgb']
            except:
                variants['color'] = ''
            try:
                variants['proSize'] = var['size']
            except:
                variants['proSize'] = ''
            try:
                variants['msrPrice'] = var['msrPrice']
            except:
                variants['msrPrice'] = 0
            variants['shipping'] = var['shipping']['price']
            variants['shippingTime'] = '-'.join([str(var['shipping']['minDays']), str(var['shipping']['maxDays'])])
            variants['price'] = var['price']
            try:
                variants['shippingWeight'] = var['shippingWeight']
            except:
                variants['shippingWeight'] = 0
            try:
                variants['varMainImage'] = var['mainImage']['images'][-1]['url']
            except:
                variants['varMainImage'] = ''
            variants['quantity'] = var['inventory']
            wanted_info = dict(main_info, **variants)
            yield wanted_info


def crawler():
    with ms_sql as con:
        cur = con.cursor()
        insert_sql = ("insert oa_data_mine_detail"
                      "(mid,parentId,proName,description,"
                      "tags,childId,color,proSize,quantity,"
                      "price,msrPrice,shipping,shippingWeight,"
                      "shippingTime,varMainImage,extra_image0,"
                      "extra_image1,extra_image2,extra_image3,"
                      "extra_image4,extra_image5,extra_image6,"
                      "extra_image7,extra_image8,extra_image9,"
                      "extra_image10,mainImage"
                      ") "
                      "values( %s,%s,%s,%s,%s,%s,%s,%s,"
                      "%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,"
                      "%s,%s,%s,%s,%s,%s,%s,%s)")
        update_sql = "update oa_data_mine set progress=%s where id=%s"
        code_sql = "select goodsCode from oa_data_mine where id=%s"
        main_image_sql = "update oa_data_mine set mainImage=%s"
        while True:
            try:
                job = redis.blpop('job_list')[1]
                job_info = job.split(',')
                job_id, pro_id = job_info
                raw_data = fetch__products(pro_id)
                cur.execute(code_sql, (job_id,))
                code_ret = cur.fetchone()
                code = code_ret[0]
                index = 1
                for row in parse_response(raw_data):
                    row['mid'] = job_id
                    row['parentId'] = code
                    row['childId'] = code + '_' + '0'*(2-len(str(index))) + str(index)
                    index += 1
                    cur.execute(main_image_sql, (row['mainImage']))
                    cur.execute(insert_sql,
                                (row['mid'], row['parentId'], row['proName'], row['description'],
                                row['tags'], row['childId'], row['color'], row['proSize'], row['quantity'],
                                float(row['price']), float(row['msrPrice']), row['shipping'], float(row['shippingWeight']),
                                row['shippingTime'],
                                row['varMainImage'], row['extra_image0'], row['extra_image1'], row['extra_image2'],
                                row['extra_image3'], row['extra_image4'], row['extra_image5'],
                                row['extra_image6'], row['extra_image7'], row['extra_image8'],
                                row['extra_image9'], row['extra_image10'], row['mainImage']))

                cur.execute(update_sql, (u'采集成功', job_id))
                con.commit()
            except Exception as why:
                try:
                    logger.error('%s while fetching %s' % (why, pro_id))
                    cur.execute(update_sql, (u'采集失败', job_id))
                    con.commit()
                except NameError as how:
                    logger.error('%s:not able to get job' % how)


if __name__ == "__main__":
    crawler()


