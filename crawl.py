#! usr/bin/python
# coding:utf8

from src import crawler

worker = crawler.Crawler('mysql')
worker.run()

