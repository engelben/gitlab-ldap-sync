#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import gitlab
import sys
import json
import ldap
import ldap.asyncsearch
import logging

import pandas as pd
import numpy as np

if __name__ == "__main__":
    print('Initializing gitlab-ldap-sync.')
    config = None
    with open('config.json') as f:
        config = json.load(f)
    if config is not None:
        print('Done.')
        print('Updating logger configuration')
        if not config['gitlab']['group_visibility']:
            config['gitlab']['group_visibility'] = 'private'
        log_option = {
            'format': '[%(asctime)s] [%(levelname)s] %(message)s'
        }
        if config['log']:
            log_option['filename'] = config['log']
        if config['log_level']:
            log_option['level'] = getattr(logging, str(config['log_level']).upper())
        logging.basicConfig(**log_option)
        print('Done.')
        logging.info('Connecting to GitLab')
        if config['gitlab']['api']:
            gl = None
            if not config['gitlab']['private_token'] and not config['gitlab']['oauth_token']:
                logging.error('You should set at least one auth information in config.json, aborting.')
            elif config['gitlab']['private_token'] and config['gitlab']['oauth_token']:
                logging.error('You should set at most one auth information in config.json, aborting.')
            else:
                if config['gitlab']['private_token']:
                    gl = gitlab.Gitlab(url=config['gitlab']['api'], private_token=config['gitlab']['private_token'], ssl_verify=config['gitlab']['ssl_verify'])
                elif config['gitlab']['oauth_token']:
                    gl = gitlab.Gitlab(url=config['gitlab']['api'], oauth_token=config['gitlab']['oauth_token'], ssl_verify=config['gitlab']['ssl_verify'])
                else:
                    gl = None
                if gl is None:
                    logging.error('Cannot create gitlab object, aborting.')
                    sys.exit(1)
            gl.auth()
            logging.info('Done.')

            logging.info('Connecting to LDAP')
            if not config['ldap']['url']:
                logging.error('You should configure LDAP in config.json')
                sys.exit(1)

            try:
                l = ldap.initialize(uri=config['ldap']['url'])
                l.simple_bind_s(config['ldap']['bind_dn'], config['ldap']['password'])
            except:
                logging.error('Error while connecting')
                sys.exit(1)

            logging.info('Done.')


            logging.info('Getting all groups from LDAP.')
            ldap_groups = []
            ldap_groups_names = []
            if not config['ldap']['group_attribute'] and not config['ldap']['group_prefix']:
                filterstr = '(objectClass=group)'
            else:
                if config['ldap']['group_attribute'] and config['ldap']['group_prefix']:
                    logging.error('You should set "group_attribute" or "group_prefix" but not both in config.json')
                    sys.exit(1)
                else:
                    if config['ldap']['group_attribute']:
                        filterstr = '(&(objectClass=group)(%s=gitlab_sync))' % config['ldap']['group_attribute']
                    if config['ldap']['group_prefix']:
                        filterstr = '(&(objectClass=group)(cn=%s*))' % config['ldap']['group_prefix']
            attrlist=['name', 'member']

            memberlist = []
            for group_dn, group_data in l.search_s(base=config['ldap']['groups_base_dn'],
                                                   scope=ldap.SCOPE_SUBTREE):
                if 'member' in group_data:
                    for member in group_data['member']:
                        member = member.decode()
                        for user_dn, user_data in l.search_s(member,
                                                             scope=ldap.SCOPE_BASE,
                                                             filterstr='(objectClass=inetOrgPerson)',
                                                             attrlist=['uid', 'givenName', 'sn']):
                            firstName = user_data['givenName'][0].decode()
                            lastName = user_data['sn'][0].decode()
                            memberlist.append({
                                'username': firstName[0]+lastName,
                                'name': firstName+" "+lastName,
                                'identities': str(member).lower(),
                                'email': user_data['uid'][0].decode()
                            })
            logging.info('Done.')

            logging.info('|- Working on group\'s members.')
            mapping = []
            for l_member in memberlist:
                u = gl.users.list(search=l_member['email'])
                if len(u) > 0:
                    u = u[0]
                    mapping.append([l_member['email'],u.username])
        df = pd.DataFrame(mapping)
        s = df.to_csv(index=False)
        s = s.replace(",", ": ").replace("\n\n", "\n")
        with open("user_mappings.yml", "w") as f:
            f.writelines(s)