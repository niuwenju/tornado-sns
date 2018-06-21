# _*_ coding: utf-8 _*_
"""Simplified chat demo for websockets.
"""

import logging
import tornado.escape
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.websocket
from tornado import gen
import os.path
import os
import motor.motor_tornado
import time
import random, itertools
import md5
import uuid
import datetime
from tornado.options import define, options

define("port", default=8005, help="run on the given port", type=int)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/index", MainHandler,{},'index'),
            (r"/login", LoginHandler,{},'login'),
            (r"/signup", SignupHandler,{},'signup'),
            (r"/logout", LogoutHandler,{},'logout'),
            (r"/edit", EditHandler,{},'edit'),
            (r"/settings", SettingsHandler,{},'settings'),
            (r"/changepassword", ChangeHandler),
            (r"/friends", FriendsHandler,{},'friends'),
            (r"/friend_add/(?P<email>[a-zA-Z\-_\-.\-@\-%\d]+)", AddfriendsHandler,{},'friend_add'),
            (r"/friend_remove/(?P<email>[a-zA-Z\-_\-.\-@\-%\d]+)", RemovefriendsHandler,{},'friend_remove'),
            (r"/search_friends", SearchfriendsHandler),
            (r"/add_message", AddmessageHandler),
            # (r"/chatsocket/(?P<email>[a-zA-Z\-_\-.\-@\-%\d]+)", ChatHandler,{},'chatsocket'),
            (r"/", ChatHandler,{},'chatsocket'),
            (r"/chatsocket", ChatSocketHandler),
            # (r"/create_code_img", CreatecodeimgHandler),
            # (r"/chatsocket", ChatSocketHandler),
        ]
        settings = dict(
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            login_url="/login",
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            # template_loader=JinjaLoader(os.path.join(os.path.dirname(__file__), 'templates/')),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            # xsrf_cookies=True,
            debug = True,
            db=motor.motor_tornado.MotorClient().minisns
        )
        super(Application, self).__init__(handlers, **settings)


