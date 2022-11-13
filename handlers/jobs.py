import webapp2, utils, re, datetime, json
from models import *
from google.appengine.ext import db

class JobsHandler(utils.DefaultHandler):

    @utils.isadmin
    def get(self,jobid=None):
        if not self.user:
            self.redirect('/')
            return

        if jobid:
            job = Jobs.get_by_id(int(jobid))
            blocks = list(Blocks.all().filter('jobid =',long(jobid)).order('starttime'))
        else:
            job = None
            blocks = None

        page = {'title':'Jobs'}

        self.render('jobs.html',page=page,user=self.user,job=job,blocks=blocks)

    @utils.isadmin
    def post(self,jobid=None):
        if not self.user or self.user.readonly:
            self.redirect('/')
            return

        name = self.request.get('name')
        #positions = int(self.request.get('positions'))
        description = self.request.get('description')
        #start = self.request.get('start')
        #end = self.request.get('end')

        #start = datetime.strptime(start,'%Y-%m-%dT%H:%M')
        #end  = datetime.strptime(end,'%Y-%m-%dT%H:%M')

        self.redirect('/admin')

        if jobid:
            # print 'found job'
            job = Jobs.get_by_id(int(jobid))
            # print job
        else:
            job = None

        if job:
            job.name = name
            job.description = description
        else:
            job = Jobs.add(name=name,description=description)
        job.put()

class JobJSONLoadHandler(utils.DefaultHandler):

    @utils.isadmin
    def get(self):
        page = {"title":"Jobs JSON Uploader"}

        self.render("jobs_load.html",user=self.user,page=page)

    @utils.isadmin
    def post(self):
        jsondata = self.request.get('jsondata')

        data = json.loads(jsondata)

        for x in data:
            job = Jobs(name=x['name'], description=x['description'])
            #job.name = x.name
            #job.description = x.description
            job.put()

        self.redirect('/admin')
