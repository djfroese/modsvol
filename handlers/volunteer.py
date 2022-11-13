import webapp2, utils, re, datetime
from google.appengine.ext import db
from google.appengine.api import memcache
from models import *
import utils

class RegistrationHandler(utils.DefaultHandler):

    def get(self, eventid):

        if not self.user:
            self.render('login.html',redirecturl=self.request.path)
            return

        event = Events.by_id(int(eventid))

        #jobs = list(EventJob.all().filter("eventKey=",event.key().id()).order('startTime'))
        jobs = event.jobs('startTime')

        page = {'title':'Register for %s'%event.eventname}

        #jobblocks = [{'job':job,'blocks':list(Blocks.all().filter('jobid =',job.key().id()).order('startTime'))} for job in jobs]

        self.render('registerform.html',page=page,event=event,user=self.user,errors=None)

    @utils.loggedin
    def post(self, eventid):
        jobs = self.request.get_all('jobs')
        jobs = [long(x) for x in jobs]

        blocks = [Blocks.by_id(long(x)) for x in self.request.get_all('blocks')]

        valid = True

        errors = {}
        # Need to handle event in the future
        fields = {'blocks':blocks}

        phoneRE = r'[0-9][0-9][0-9].[0-9][0-9][0-9].[0-9][0-9][0-9][0-9]'


        if self.user:
            #if self.user.email == email and vol.phone == phone and vol.name == name:
            current_blocks = self.user.blocks() + blocks

            # remove_blocks = [x for x in current_blocks if x.key().id() not in [y.key().id() for y in blocks]]

            #all_blocks = blocks
            #print all_blocks
            if not utils.valid_blocks(current_blocks):
                errors['blockerr'] = True
                valid = False
                print "Block Conflict with already registered blocks"



        if valid:
            for block in blocks:
                if block.addVolunteer(self.user.key().id()):
                    block.put()
                    memcache.delete('AllBlocks', seconds=2)
                    memcache.delete('%s:Blocks:%s'%(block.eventJobid, "None"),seconds=2)
                    #memcache.delete('%s:Blocks:%s'%(block.eventJobid, "startTime"),seconds=2)
                    memcache.delete('%s:Blocks:%s'%(block.eventJobid, "starttime"),seconds=2)
                    memcache.delete('%s:Blocks'%block.eventJobid, seconds=2)
                    memcache.delete('%s:EventJobs'%(eventid),seconds=2)

            # for unblock in remove_blocks:
            #     if unblock.removeVolunteer(self.user.key().id()):
            #       print "REMOVED VOLUNTEER FROM BLOCK."
            #       unblock.put()
            #       memcache.delete('%s:Blocks:%s'%(unblock.eventJobid,'starttime'))
            #       memcache.delete('%s:Blocks:%s'%(unblock.eventJobid,None))

            self.redirect('/user/schedule')

        else:
            print "Error - One or more inputs are invalid"
            event = Events.by_id(int(eventid))
            #jobs = list(Jobs.all().order('starttime'))
            jobs = event.jobs('startTime')
            page = {'title':'Register'}

            jobblocks = [{'job':job,'blocks':list(Blocks.all().filter('jobid =',job.key().id()).order('starttime'))} for job in jobs]

            self.render('registerform.html',page=page,event=event,user=self.user,jobs=jobblocks,errors=errors,fields=fields)


class VolunteerUserScheduleHandler(utils.DefaultHandler):
    @utils.loggedin
    def get(self):
        blocks = self.user.blocks()
        events = Events.getAll()

        events = [x for x in events if x.enddate >= datetime.now()]

        event_list = []
        for event in events:
            eb = [b for b in list(blocks) if long(b.eventid()) == event.key().id()]
            vol_blocks = sorted(eb, key=lambda x: x.starttime)

            #e = {'event':event, 'blocks':eb}
            event.blocks = vol_blocks
            event_list.append(event)


        self.render('volunteers/volunteerSchedule.html',user=self.user,events=event_list)

class VolunteerUserChangePasswordHandler(utils.DefaultHandler):
  @utils.loggedin
  def get(self):
    if not self.user:
      self.redirect('/')
      return

    self.render('volunteers/changepw.html',user=self.user,errors=None)


  @utils.loggedin
  def post(self):
    if not self.user:
      self.redirect('/')
      return

    old = self.request.get('old_password')
    password = self.request.get('password')
    confirm = self.request.get('confirm')
    valid = True

    errors = {}

    if not utils.valid_pw(self.user.email, old, self.user.password):
      valid = False
      errors['oldbad'] = True
    if not utils.valid_verify(password, confirm):
      valid = False
      errors['mismatch'] = True
    if not utils.valid_password(password):
      valid = False
      errors['badpw'] = True

    if valid:
      self.user.password = utils.make_pw_hash(self.user.email, password)
      self.user.put()
      self.logout()
      self.redirect('/_login')
    else:
      self.render('volunteers/changepw.html',user=self.user,errors=errors)


class VolunteerSearchHandler(utils.DefaultHandler):
    @utils.isadmin
    def post(self):
        email = self.request.get('email')
        if email and utils.valid_email(email):
            vol = Volunteers.gql("WHERE email = :1",email).get()
        else:
            vol = None

        if vol:
            self.redirect('/volunteers/%s'%vol.key().id())
        else:
            page = {'title':'Main','content':''}
            jobs = list(Jobs.all().order('starttime'))
            events = list(Events.all())
            errors = "Volunteer with that email not found. Please ensure your email address is entered correctly and that is the same email you used to register."
            self.render('jobsdesc.html',page=page,user=self.user,jobs=jobs,events=events,errors=errors)


class VolunteerHandler(utils.DefaultHandler):
    @utils.isadmin
    def get(self,volid=None):
        if volid:
            vol = Users.get_by_id(int(volid))
            #print vol.key().id()
            blocks = list(Blocks.all())
            events = list(Events.all())

            blocks = [block for block in Blocks.all().order('starttime') if long(volid) in block.volids]
            #blocks = db.GqlQuery('SELECT * FROM Blocks WHERE :1 IN volids',vol.key().id())

            #jobs = [{'jobname':Jobs.get_by_id(block.jobid).job.name,'block':block} for block in blocks]
            jobs = list(Jobs.all())
            self.render('volunteer.html',volunteer=vol,blocks=blocks,jobs=jobs,user=self.user,events=events)
        else:
            if not self.user:
                self.redirect('/')
                return

            volunteers = list(Volunteers.all().order('name'))
            self.render('volunteers.html',volunteers=volunteers,user=self.user)

class ThankyouHandler(utils.DefaultHandler):
    def get(self):
        self.render('thankyou.html',user=self.user)
