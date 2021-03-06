#! /usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import re
import sys
import time
from datetime import datetime

import urllib.request

from aliyunsdkalidns.request.v20150109 import (DescribeDomainRecordInfoRequest,
                                               DescribeDomainRecordsRequest,
                                               UpdateDomainRecordRequest)
from aliyunsdkcore import client

# Setup Aliyun API Access key
with open('accesskey.json') as json_file:
    conf = json.load(json_file)

# 阿里云 Access Key ID
access_key_id = str(conf['id'])
# 阿里云 Access Key Secretp
access_key_secret = str(conf['secret'])
# 返回内容格式
rc_format = 'json'

"""
获取域名的解析信息
"""


def check_records(dns_domain):
    clt = client.AcsClient(access_key_id, access_key_secret, 'cn-hangzhou')
    request = DescribeDomainRecordsRequest.DescribeDomainRecordsRequest()
    request.set_DomainName(dns_domain)
    request.set_PageSize(50)
    request.set_accept_format(rc_format)
    result = clt.do_action(request)
    result = json.loads(result.decode('utf-8'))
    return result


"""
根据域名解析记录ID查询上一次的IP记录
"""


def get_old_ip(record_id):
    clt = client.AcsClient(access_key_id, access_key_secret, 'cn-hangzhou')
    request = DescribeDomainRecordInfoRequest.DescribeDomainRecordInfoRequest()
    request.set_RecordId(record_id)
    request.set_accept_format(rc_format)
    result = clt.do_action(request)
    result = json.loads(result.decode('utf-8'))
    result = result['Value']
    return result


"""
更新阿里云域名解析记录信息
"""


def update_dns(dns_rr, dns_type, dns_value, dns_record_id, dns_ttl, dns_format):
    clt = client.AcsClient(access_key_id, access_key_secret, 'cn-hangzhou')
    request = UpdateDomainRecordRequest.UpdateDomainRecordRequest()
    request.set_RR(dns_rr)
    request.set_Type(dns_type)
    request.set_Value(dns_value)
    request.set_RecordId(dns_record_id)
    request.set_TTL(dns_ttl)
    request.set_accept_format(dns_format)
    result = clt.do_action(request)
    return result


"""
通过 ip.cn 获取当前主机的外网IP
"""


def get_my_ip_public():
    try:
        u = urllib.request.urlopen('https://freemindworld.com/tools/myip.php')
        return u.read().decode('utf-8').strip('\n')
    except Exception as e:
        print('getMyIp:', e)
        return None


def get_my_ip_internal():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("baidu.com", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


def get_cached_ip():
    try:
        with open('cache.json', 'r') as cache_file:
            conf = json.load(cache_file)
            t = int(conf['ts'])
            ip = str(conf['ip'])
            now = int(time.time())
            print(now, t)
            if now - t < 30 * 60:
                return ip
            else:
                return None
    except Exception as e:
        print(e)
        return None


def update_cache(ip):
    try:
        value = {'ts': int(time.time()), 'ip': ip}
        f = open('cache.json', 'w')
        f.write(json.dumps(value))
        f.close()
    except Exception as e:
        print(e)
        pass


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: ./update.py <top domain> <record> <IP>")
        sys.exit(-1)

    rc_domain = sys.argv[1]
    rc_record = sys.argv[2]

    if len(sys.argv) == 4:
        now_ip = sys.argv[3]
        print(now_ip)
        if now_ip == "internal":
            now_ip = get_my_ip_internal()
    else:
        now_ip = get_my_ip_public()

    if get_cached_ip() == now_ip:
        print("No need to update. (Cached)")
        sys.exit(0)

    # # 之前的解析记录
    old_ip = ""
    record_id = ""
    dns_records = check_records(rc_domain)
    # print dns_records
    for record in dns_records["DomainRecords"]["Record"]:
        # print record["Type"] + "." + record["RR"]
        if record["Type"] == 'A' and record["RR"] == rc_record:
            record_id = record["RecordId"]
            print("%s.%s recordID is %s" % (rc_record, rc_domain, record_id))
            if record_id != "":
                old_ip = get_old_ip(record_id)
    # 获取主机当前的IP
    print("now host ip is %s, dns ip is %s" % (now_ip, old_ip))

    if old_ip == now_ip:
        update_cache(now_ip)
        print("No need to update. ")
    else:
        print(rc_record, now_ip, record_id)
        rc_rr = rc_record           # 解析记录
        rc_type = 'A'               # 记录类型, DDNS填写A记录
        rc_value = now_ip           # 新的解析记录值
        rc_record_id = record_id    # 记录ID
        rc_ttl = '600'             # 解析记录有效生存时间TTL,单位:秒

        print(update_dns(rc_rr, rc_type, rc_value,
                         rc_record_id, rc_ttl, rc_format))
        update_cache(now_ip)
