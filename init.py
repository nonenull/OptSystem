# coding=utf-8
import web
from model import Model
import json
from batch import Batch
import web.db

# 设置模板位置
render = web.template.render('templates/')
web.config.debug = True
web.webapi.internalerror = web.debugerror

# 构造URL
urls = (
    '/', 'INDEX',
    '/error', 'ERROR',
    '/admin/user', 'USER',
    '/admin/permissions','PERMISSIONS',
    '/login', 'LOGIN',
    '/login/auth', 'AUTH',
    '/login/logout', 'LOGOUT',
    '/dashboard', 'DASHBOARD',
    '/batch', 'BATCH',
    '/batch/search', 'SEARCH_SERVER',
    '/batch/executive', 'EXECUTIVE'
)
app = web.application(urls, globals())
application = app.wsgifunc()

# 兼容debug模式开启session
if web.config.get('_session') is None:
    session = web.session.Session(app, web.session.DiskStore('sessions'), {'count': 0})
    web.config._session = session
else:
    session = web.config._session

# 复用函数
class PUBLIC:
    # 根据用户权限获取子页面按钮
    def get_button(self,menu_id):
        check_button = ''
        if session.user_permissions:
            check_button = "and `menu_id` in %s" % (session.user_permissions)
        button = Model().select("select menu_title,menu_url from opt_menu where upper_menu='%s' and menu_level=0 %s" % (menu_id,check_button))
        return button

    # 获取菜单
    # ((a,b,(aa,bb)),(),())
    def get_menu(self,user_permissions):
        # 将数据改成('1','2','3','4','5')的格式，方便下面SQL in语句套用
        session.user_permissions = str(tuple(user_permissions.split(',')))
        menu_id = "and `menu_id` in %s" % (session.user_permissions)
        # 获取一级别菜单
        top_menu = Model().select("select menu_id,menu_title,menu_url,menu_icon from opt_menu where `menu_level`=1 %s order by sort" % (menu_id))
        # tuple转list
        top_menu = list(top_menu)
        # 循环获取二级菜单，并且组成三维数组
        for i in xrange(len(top_menu)):
            # 将tuple转换为list
            top_menu[i] = list(top_menu[i])
            second_menu = Model().select("select menu_id,menu_title,menu_url from opt_menu where `upper_menu`='%s' and menu_level !=0 %s order by sort" % (top_menu[i][0],menu_id))
            if second_menu:
                # 获取二级菜单，组成三维数组
                top_menu[i].append(list(second_menu))
                # print top_menu[i][-1]
                for a in xrange(len(top_menu[i][-1])):
                    third_menu = Model().select("select menu_id,menu_title,menu_url from opt_menu where `upper_menu`='%s' and menu_level =0 %s order by sort" % (top_menu[i][-1][a][0],menu_id))
                    if third_menu:
                        #tuple转list，不然无法append
                        top_menu[i][-1][a] = list(top_menu[i][-1][a])
                        top_menu[i][-1][a].append(third_menu)
        return top_menu

    #获取当前菜单的ID，方便后面做权限判断和获取按钮
    def check_permissions(self,menu_title):
        menu_id = Model().select("select menu_id from opt_menu where menu_title='%s'" % (menu_title))
        if menu_id[0][0] not in session.user_permissions:
            # 如果 menu_id 不在session保存的权限列表中，返回HTTP code 403
            raise web.webapi.HTTPError('403',{'Content-Type':'text/html; charset=utf-8'},'权限不足')
        return menu_id[0][0]

#错误页面
class ERROR:
    def GET(self):
        return render.error(error_messages='fuckyou')

# 首页
class INDEX:
    def GET(self):
        # 判断session是否存在user对象，如果没有，说明没有登录，跳转到login页面并且终止程序，不执行后面的代码
        if session.has_key("user") == False:
            raise web.seeother('/login')
        # 判断用户 role_id == 0 的情况下，默认拥有所有权限，加载所有菜单
        user_role_id = Model().select("select role_id from opt_user where username='%s'" % (session.user[0]))
        if user_role_id[0][0] == 0:
            user_permissions = Model().select("select GROUP_CONCAT(menu_id) from opt_menu order by sort")
        else:
            # 超级管理员之外的用户考虑配置实时生效，不存入session。每次加载首页，获取一次权限。这里判断role_id不等于0
            user_permissions = Model().select("select permissions from opt_role where id=%s" % (user_role_id[0][0]))
        if not user_permissions:
            raise web.webapi.HTTPError('403',{'Content-Type':'text/html; charset=utf-8'},'获取权限错误,请检查用户对应的角色')
        menu = PUBLIC().get_menu(user_permissions[0][0])
        # 将session信息和菜单信息赋值到模板
        return render.index(data=session.user, menu=menu)

