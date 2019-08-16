#! usr/bin/python
# coding:utf8

"""fetch products using request"""


import requests
import time
from common.color import get_color_dict
from common.tools import BaseCrawler, MsSQL, MySQL
import pymysql

color_dict = get_color_dict()
ms_sql = MsSQL()
my_sql = MySQL()
con = ms_sql.connection()


class Crawler(BaseCrawler):

    def __init__(self, db_type='mssql'):
        if db_type == 'mssql':
            self.data_base = MsSQL()
        else:
            self.data_base = MySQL()

        super(Crawler, self).__init__()

    def get_token(self):
        sql = 'select  token, bearerToken from urTools.sys_joom_token limit 1'
        con = self.data_base.connection()
        cur = con.cursor(pymysql.cursors.DictCursor)
        cur.execute(sql)
        ret = cur.fetchone()
        if ret:
            return ret
        return None

    def fetch(self, pro_id):
        if not pro_id:
            raise Exception('Invalid pro ID', pro_id)
        api = 'https://api.joom.com/1.1/products/{}?currency=USD&language=en-US'

        base_url = api.format(pro_id)
        token = self.get_token()
        api_token = token['token']
        bearer_token = token['bearerToken']
        headers = {
            'authorization': bearer_token,
            'user-agent': ('Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                           'AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/64.0.3282.186 Safari/537.36'),
            'referer': "https://www.joom.com",
            'origin': "https://www.joom.com",
            'Host': "api.joom.com",
            'User-Agent': ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/"
                           "537.36 (KHTML, like Gecko) Chrome/67.0.3396.79 Safari/537.36"),
            'Cache-Control': "no-cache",
            'x-version': "0.1.9",
            'x-ostype ': 'Windows',
            'x-api-token': api_token
        }
        session = requests.Session()
        r = session.get(base_url, headers=headers, verify=False)
        return r.json()

    @staticmethod
    def parse(data):
        wanted_info = dict()
        main_info = dict()
        if data is None:
            yield wanted_info
            return

        pro_info = data['payload']
        try:
            tags_info = pro_info['nameExt']['tags']
            tags = ','.join([name['nameEng'] for name in tags_info])
        except:
            tags = ''
        main_info['tags'] = tags
        extra_images = pro_info.get('gallery', '')
        main_info['proId'] = pro_info.get('id', '')
        main_info['description'] = pro_info.get('engDescription', '')
        main_info['proName'] = pro_info.get('engName', '')
        main_info['categoryId'] = pro_info.get('categoryId', '')
        main_info['mainImage'] = pro_info['lite']['mainImage']['images'][-1]['url']
        for image in extra_images:
            main_info['extra_image' + str(extra_images.index(image))] = image['payload']['images'][-1]['url']
        for i in range(0, 11 - len(extra_images)):
            main_info['extra_image' + str(11 - i - 1)] = ''
        pro_variants = pro_info.get('variants', '')

        for var in pro_variants:
            variants = dict()
            try:
                try:
                    variants['color'] = color_dict['#' + var['colors'][0]['rgb']]
                except:
                    variants['color'] = var['colors'][0]['rgb']
            except:
                variants['color'] = ''
            variants['proSize'] = var.get('size', '')
            variants['msrPrice'] = var.get('msrPrice', 0)
            variants['shipping'] = var['shipping']['price']
            variants['shippingTime'] = '-'.join([str(var['shipping']['minDays']), str(var['shipping']['maxDays'])])
            variants['price'] = var['price']
            variants['shippingWeight'] = var.get('shippingWeight', 0)
            try:
                variants['varMainImage'] = var['mainImage']['images'][-1]['url']
            except:
                variants['varMainImage'] = ''
            # variants['quantity'] = var['inventory']
            variants['quantity'] = 100000
            wanted_info = dict(main_info, **variants)
            yield wanted_info

    def get_task(self, queue_name, block=True):
        if block:
            task = self.redis.blpop(queue_name, timeout=10)
            task = task[1]
        else:
            task = self.redis.lpop(queue_name)
            if not task:
                time.sleep(1)
        return task

    def run(self):
        while 1:
            try:
                job = self.get_task('job_list', block=True)
                if job:
                    job_info = job.split(',')
                    job_id, pro_id = job_info
                    raw_data = self.fetch(pro_id)
                    rows = self.parse(raw_data)
                    self.data_base.insert(rows, job_id)
            except Exception as why:
                pass


if __name__ == "__main__":
    crawler = Crawler('mysql')
    pro = '5bfe498e36b54d01016765f3'
    print crawler.fetch(pro)


