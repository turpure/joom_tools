#! usr/bin/python
# coding:utf8

""" get products using token"""

from tools import MsSQL


connection = MsSQL()


def get_token(alias_name):
    """
    get token from table
    :return:string
    """
    sql = "select AccessToken from S_JoomSyncInfo where AliasName=%s"

    with connection as con:
        cur = con.cursor(as_dict=True)
        cur.execute(sql, (alias_name,))
        ret = cur.fetchone()
        if isinstance(ret, dict):
            return ret['AccessToken']


if __name__ ==  "__main__":
    print get_token('Joom01-YHBaby')
