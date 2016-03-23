#! /usr/bin/env python2.7

import aliyun.api
import json
import sys
import urllib2
import time

def init_api():
    # Setup Aliyun API Access key
    conf = json.load(file('accesskey.json'))
    aliyun.setDefaultAppInfo(str(conf['id']),str(conf['secret']))

def get_domain_record(record):
    # Query domain record Id
    r = aliyun.api.dns.DnsDescribeDomainRecordInfoRequest()
    r.RecordId = record
    try:
        response = r.getResponse()
        return response['Value']
    except Exception, e:
        print("get_domain_record:", e)
        return None
    
def get_my_ip_internal():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("baidu.com",80))
    ip = s.getsockname()[0] 
    s.close()
    return ip

def get_my_ip():
    try:
        u = urllib2.urlopen('https://www.freemindworld.com/tools/myip.php')
        return u.read().strip('\n')
    except HTTPError as e:
        print('getMyIp:',e)
        return None

def update_domain_record_id(record_id, ip, record):
    r = aliyun.api.dns.DnsUpdateDomainRecordRequest()
    r.RecordId = record_id
    r.RR = record
    r.Type = "A"
    r.Value = ip
    try:
        response = r.getResponse()
        if 'Code' in response:
            print("get_domain_record:", response)
            return False
        else:
            return True
    except Exception, e:
        print("get_domain_record:", e)
        return False
        
    return True

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
        print("Usage: ./update.py <Record Id> <record> <IP>")
        sys.exit(-1)
    record_id = sys.argv[1]
    record = sys.argv[2]

    if len(sys.argv) == 4:
        ip = sys.argv[3]
        if ip == "internal":
            ip = get_my_ip_internal()
    else:
        ip = get_my_ip()

    if get_cached_ip() == ip:
        print("No need to update. (Cached)")
        sys.exit(0)
        
    init_api()
    
    if get_domain_record(record_id) == ip:
        update_cache(ip)
        print("No need to update")
        sys.exit(0)

    if update_domain_record_id(record_id, ip, record):
        update_cache(ip)
        print("Success")
        sys.exit(0)
    else:
        print("Failed")
        sys.exit(-1)

