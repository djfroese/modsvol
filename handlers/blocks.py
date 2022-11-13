import webapp2, utils, re, datetime
from models import *
from google.appengine.ext import db

class BlocksListHandler(utils.DefaultHandler):
    @utils.isadmin
    def get(self,jobid):

        page = {'title':'Blocks'}
        blocks = list(Blocks.all().filter('jobid =',int(jobid)).order('starttime'))

        print jobid
        if jobid:
            job = EventJob.get_by_id(int(jobid))
        else:
            job = None

        self.render('blocks.html',page=page,blocks=blocks,user=self.user,job=job)

    # Creates a new block

    @utils.isadmin
    def post(self, eventJobid):
        if not self.user or self.user.readonly:
            self.redirect('/jobs/%s'%jobid)
            return

        st = self.request.get('starttime')
        et = self.request.get('endtime')
        st = datetime.strptime(st,'%Y-%m-%dT%H:%M')
        et = datetime.strptime(st,'%Y-%m-%dT%H:%M')

        block = Blocks(starttime = st , endtime = et, eventJobid=int(eventJobid), volids=[])
        block.put()


        memcache.delete('AllBlocks',seconds=2)
        memcache.delete('%s:Blocks:%s'%(block.eventJobid, "None"),seconds=2)
        #memcache.delete('%s:Blocks:%s'%(block.eventJobid, "startTime"),seconds=2)
        memcache.delete('%s:Blocks:%s'%(block.eventJobid, "starttime"),seconds=2)
        memcache.delete('%s:Blocks'%block.eventJobid, seconds=2)
        memcache.delete('%s:EventJobs'%(eventid),seconds=2)

        self.redirect('/jobs/%s'%jobid,permanent=False)


class BlocksHandler(utils.DefaultHandler):
    @utils.isadmin
    def get(self, blockid):
        block = Blocks.get_by_id(long(blockid))
        job = EventJob.get_by_id(long(block.eventJobid))

        blockvolunteers = list(Volunteers.get_by_id(ids=block.volids))
        volunteers = list(Volunteers.all())
        self.render('blocks.html',page={'title':'Block'},job=job,block=block,blockvolunteers=blockvolunteers,volunteers=volunteers,user=self.user)

    @utils.isadmin
    def post(self,blockid):
        if not self.user or self.user.readonly:
            self.redirect('/schedule')
            return

        blockid = long(blockid)
        volid = long(self.request.get('volid'))

        block = Blocks.get_by_id(blockid)

        if volid in block.volids:
            block.volids.remove(volid)

        block.put()

        memcache.delete('AllBlocks',seconds=2)
        memcache.delete('%s:Blocks:%s'%(block.eventJobid, "None"),seconds=2)
        #memcache.delete('%s:Blocks:%s'%(block.eventJobid, "startTime"),seconds=2)
        memcache.delete('%s:Blocks:%s'%(block.eventJobid, "starttime"),seconds=2)
        memcache.delete('%s:Blocks'%block.eventJobid, seconds=2)
        memcache.delete('%s:EventJobs'%(eventid),seconds=2)

        self.redirect('/blocks/%s'%blockid)

# Add a volunteer to a block
class BlocksVolunteerHandler(utils.DefaultHandler):
    @utils.isadmin
    def post(self,blockid):
        if not self.user or self.user.readonly:
            self.redirect('/')
            return

        blockid = long(blockid)

        volid = long(self.request.get('volunteer'))

        block = Blocks.get_by_id(blockid)

        block.addVolunteer(volid)
        block.put()

        memcache.delete("AllBlocks",seconds=5)
        memcache.delete("%s:Blocks:%s"%(block.eventJobid, "None"),seconds=2)
        #memcache.delete('%s:Blocks:%s"%(block.eventJobid, "startTime"),seconds=2)
        memcache.delete("%s:Blocks:%s"%(block.eventJobid, "starttime"),seconds=2)
        memcache.delete("%s:Blocks"%block.eventJobid, seconds=2)
        memcache.delete("%s:EventJobs"%(eventid),seconds=2)

        self.redirect('/blocks/%s'%blockid)

# delete block from eventjob
class BlocksDeleteHandler(utils.DefaultHandler):
    @utils.isadmin
    def post(self,blockid):
        if not self.user or self.user.readonly:
            self.redirect('/')
            return

        blockid = long(blockid)
        block = Blocks.get_by_id(blockid)
        jobid = block.eventJobid
        eventid = block.eventid()
        block.delete()

        memcache.delete('AllBlocks',seconds=2)
        memcache.delete('%s:Blocks:%s'%(block.eventJobid, "None"),seconds=2)
        #memcache.delete('%s:Blocks:%s'%(block.eventJobid, "startTime"),seconds=2)
        memcache.delete('%s:Blocks:%s'%(block.eventJobid, "starttime"),seconds=2)
        memcache.delete('%s:Blocks'%block.eventJobid, seconds=2)
        memcache.delete('%s:EventJobs'%(eventid),seconds=2)

        self.redirect('/events/%s/jobs/%s/'%(eventid,jobid))

# edit block
class BlocksEditHandler(utils.DefaultHandler):

    @utils.isadmin
    def get(self,blockid):
        blockid = long(blockid)
        block = Blocks.get_by_id(blockid)

        self.render('blocks_edit.html', page={'title':'Block'}, block=block, user=self.user)

    @utils.isadmin
    def post(self,blockid):
        if not self.user or self.user.readonly:
            self.redirect('/')
            return

        blockid = long(blockid)
        block = Blocks.get_by_id(blockid)
        eventid = block.eventid()
        start = self.request.get('start')
        end = self.request.get('end')
        positions = long(self.request.get('positions'))

        block.starttime = datetime.strptime(start,'%Y-%m-%dT%H:%M')
        block.endtime = datetime.strptime(end,'%Y-%m-%dT%H:%M')
        block.positions = positions

        #print '%s:Blocks:%s'%(block.eventJobid,None)

        block.put()

        self.redirect('/events/%s/jobs/%s/'%(eventid,block.eventJobid))
        memcache.delete('AllBlocks',seconds=2)
        memcache.delete('%s:Blocks:%s'%(block.eventJobid, "None"),seconds=2)
        #memcache.delete('%s:Blocks:%s'%(block.eventJobid, "startTime"),seconds=2)
        memcache.delete('%s:Blocks:%s'%(block.eventJobid, "starttime"),seconds=2)
        memcache.delete('%s:Blocks'%block.eventJobid, seconds=2)
        memcache.delete('%s:EventJobs'%(eventid),seconds=2)


class BlocksVolunteerLeaveHandler(utils.DefaultHandler):
  @utils.loggedin
  def post(self,blockid):
    block = Blocks.by_id(long(blockid))
    if block.removeVolunteer(self.user.key().id()):
      block.put()
      memcache.delete('AllBlocks',seconds=2)
      memcache.delete('%s:Blocks:%s'%(block.eventJobid, "None"),seconds=2)
      #memcache.delete('%s:Blocks:%s'%(block.eventJobid, "startTime"),seconds=2)
      memcache.delete('%s:Blocks:%s'%(block.eventJobid, "starttime"),seconds=2)
      memcache.delete('%s:Blocks'%block.eventJobid, seconds=2)
      memcache.delete('%s:EventJobs'%(eventid),seconds=2)

    self.redirect('/user/schedule')
