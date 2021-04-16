api = "https://code.asam.net/"
private_token= "PEMYVMYj_zd4c4XxrDTo"
projectid=68

import gitlab

gl = gitlab.Gitlab(url=api, private_token=private_token, ssl_verify=True)
gl.auth()

# u = gl.users.create({
#                                 'email': 'engelben@protonmail.com',
#                                 'name': 'Test API',
#                                 'username': 'TNewMail',
#                                 'reset_password': True,
#                                 'password': 'Asam2020'
#                             })

p = gl.projects.get(68)
plist = p.members.list(all=True)
for u in plist:
    print("deleting {}".format(u.id))
    p.members.delete(u.id)