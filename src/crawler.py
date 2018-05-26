#! usr/bin/python
# coding:utf8

"""fetch products using request"""


import requests
from common.color import get_color_dict
from common.tools import BaseCrawler, MsSQL


color_dict = get_color_dict()
ms_sql = MsSQL()
con = ms_sql.connection()


class Crawler(BaseCrawler):

    data_base = MsSQL()

    def __int__(self):
        super(Crawler, self).__init__()

    @staticmethod
    def fetch(pro_id):
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
            variants['quantity'] = var['inventory']
            wanted_info = dict(main_info, **variants)
            yield wanted_info

    def run(self):
        while 1:
            task = self.redis.lpop('job_list', timeout=1800)
            job = task[1]
            job_info = job.split(',')
            job_id, pro_id = job_info
            raw_data = self.fetch(pro_id)
            rows = self.parse(raw_data)
            self.data_base.insert(rows, job_id)


if __name__ == "__main__":
    crawler = Crawler()
    crawler.run()


