import webapp2, utils, re, datetime
from google.appengine.ext import db
from google.appengine.api import memcache
import utils
from models import *

class AdminConsoleHandler(utils.DefaultHandler):
    @utils.isadmin
    def get(self):
        users = list(Users.all())
        vols = list(Volunteers.all())
        blocks = list(Blocks.all())
        jobs = list(Jobs.all().order('starttime'))
        events = list(Events.all())
        self.render('admin.html',users=users,volunteers=vols,blocks=blocks,jobs=jobs,events=events,user=self.user)
    
    @utils.isadmin
    def post(self):
        pass


class UserHandler(utils.DefaultHandler):
    @utils.isadmin
    def get(self,userid=None):
        if userid is None:
            self.redirect('/admin')
            return
        
        euser = Users.by_id(int(userid))
        self.render('user.html',user=self.user,euser=euser)
    
    @utils.isadmin
    def post(self,userid=None):
        if userid is None:
            self.redirect('/admin')
            return
        
        user_password = self.request.get('newpassword')
        user_confirm = self.request.get('confirm')
        
        euser = Users.by_id(int(userid))
        if self.request.get('readonly'):
            euser.readonly = True
        else:
            euser.readonly = False
        
        if self.request.get('active'):
            euser.active = True
        elif not (self.request.get('active') or euser.key() == self.user.key()):
            euser.active = False
            
        if self.request.get('volunteer'):
            euser.volunteer = True
        else:
            euser.volunteer = False
        
        
        if not utils.valid_verify(user_password, user_confirm):
            self.redirect('/admin/user/%s'%userid)
            return
        else:
            if user_password != '':
                euser.password = utils.make_pw_hash(euser.username, user_password)
        
        euser.put()
        self.redirect('/admin')

class VolunteerScheduleHandler(utils.DefaultHandler):
    @utils.isadmin
    def get(self,eventid):
        event = Events.by_id(eventid)
        #volunteers = list(Volunteers.all().order('name'))
        user_list = list(Users.all().order('username'))
        #jobs = EventJob.all().order('startTime')
        #jobblocks = [{'job':job,'blocks':list(Blocks.all().filter('jobid =',job.key().id()).order('starttime'))} for job in jobs]
        
        self.render('schedule.html',user=self.user,user_list=user_list,event=event)

class StartHandler(utils.DefaultHandler):
    #@utils.isadmin
    def get(self):
        pw = utils.make_pw_hash('volunteer@mods.mb.ca','v0lunt33r')
        u = Users(username='modsvoladmin',
                  password=pw,
                  email='volunteer@mods.mb.ca',
                  phone='204-555-1234',
                  readonly=False,
                  active=True,
                  volunteer=False)
        u.put()

class ClearVolunteers(utils.DefaultHandler):
    @utils.isadmin
    def get(self):
       blocks = Blocks.all().fetch(None)
       for b in blocks:
           b.volids = []
           b.put()
       
       memcache.flush_all() 
