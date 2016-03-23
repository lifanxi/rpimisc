#! /usr/bin/env python2.7

import aliyun.api
import json
import sys

def init_api():
    # Setup Aliyun API Access key
    conf = json.load(file('accesskey.json'))
    aliyun.setDefaultAppInfo(str(conf['id']),str(conf['secret']))

def check_domain_existence(domain):
    # Get domain list
    domains = aliyun.api.dns.DnsDescribeDomainsRequest().getResponse()
    found = False
    for d in domains['Domains']['Domain']:
        if d['DomainName'] == domain:
            found = True
    return found

def query_domain_record_id(record, domain):
    # Query domain record Id
    r = aliyun.api.dns.DnsDescribeDomainRecordsRequest()
    r.DomainName = domain
    records = r.getResponse()

    for r in records['DomainRecords']['Record']:
        if r['RR'] == record and r['Type'] == 'A':
            return r['RecordId']
    return None
    

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: ./query.py <record.domainName>")
        sys.exit(-1)
    domainsplits = sys.argv[1].rsplit('.')
    if len(domainsplits) < 2:
        print("Domain name shoule be in <record.domain.postfix> format, record can be empty")
        sys.exit(-1)
        
    domain = ".".join(domainsplits[-2:])
    record = ".".join(domainsplits[:-2])
    if len(record) == 0:
        record = '@'

    init_api()
    
    if not check_domain_existence(domain):
        print("Cannot find domain %s" % (domain));
        sys.exit(-1)

    id = query_domain_record_id(record, domain)
    if id:
        print("Record Id: %s" % (id))
    else:
        print("Record not found.")