class BaseHandler(tornado.web.RequestHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")

    @property
    def db(self):
        # if not hasattr(self, '_db'):
        #     self._db = asyncmongo.Client(pool_id='mydb', host='127.0.0.1', port=27017, maxcached=10, maxconnections=50,
        #                                  dbname='test')
        # return self._db
        return self.application.settings['db']


class ChatbaseHandler(tornado.websocket.WebSocketHandler):
    def get_current_user(self):
        return self.get_secure_cookie("user")

    @property
    def db(self):
        # if not hasattr(self, '_db'):
        #     self._db = asyncmongo.Client(pool_id='mydb', host='127.0.0.1', port=27017, maxcached=10, maxconnections=50,
        #                                  dbname='test')
        # return self._db
        return self.application.settings['db']


class MainHandler(BaseHandler):
    @tornado.web.authenticated
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        user = self.current_user
        messages = []
        cursor = self.db.message.find().sort('-addtime')
        for document in (yield cursor.to_list(length=100)):
            messages.append(document)
        # self.render("index.html", messages=ChatSocketHandler.cache, clients=ChatSocketHandler.waiters, username= "游客%d" % ChatSocketHandler.client_id)
        self.render("index.html", user=user, messages=messages)


# class CreatecodeimgHandler
# def create_code_img(request):
#     f = io.BytesIO()  # 直接在内存开辟一点空间存放临时生成的图片
#     img, code = check_code.create_validate_code()  # 调用check_code生成照片和验证码
#     request.session['check_code'] = code  # 将验证码存在服务器的session中，用于校验
#     img.save(f, 'PNG')  # 生成的图片放置于开辟的内存中
#     return HttpResponse(f.getvalue())


class LoginHandler(BaseHandler):
    def get(self):
        # try:
        #     email = self.get_argument('email')
        #     user = yield self.db.user.find_one({'email': email})
        # except:
        #     user = None
        self.render("signin.html", error = '' )

    @tornado.web.asynchronous
    @gen.coroutine
    def post(self):
        try:
            email = self.get_argument('email')
            password = md5.new(self.get_argument('password')).hexdigest()
        except(KeyError):
            pass
        if not email:
            self.render("signin.html", error='邮箱输入有误')
        else:
            try:
                user = yield self.db.user.find_one({'email': email})
            except:
                pass
            if not user:
                self.render("signin.html", error='用户不存在')
            else:
                if password == user['password']:
                    self.set_secure_cookie("user", self.get_argument("email"))
                    self.redirect('/index')
                else:
                    self.render("signin.html", error = u'密码错误')


class SignupHandler(BaseHandler):
    def get(self):
        self.render("signup.html",error='')

    @tornado.web.asynchronous
    @gen.coroutine
    def post(self):
        try:
            email = self.get_argument('email', None)
            password = self.get_argument('password', None)
            confirm = self.get_argument('confirm', None)
        except(KeyError):
            pass
        if not email or not password or not confirm:
            self.render("signup.html", error=u'请填入有效信息')
        else:
            _verify_email = yield self.db.user.find_one({'email': email})
            if _verify_email:
                self.render("signup.html", error = u'邮箱已注册')
            else:
                if password != confirm:
                    self.render("signup.html", error=u'密码不一致')
                else:
        # if captcha and captcha == self.get_secure_cookie('captcha').replace(' ', ''):
        #     self.flash(u'验证码输入正确', 'info')
        # else:
        #     self.flash(u'验证码输入错误', 'error')
        #     self.redirect('/auth/register')
                    password = md5.new(password).hexdigest()
                    a = map("".join, list(itertools.product("abcdefghijklmnopqrstuvwxyz", repeat=5)))
                    username = a[random.randint(0, 26 ** 5 - 1)]
                    data = {
                        'username': username,
                        'email': email,
                        'password': password,
                        'sex': 'm',
                        # 'face':''
                        'timestamp': time.time() * 1000,
                        'friends':[],
                    }

                    if email:
                        yield self.db.user.insert(data)
                    self.set_secure_cookie('user', email)
                    self.redirect('/index')

class LogoutHandler(BaseHandler):
    def get(self):
        self.clear_cookie("user")
        self.redirect("/login")


class EditHandler(BaseHandler):
    def get(self):
        user = self.current_user
        self.render('edit.html', user = user)


class SettingsHandler(BaseHandler):
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        user = self.current_user
        _user = yield self.db.user.find_one({'email': user})
        self.render('settings.html', user=user, current = _user, error='')

    @tornado.web.asynchronous
    @gen.coroutine
    def post(self):
        try:
            username = self.get_argument('username')
            sex = self.get_argument('sex')
            # email = self.get_argument('email')
        except(KeyError):
            pass
        try:
            _user = yield self.db.user.find_one({'email': self.current_user})
        except:
            pass
        if not _user:
            self.render("changepassword.html", error='用户不存在')
        else:
            yield self.db.user.update_one({'email': self.current_user}, {'$set': {'username': username,'sex':sex}})
            self.redirect("/edit")


class ChangeHandler(BaseHandler):
    def get(self):
        user = self.current_user
        self.render('changepassword.html',user = user, error = '')

    @tornado.web.asynchronous
    @gen.coroutine
    def post(self):
        try:
            newpassword = self.get_argument('newpassword')
            confirm = self.get_argument('confirm')


        except(KeyError):
            pass
        if not newpassword or not confirm:
            self.render("changepassword.html", error='输入有误')
        else:
            try:
                _user = yield self.db.user.find_one({'email': self.current_user})
            except:
                pass
            if not _user:
                self.render("changepassword.html", error='用户不存在')
            else:
                if newpassword == confirm:
                    password = md5.new(newpassword).hexdigest()
                    yield self.db.user.update_one({'email': self.current_user}, {'$set': {'password': password}})
                    self.redirect('/edit')
                else:
                    self.render("changepassword.html", error=u'密码不一致')


class FriendsHandler(BaseHandler):
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        user = self.current_user
        _user = yield self.db.user.find_one({'email': self.current_user})
        friends = []
        for friend in _user['friends']:
            cur = yield self.db.user.find_one({'_id': friend})
            friends.append({'username':cur['username'], 'email':cur['email']})
        self.render('users_list.html', user=user, friends = friends)


class RemovefriendsHandler(BaseHandler):
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self,email):
        user = self.current_user
        # email.replace("%40", "@")
        friend = yield self.db.user.find_one({'email': email})
        yield self.db.user.update_one({'email': self.current_user}, {"$pull": {"friends": friend['_id']}})
        self.redirect("/friends")
        # friends = yield self.db.user.find_one({'email': self.current_user})
        # self.render('users_list.html', user=user, friends=friends['friends'])

class AddfriendsHandler(BaseHandler):
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self, email):
        user = self.current_user
        # email.replace("%40", "@")
        friend = yield self.db.user.find_one({'email':email})
        yield self.db.user.update_one({'email': user}, {"$addToSet": {"friends": friend['_id']}})
        self.redirect("/friends")
        # friends = yield self.db.user.find({'email': self.current_user})
        # self.render('users_list.html', user=user, friends=friends)

class SearchfriendsHandler(BaseHandler):
    @tornado.web.asynchronous
    @gen.coroutine
    def post(self):
        user = self.current_user
        try:
            username = self.get_argument('search')
        except:
            pass
        if username:
            friends = []
            cursor = self.db.user.find({'username': username},{'username':1, 'email':1})
            for friend in (yield cursor.to_list(length=100)):
                friends.append(friend)
            # friends = yield self.db.user.find_one({'username': username},{'username':1})
            self.render('friend_list.html', user=user, friends=friends)
        else:
            self.redirect("/friends")


class AddmessageHandler(BaseHandler):
    @tornado.web.asynchronous
    @gen.coroutine
    def post(self):
        user = self.current_user
        try:
            message = self.get_argument('message')
        except:
            pass
        if message:
            _user = yield self.db.user.find_one({'email': user})
            data = {
                'message': message,
                'addtime': time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
                'author': _user['username'],

            }
            yield self.db.message.insert(data)
            self.redirect("/index")
        else:
            self.redirect("/index")