# 用户管理页面
class USER:
    def GET(self):
        # 验证权限，成功返回菜单id
        menu_id = PUBLIC().check_permissions('用户管理')
        # 获取页面按钮
        button = PUBLIC().get_button(menu_id)
        user_data = Model().select("select id,username,full_name,position,mobile_phone,email,role_id,registered_time,update_time from opt_user")
        # print user_data
        return render.user(data=user_data,button=button)
    def POST(self):
        import re
        messages=''
        data = web.input()
         # 验证帐号，纯字母,3-20位
        if re.match('^[a-z]{3,20}',data.account) is None:
          messages += "帐号格式错误"
        if re.match('^[\u4e00-\u9fa5]{1,5}',data.full_name) is None:
          # 验证姓名，1-5个汉字
          messages += "姓名格式错误"
        if re.match('^[a-zA-Z][a-zA-Z0-9_!@#%^&]{4,15}',data.password) is None:
          # 验证密码，4-15位,字母开头，允许字母数字和"_!@#%^&"特殊字符
          messages += "密码格式错误"
        if data.password != data.repassword:
          # 密码确认
          messages += "密码不一致"
        if re.match("^[1][3578][0-9]{9}",data.phone) is None:
          # 验证手机
          messages += "手机格式错误"
        if re.match("^[\w!#$$%&'*+/=?^_`{|}~-]+(?:\.[\w!#$$%&'*+/=?^_`{|}~-]+)*@(?:[\w](?:[\w-]*[\w])?\.)+[\w](?:[\w-]*[\w])?",data.email) is None:
          #/验证邮箱
          messages += "邮箱格式错误"
        if re.match("^[\w!#$$%&'*+/=?^_`{|}~-]+(?:\.[\w!#$$%&'*+/=?^_`{|}~-]+)*@(?:[\w](?:[\w-]*[\w])?\.)+[\w](?:[\w-]*[\w])?",data.jurisdiction) is None:
          # 权限验证
          messages += "权限格式错误"
        else:
            # 未知输入框
            pass
        web.header('Content-Type','text/html; charset=utf-8', unique=True)
        return messages

# 权限管理页面
class PERMISSIONS:
    def GET(self):
        # 验证权限，成功返回菜单id
        menu_id = PUBLIC().check_permissions('权限管理')
        # 根据菜单id获取页面按钮
        button = PUBLIC().get_button(menu_id)
        user_data = Model().select("select id,role_name,permissions,update_time,comments from opt_role")
        # 获取需要配置的所有菜单id
        # all_menu_id = Model().select("select GROUP_CONCAT(menu_id) from opt_menu")
        # 组合成三围数组
        # menu = PUBLIC().get_menu(all_menu_id[0][0])
        print button
        return render.permissions(data=user_data,button=button)

    # 获取菜单列表
    def POST(self):
        data = web.input()
        menu_id = data.get('menu_id')
        print menu_id
        menu_data = PUBLIC().get_menu(str(menu_id))
        return json.dumps(menu_data)

# 登录页面
class LOGIN:
    def GET(self):
        return render.login(data="")

    def POST(self):
        post_data = web.input()
        user = post_data.get("user")
        password = post_data.get("password")
        remember = post_data.get("remember")
        if user and password:
            #获取用户信息: 帐号，全名，职位，注册时间
            data = Model().select("select username,full_name,position,registered_time from opt_user where username='%s' and password='%s'" % (user, password))
            # 如果检查到用户存在，保存信息到session，并且跳转至首页
            if data:
                #将用户信息存入session
                session.user = data[0]
                raise web.seeother('/')
        return render.login(data="帐号密码不正确")

# logout
class LOGOUT:
    def GET(self):
        session.kill()
        raise web.seeother('/login')

#仪表盘
class DASHBOARD:
    def GET(self):
        return render.dashboard()

# 批量执行页
class BATCH:
    def GET(self):
        data = Model().select("select id,hostname,ip,user,services,machine_room,description from opt_machine")
        # print data
        return render.batch(data)

# 搜索服务器
class SEARCH_SERVER:
    def POST(self):
        post_data = web.input()
        search_word = post_data.get('search_word')
        search_type = post_data.get('search_type')
        data = Model().select("select id,hostname,ip,user,services,machine_room,description from opt_machine where " + search_type + " like '%" + search_word + "%'")
        return json.dumps(data)

# 处理shell命令，采取队列多线程批量处理
class EXECUTIVE:
    def POST(self):
        #判断权限，防止恶意提交
        if "BA" not in session.user_permissions:
            web.header('Content-Type','text/html; charset=utf-8', unique=True)
            return "权限不够"
        post_data = web.input(**{'sid[]': []})
        shell_command = post_data.get('command')
        server_id = post_data.get('sid[]')
        # 交给Batch类处理
        result = Batch().do(server_id, shell_command)
        return result