#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import os
import re
import sys
from datetime import datetime
import time

from aliyunsdkcore import client
from aliyunsdkalidns.request.v20150109 import DescribeDomainRecordsRequest
from aliyunsdkalidns.request.v20150109 import DescribeDomainRecordInfoRequest
from aliyunsdkalidns.request.v20150109 import UpdateDomainRecordRequest

# Setup Aliyun API Access key
conf = json.load(file('accesskey.json'))

# 阿里云 Access Key ID
access_key_id = str(conf['id'])
# 阿里云 Access Key Secret
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
    request.set_accept_format(rc_format)
    result = clt.do_action(request)
    result = json.JSONDecoder().decode(result)
    return result

"""
根据域名解析记录ID查询上一次的IP记录
"""
def get_old_ip(record_id):
    clt = client.AcsClient(access_key_id,access_key_secret,'cn-hangzhou')
    request = DescribeDomainRecordInfoRequest.DescribeDomainRecordInfoRequest()
    request.set_RecordId(record_id)
    request.set_accept_format(rc_format)
    result = clt.do_action(request)
    result = json.JSONDecoder().decode(result)
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
    get_ip_method = os.popen('curl -s https://freemindworld.com/tools/myip.php')
    get_ip_responses = get_ip_method.readlines()[0]
    get_ip_pattern = re.compile(r'\d+\.\d+\.\d+\.\d+')
    get_ip_value = get_ip_pattern.findall(get_ip_responses)
    return get_ip_value

def get_my_ip_internal():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("baidu.com",80))
    ip = s.getsockname()[0] 
    s.close()
    return ip

def get_cached_ip():
    try:
        conf = json.load(file('cache.json'))
        t = int(conf['ts'])
        ip = str(conf['ip'])
        now = int(time.time())
        print(now,t)
        if now - t < 30 * 60:
            return ip
        else:
            return None
    except Exception,e:
        print(e)
        return None

def update_cache(ip):
    try:
        value = {'ts': int(time.time()), 'ip': ip}
        f = file('cache.json', 'w')
        f.write(json.dumps(value))
        f.close()
    except Exception,e:
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
        print now_ip
        if now_ip == "internal":
            now_ip = get_my_ip_internal()
    else:
        now_ip = get_my_ip_public()[0]

    if get_cached_ip() == now_ip:
        print("No need to update. (Cached)")
        sys.exit(0)
        
    # # 之前的解析记录
    old_ip = ""
    record_id = ""
    dns_records = check_records(rc_domain)
    #print dns_records
    for record in dns_records["DomainRecords"]["Record"]:
        # print record["Type"] + "." + record["RR"]
        if record["Type"] == 'A' and record["RR"] == rc_record:
            record_id = record["RecordId"]
            print "%s.%s recordID is %s" % (rc_record,rc_domain,record_id)
            if record_id != "":
                old_ip = get_old_ip(record_id)
    # 获取主机当前的IP
    print "now host ip is %s, dns ip is %s" % (now_ip, old_ip)

    if old_ip == now_ip:
        update_cache(now_ip)
        print "No need to update. "
    else:
        rc_rr = rc_record           # 解析记录
        rc_type = 'A'               # 记录类型, DDNS填写A记录
        rc_value = now_ip           # 新的解析记录值
        rc_record_id = record_id    # 记录ID
        rc_ttl = '1000'             # 解析记录有效生存时间TTL,单位:秒

        print update_dns(rc_rr, rc_type, rc_value, rc_record_id, rc_ttl, rc_format)
        update_cache(now_ip)