"""团战聊天"""

class ChatHandler(BaseHandler):
    @tornado.web.asynchronous
    @gen.coroutine
    def get(self):
        user = self.current_user
        _user = yield self.db.user.find_one({'email':user})
        username = _user['username']
        self.render("chatindex.html", messages=ChatSocketHandler.cache, clients=ChatSocketHandler.waiters,
                    username=username,user=user)

#
#
# class MainHandler(tornado.web.RequestHandler):
#     def get(self):
#         self.render("index.html", messages=ChatSocketHandler.cache, clients=ChatSocketHandler.waiters, username= "游客%d" % ChatSocketHandler.client_id)


class ChatSocketHandler(ChatbaseHandler):
    waiters = set()
    cache = []
    cache_size = 200
    client_id = 0

    def get_compression_options(self):
        # Non-None enables compression with default options.
        return {}

    @tornado.web.asynchronous
    @gen.coroutine
    def open(self):
        user = self.current_user
        _user = yield self.db.user.find_one({'email': user})
        self.client_id = ChatSocketHandler.client_id
        ChatSocketHandler.client_id = ChatSocketHandler.client_id + 1
        self.username = _user['username']
        ChatSocketHandler.waiters.add(self)

        chat = {
            "id": str(uuid.uuid4()),
            "type": "online",
            "client_id": self.client_id,
            "username": self.username,
            "datetime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            }
        ChatSocketHandler.send_updates(chat)

    def on_close(self):
        ChatSocketHandler.waiters.remove(self)
        chat = {
            "id": str(uuid.uuid4()),
            "type": "offline",
            "client_id": self.client_id,
            "username": self.username,
            "datetime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            }
        ChatSocketHandler.send_updates(chat)


    @classmethod
    def update_cache(cls, chat):
        cls.cache.append(chat)
        if len(cls.cache) > cls.cache_size:
            cls.cache = cls.cache[-cls.cache_size:]

    @classmethod
    def send_updates(cls, chat):
        logging.info("sending message to %d waiters", len(cls.waiters))
        for waiter in cls.waiters:
            try:
                waiter.write_message(chat)
            except:
                logging.error("Error sending message", exc_info=True)

    def on_message(self, message):
        logging.info("got message %r", message)
        parsed = tornado.escape.json_decode(message)
        self.username = parsed["username"]
        chat = {
            "id": str(uuid.uuid4()),
            "body": parsed["body"],
            "type": "message",
            "client_id": self.client_id,
            "username": self.username,
            "datetime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            }
        chat["html"] = tornado.escape.to_basestring(
            self.render_string("message.html", message=chat))

        ChatSocketHandler.update_cache(chat)
        ChatSocketHandler.send_updates(chat)


"""1对1聊天待开发"""
# class ChatSocketHandler(tornado.websocket.WebSocketHandler):
#     waiters = set()
#     cache = []
#     cache_size = 200
#     client_id = 0
#
#     def get_compression_options(self):
#         # Non-None enables compression with default options.
#         return {}
#
#     def open(self):
#         self.client_id = ChatSocketHandler.client_id
#         ChatSocketHandler.client_id = ChatSocketHandler.client_id + 1
#         self.username = "游客%d" % self.client_id
#         ChatSocketHandler.waiters.add(self)
#
#         chat = {
#             "id": str(uuid.uuid4()),
#             "type": "online",
#             "client_id": self.client_id,
#             "username": self.username,
#             "datetime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
#             }
#         ChatSocketHandler.send_updates(chat)
#
#     def on_close(self):
#         ChatSocketHandler.waiters.remove(self)
#         chat = {
#             "id": str(uuid.uuid4()),
#             "type": "offline",
#             "client_id": self.client_id,
#             "username": self.username,
#             "datetime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#             }
#         ChatSocketHandler.send_updates(chat)
#
#
#     @classmethod
#     def update_cache(cls, chat):
#         cls.cache.append(chat)
#         if len(cls.cache) > cls.cache_size:
#             cls.cache = cls.cache[-cls.cache_size:]
#
#     @classmethod
#     def send_updates(cls, chat):
#         logging.info("sending message to %d waiters", len(cls.waiters))
#         for waiter in cls.waiters:
#             try:
#                 waiter.write_message(chat)
#             except:
#                 logging.error("Error sending message", exc_info=True)
#
#     def on_message(self, message):
#         logging.info("got message %r", message)
#         parsed = tornado.escape.json_decode(message)
#         self.username = parsed["username"]
#         chat = {
#             "id": str(uuid.uuid4()),
#             "body": parsed["body"],
#             "type": "message",
#             "client_id": self.client_id,
#             "username": self.username,
#             "datetime": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#             }
#         chat["html"] = tornado.escape.to_basestring(
#             self.render_string("message.html", message=chat))
#
#         ChatSocketHandler.update_cache(chat)
#         ChatSocketHandler.send_updates(chat)

def main():
    tornado.options.parse_command_line()
    app = Application()
    app.listen(options.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
