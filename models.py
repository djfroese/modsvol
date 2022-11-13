from google.appengine.ext import db
from google.appengine.api import memcache
from datetime import datetime
import utils

class Users(db.Model):
    #name = db.StringProperty(required=True)
    username = db.StringProperty(required=True)
    password = db.StringProperty(required=True)
    email = db.EmailProperty(required=True)
    phone = db.StringProperty(required=True)
    active = db.BooleanProperty(required=True)
    readonly = db.BooleanProperty(required=True)
    volunteer = db.BooleanProperty(required=True, default=True)

    @classmethod
    def by_id(cls, uid):
    	return cls.get_by_id(uid)

    @classmethod
    def by_name(cls, name):
    	u = cls.all().filter('username = ',name).get()
    	return u

    @classmethod
    def by_email(cls, email):
        u = cls.all().filter('email = ',email).get()
        return u

    @classmethod
    def register(cls, name, pw, email, phone):
    	pw_hash = utils.make_pw_hash(email, pw)
    	return cls(username = name,
    				password = pw_hash,
    				email = email,
    				phone = phone,
    				active = True,
    				readonly = True,
    				volunteer=True)

    @classmethod
    def login(cls, email, pw):
    	u = cls.by_email(email)
    	if u and u.active and utils.valid_pw(email, pw, u.password):
    		return u

    def grantWriteAccess(self):
        self.readonly = False
        self.put()
        return

    def blocks(self):
        result = Blocks.allblocks()
        result = [x for x in result if self.key().id() in x.volids]
        return result

    def isadmin(self):
        return not self.volunteer

class Events(db.Model):
    eventname = db.StringProperty(required=True)
    startdate = db.DateTimeProperty(required=True)
    enddate = db.DateTimeProperty(required=True)
    active = db.BooleanProperty(required=True,default=True)

    @classmethod
    def activeEvents(cls):
        result = list(cls.all().filter("enddate >=",datetime.now()).filter('active =',True).fetch(None))
        return result

    @classmethod
    def by_id(cls, uid):
    	return cls.get_by_id(int(uid))

    @classmethod
    def getAll(cls):
        events = memcache.get("Events:All")
        if events is not None and events != []:
            result = events
        else:
            events = Events.all().fetch(None)
            result = list(events)
            memcache.set("Events:All",result)

        return result

    def jobs(self,order='positions'):
        eventjobs_list = memcache.get('%s:EventJobs'%self.key().id())
        if eventjobs_list is not None:
            result = eventjobs_list
        else:
            result = EventJob.gql("WHERE eventKey = :1 ORDER BY %s ASC"%order, self.key().id()).fetch(None)
            memcache.set('%s:EventJobs'%self.key().id(), list(result))

        #return list(result).sort(key=lambda x: x.startTime, reverse=True)
        return result

    def availablePositions(self):
        result = sum([x.availablePositions() for x in self.jobs()])
        return result

    def hasVolunteer(self, volid):
        jobs = self.jobs()

        for job in jobs:
            if job.hasVolunteer(volid):
                return True

        return False

    def hasJob(self, jobid):
        for job in self.jobs():
            if long(job.jobKey) == long(jobid):
                return True

        return False

    def registrationClosed(self):
        """Returns True if the event takes place within seven days of the current datetime. This is used
           to determine if a volunteer can unregister for a shift on the site or needs to contact the volunteer
           coordinator."""
        if (self.startdate - datetime.now()).days <= 7:
            return True

        return False

    def volunteers(self):
      jobs = self.jobs()

      volunteers = []

      for job in jobs:
        volunteers.extend(job.volunteers())

      volunteers = set(volunteers)

      volunteerList = [Users.by_id(x) for x in volunteers]

      return volunteerList


class Jobs(db.Model):
    name = db.StringProperty(required=True)
    positions = db.IntegerProperty(required=True, default=0) # Depricated Now In EventJob
    description = db.TextProperty(required=True)
    starttime = db.DateTimeProperty() # Depricated Now In EventJob
    endtime = db.DateTimeProperty() # Depricated Now In EventJob
    eventid = db.IntegerProperty() # Depricated Now In EventJob

    @classmethod
    def add(cls, name, description, starttime=None, endtime=None):
        job = cls(name=name, description=description,starttime=starttime,endtime=endtime)
        return job

    @classmethod
    def jobs_blocks(cls):
        jobs = list(cls.all())
        jb = [{'job':job,'blocks':Blocks.by_job_id(job.key().id())} for job in jobs]
        return jb

    @classmethod
    def getAll(cls):
        jobs = memcache.get('Jobs:All')
        if not jobs:
            jobs = list(Jobs.all().fetch(None))
            memcache.set('Jobs:All',jobs)

        return jobs

class Volunteers(db.Model):
    name = db.StringProperty(required=True)
    phone = db.StringProperty(required=True)
    email = db.EmailProperty(required=True)

    @classmethod
    def by_name(cls, name):
        vol = cls.all().filter('name = ',name).get()
        return vol

    @classmethod
    def register(cls, name, phone, email, event):
        return cls(name = name, phone=phone, email=email,event=event)

    def blocks(self):
        result = Blocks.all()
        result = [x for x in result if self.key().id() in x.volids]
        return result

