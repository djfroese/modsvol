#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2, utils, re, datetime
from models import *
from handlers import *
from google.appengine.ext import db

class MainHandler(utils.DefaultHandler):
    def get(self):
        page = {'title':'Main','content':'Some Default Content'}
        jobs = Jobs.getAll()
        events = Events.activeEvents()
        self.render('jobsdesc.html',page=page, user=self.user, jobs=jobs, events=events, errors=None)


class EventHandler(utils.DefaultHandler):
    def get(self):
        if not self.user:
            self.redirect('/admin')
            return

        page = {'title':'Add Event'}
        self.render('event.html',page=page,now=datetime.strftime(datetime.now(),'%Y-%m-%d'))

    def post(self):
        if not self.user:
            self.redirect('/admin')
            return

        name = self.request.get('eventname')
        start = self.request.get('startdate')
        end = self.request.get('enddate')

        start = datetime.strptime(start,'%Y-%m-%d')
        end  = datetime.strptime(end,'%Y-%m-%d')

        self.redirect('/admin')
        e = Events(eventname=name,startdate=start,enddate=end)
        e.put()

app = webapp2.WSGIApplication([
     ('/', MainHandler),
     ('/admin/start',StartHandler),
     ('/volunteers', VolunteerHandler),
     ('/volunteers/_find', VolunteerSearchHandler),
     ('/volunteers/report', VolunteerReport),
     ('/volunteers/(.*)', VolunteerHandler),
     ('/jobs/_load', JobJSONLoadHandler),
     ('/jobs/(.*)/blocks', BlocksListHandler),
     ('/jobs/(.*)', JobsHandler),
     ('/jobs', JobsHandler),
     ('/events/(\d+)/jobs/(\d+)/', EventBlockEditHandler),
     ('/events/(\d+)/register', RegistrationHandler),
     ('/events/(\d+)/schedule',VolunteerScheduleHandler),
     ('/events/(\d+)/_poster', PrintPosterSchedule),
     ('/events/(\d+)/_signinsheet', PrintSigninSheet),
     ('/events/(\d+)/_add', EventJobsEditHandler),
     ('/events/(\d+)/_update',EventJobsUpdateHandler),
     ('/events/(\d+)/_volunteers', VolunteersFromEvent),
     ('/events/(\d+)', EventEditHandler),
     ('/events', EventHandler),
     ('/blocks/(.*)/_del', BlocksDeleteHandler),
     ('/blocks/(.*)/_addvol', BlocksVolunteerHandler),
     ('/blocks/(.*)/_edit', BlocksEditHandler),
     ('/blocks/(\d+)/_leave', BlocksVolunteerLeaveHandler),
     ('/blocks/(.*)', BlocksHandler),
     ('/_login', LoginHandler),
     ('/_logout', LogoutHandler),
     ('/_signup', SignupHandler),
     ('/admin', AdminConsoleHandler),
     ('/user/schedule', VolunteerUserScheduleHandler),
     ('/user/_changepw', VolunteerUserChangePasswordHandler),
     ('/admin/user/(.*)', UserHandler),
     #('/admin/_clearvolids', ClearVolunteers),
     ('/thankyou',ThankyouHandler)
     ], debug=True)
