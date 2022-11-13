import webapp2, utils, re, datetime
from google.appengine.ext import db
from google.appengine.api import memcache
import utils
from models import *


class SignupHandler(utils.DefaultHandler):
    def render_front(username="",email="",unerr="",passerr="",vererr="",emerr=""):
        self.render("admin.html",username=username,emamil=email,unerr=unerr,passerr=passerr,vererr=vererr,emerr=emerr)
    
    def get(self):
        self.render("signup.html")
    
    def post(self):
#        if not self.user:
#            self.redirect('/admin')
#            return
#        
#        if self.user.readonly == True:
#            self.redirect('/admin')
#            return
        
        user_uname = self.request.get('username')
        user_password = self.request.get('password')
        user_verify = self.request.get('verify')
        user_email = self.request.get('email')
        user_phone = self.request.get('phone')
        
        formdict = {}
        validation = True
        formdict['username'] = user_uname
        formdict['email'] = user_email
        
#        if not utils.valid_username(user_uname):
#            formdict['unerr'] = "That's not a valid username."
#            validation = False
        if Users.by_email(user_email):
            formdict['unerr'] = "User with that E-mail already exists."
            validation = False
        if not utils.valid_password(user_password):
            formdict['passerr'] = "That's not a valid password."
            validation = False
        if not utils.valid_verify(user_password, user_verify):
            formdict['vererr'] = "Your passwords don't match."
            validation = False
        if not utils.valid_email(user_email):
            formdict['emerr'] = "That's not a valid email."
            validation = False
        else:
            formdict['email'] = user_email
            #if not user_email:
            #	user_email = None
        
        if validation:
            u = Users.register(name=user_uname,pw=user_password,email=user_email,phone=user_phone)
            u.put()
            #if self.request.get('login'):
            self.login(u)
            self.redirect('/')
        else:
            #self.redirect('/admin', showform=True, **formdict)
            users = list(Users.all())
            vols = list(Volunteers.all())
            blocks = list(Blocks.all())
            jobs = list(Jobs.all())
            events = list(Events.all())
            self.render('signup.html', **formdict)
        

class LoginHandler(utils.DefaultHandler):
    def get(self):
        if self.user:
            self.redirect('/')
        else:
            page = memcache.get('page:login.html')
            if not page:
                page = self.render_str("login.html",username="")
                memcache.add('page:login.html',page)
            
            #self.render_str("login.html",username="")
            self.write(page)
    
    def post(self):
        email = self.request.get('email')
        password = self.request.get('password')
        redirecturl = self.request.get('redirecturl')
        print redirecturl
        
        user = Users.login(email, password)
        if user:
            self.login(user)
            
            if redirecturl is None or redirecturl == '':
                self.redirect('/')
            else:
                self.redirect(redirecturl)
        else:
            msg = "Invalid Login."
            self.render("login.html",error=msg,email=email, redirecturl=redirecturl)

class LogoutHandler(utils.DefaultHandler):
    def get(self):
        self.logout()
        self.redirect('/')

