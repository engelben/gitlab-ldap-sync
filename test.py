import gitlab
import sys
import json
import ldap
import ldap.asyncsearch
import logging

users_base_dn = 'ou=users,dc=195,dc=201,dc=116,dc=53'

l = ldap.initialize(uri='ldap://ldap.asam.net')
l.simple_bind_s('cn=admin,dc=195,dc=201,dc=116,dc=53', 'Mq7EzX4CZ9aCteJw')


u = gl.users.create({
                                'email': l_member['email'],
                                'name': l_member['name'],
                                'username': l_member['username'],
                                'extern_uid': l_member['identities'],
                                'provider': config['gitlab']['ldap_provider'],
                                'force_random_password': True
                            })


