import webapp2, utils, re, datetime
from google.appengine.ext import db
from models import *
import utils

class UserScheduleHandler(utils.DefaultHandler):

    @utils.loggedin
    def get(self):
        pass


class VolunteersFromEvent(utils.DefaultHandler):

  @utils.isadmin
  def get(self, eventid):
    event = Events.by_id(long(eventid))

    volunteers = event.volunteers()
    
    self.render("volunteers/eventVolunteers.html",
                user=self.user,
                page={"title": "Event Volunteers Contact Info"},
                volunteerList=volunteers)