class Blocks(db.Model):
    starttime = db.DateTimeProperty(required=True)
    endtime = db.DateTimeProperty(required=True)
    #jobid = db.IntegerProperty(required=True) # Depricated
    volids = db.ListProperty(long,required=True)
    eventJobid = db.StringProperty(required=True)
    positions = db.IntegerProperty()

    @classmethod
    def add(cls, starttime, endtime, eventJobid):
        # need to check if start and end time are in between eventjob's start and end time
        start = datetime.strptime(starttime,"%Y-%m-%dT%H:%M")
        end = datetime.strptime(endtime,"%Y-%m-%dT%H:%M")
        volids = []
        b = cls(starttime=start, endtime=end, eventJobid=str(eventJobid))
        b.positions = EventJob.get_by_id(eventJobid).positions
        print b.positions
        return b

    @classmethod
    def by_id(cls,bid):
        return cls.get_by_id(bid)

    @classmethod
    def by_job_id(cls,jid):
        return list(Blocks.all().filter('eventJobid =',jid).order('starttime'))

    @classmethod
    def allblocks(cls):
        blocks = memcache.get('AllBlocks')
        if blocks is not None and blocks != []:
          result = blocks
        else:
          result = list(Blocks.all().fetch(None))
          memcache.set('AllBlocks',result)

        return result

    def addVolunteer(self,volid):
        #job = EventJob.get_by_id(int(self.eventJobid))

        if len(self.volids) >= self.positions or volid in self.volids:
            return False
        else:
            self.volids.append(volid)

        return True

    def removeVolunteer(self,volid):
        if volid in self.volids:
          self.volids.remove(volid)
          return True

        return False

    def eventid(self):
        ej = EventJob.get_by_id(int(self.eventJobid))
        return ej.eventKey

    def jobName(self):
        ej = EventJob.get_by_id(long(self.eventJobid))
        return ej.name()

    def volunteers(self):
        volunteers = Users.get_by_id(self.volids)
        return volunteers


class EventVolunteers(db.Model):
    eventKey = db.StringProperty(required=True)
    volKey = db.StringProperty(required=True)

class EventJob(db.Model):
    eventKey = db.IntegerProperty(required=True)
    jobKey = db.IntegerProperty(required=True)
    positions = db.IntegerProperty(required=True)
    startTime = db.DateTimeProperty(required=True)
    endTime = db.DateTimeProperty(required=True)

    def job(self):
        return Jobs.get_by_id(self.jobKey)

    def event(self):
        return Events.get_by_id(self.eventKey)

    def name(self):
        return self.job().name

    def blocks(self,order=None):
        #print type(str(self.key().id()))
        blocks = memcache.get('%s:Blocks:%s'%(self.key().id(),order))
        #print '%s:Blocks:%s'%(self.key().id(),order)
        #print blocks
        if blocks is not None and blocks != []:
            #print "HIT", '%s:Blocks:%s'%(self.key().id(),order)
            result = blocks
        else:
            #print "MISS ", '%s:Blocks:%s'%(self.key().id(),order)
            if order is None:
                blocks = Blocks.gql("WHERE eventJobid = :1",str(self.key().id())).fetch(None)
            else:
                blocks = Blocks.gql("WHERE eventJobid = :eid ORDER BY %s ASC"%order, eid=str(self.key().id())).fetch(None)
            result = list(blocks)
            memcache.set('%s:Blocks:%s'%(self.key().id(),order),result)

        return result

    def availablePositions(self):
        blocks = list(self.blocks())
        filled = 0
        total = 0
        for x in blocks:
            filled += len(x.volids)
            total += x.positions

        #total = len(blocks) * self.positions
        available = total - filled
        assert(available >= 0)

        return available

    def totalPositions(self):
        blocks = list(self.blocks())
        return sum(b.positions for b in blocks)

    def hasVolunteer(self, volid):
        blocks = self.blocks()

        for block in blocks:
            if int(volid) in block.volids:
                return True

        return False

    def update(self):
        bs = self.blocks()
        if bs != []:
            self.startTime = min([b.starttime for b in bs])
            self.endTime = max([b.endtime for b in bs])

        self.put()
        memcache.flush_all()

    def volunteers(self):
      blocks = self.blocks()

      volunteers = []
      for block in blocks:
        volunteers.extend(block.volids)

      return volunteers



class Log(db.Model):
    userid = db.IntegerProperty(required=True)
    action = db.StringProperty(required=True)
    timestamp = db.DateTimeProperty(required=True,default=datetime.now())
    type = db.StringProperty(required=True)
    content = db.TextProperty(default="")
    level = db.IntegerProperty(default=3)


class AssignedBlocksJobs(db.Model):
    blockkey = db.StringProperty(required=True)
    volkey = db.StringProperty(required=True)
    jobkey = db.StringProperty(required=True)

class VolunteerJobs(db.Model):
    volid = db.IntegerProperty(required=True)
    jobids = db.ListProperty(long,required=True)
