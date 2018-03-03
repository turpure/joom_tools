#! usr/bin/python
# coding:utf8

import logging


def log(name, path):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    console = logging.StreamHandler()
    console.setFormatter(formatter)

    fh = logging.FileHandler(path)
    fh.setFormatter(formatter)

    logger.addHandler(fh)
    return  logger