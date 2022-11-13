import webapp2, utils, re, datetime
from google.appengine.ext import db
from google.appengine.api import memcache
from models import *
import utils

class PrintPosterSchedule(utils.DefaultHandler):

  @utils.isadmin
  def get(self, eventid):
    event = Events.by_id(long(eventid))

    #jobs = event.jobs('startTime');

    event.jobsList = [j for j in event.jobs('startTime') if len(j.blocks()) > 0]

    for job in event.jobsList:
      job.blocksList = [b for b in job.blocks('starttime') if len(b.volids) > 0]

    for block in job.blocksList:
      block.volunteersList = [v for v in block.volunteers() if len(block.volunteers()) > 0]

    self.render('printscreens/poster.html',user=self.user, event=event)

class VolunteerReport(utils.DefaultHandler):

  @utils.isadmin
  def get(self):
    volunteers = Users.all().fetch(None)

    for volunteer in volunteers:
      volunteer.slotCount = len(volunteer.blocks())


    volunteers.sort(key=lambda x: x.slotCount, reverse=True)

    self.render('printscreens/blockcount.html', user=self.user, volunteers=volunteers)

class PrintSigninSheet(utils.DefaultHandler):

  @utils.isadmin
  def get(self, eventid):
    event = Events.by_id(long(eventid))

    #jobs = event.jobs('startTime');

    event.jobsList = [j for j in event.jobs('startTime') if len(j.blocks()) > 0]

    for job in event.jobsList:
      job.blocksList = [b for b in job.blocks('starttime') if len(b.volids) > 0]

    for block in job.blocksList:
      block.volunteersList = [v for v in block.volunteers() if len(block.volunteers()) > 0]

    self.render('printscreens/signinsheet.html',user=self.user, event=event)
