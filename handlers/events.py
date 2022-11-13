import webapp2, utils, re, datetime
from models import *
from google.appengine.ext import db
from datetime import timedelta

class EventEditHandler(utils.DefaultHandler):

    @utils.isadmin
    def get(self, eventid):
        event = Events.by_id(int(eventid))
        jobs = list(Jobs.all().order('name'))
        self.render('event_edit.html',user=self.user,event=event, jobs=jobs, errors={},selected_positions={},selected_jobs=[])

    @utils.isadmin
    def post(self, eventid):
        event = Events.by_id(long(eventid))
        startdate = self.request.get('startdate')
        enddate = self.request.get('enddate')
        active = self.request.get('active')

        startdate = datetime.strptime(startdate,"%Y-%m-%d")
        enddate = datetime.strptime(enddate,"%Y-%m-%d")

        if active:
            event.active = True
        else:
            event.active = False

        event.name = self.request.get('name')
        event.startdate = startdate
        event.enddate = enddate

        event.put()

        self.redirect('/events/%s'%eventid)



class EventJobsEditHandler(utils.DefaultHandler):

    @utils.isadmin
    def post(self, eventid):
        jobid = self.request.get('jobid')

        positions = {}
        seljobs = []

        errors = {}
        valid = True

        post_args = self.request.arguments()
        for pa in post_args:
            field, jid = pa.split('-')
            jid = int(jid)
            if field == 'positions':
                positions[jid] = int(self.request.get(pa))
            elif field == 'job':
                seljobs.append(jid)
        event = Events.by_id(int(eventid))

        for jid in seljobs:
            #ej = EventJob.all().filter('jobKey=',int(jid)).filter('eventKey=',int(eventid)).get()
            ej = EventJob.gql("WHERE jobKey = :1 AND eventKey = :2",int(jid),int(eventid)).get()
            print ej
            if positions[jid] == 0:
                errors['zero'] = "Positions for one or more selected jobs is 0 (zero). Either uncheck the job or add the number of positions"
                valid = False

            if ej:
                errors['job_exists'] = "A job you are trying to add already exists. Check the jobs listed above and try again."
                valid = False

            print "ERRORS FOLLOW", errors

            if valid:

                ejob = EventJob(jobKey = jid,
                              eventKey = int(eventid),
                              positions = positions[jid],
                              startTime = event.startdate,
                              endTime = event.enddate)
                ejob.put()
                # UPDATE CACHE




        if not valid:
            print "SHOULD SHOW ERROR"
            jobs = list(Jobs.all())

            self.render('event_edit.html', user=self.user, event=event, jobs=jobs, errors=errors, selected_jobs=seljobs, selected_positions=positions)
            return
        else:
             print "REDIRECTING"
             event.jobs()
             event.jobs(order='startTime')
             #memcache.add(key='%s:EventJobs:%s'%(event.key().id(),order), value=list(EventJob.gql("WHERE eventKey = :1 ORDER BY %s ASC"%order, event.key().id()).fetch(None)))
             self.redirect('/events/%s'%eventid)

def interval_datetimes(start, end, interval, margin=0, extends=False):
    """Returns a list of datetimes that are each separated by the interval."""
    dts = []
    step = timedelta(hours=interval-margin)
    margin = timedelta(hours=margin)
    interval = timedelta(hours=interval)

    current = start

    while current < end:
        if not (extends and end-current < interval):
            dts.append(current)
        current += step

    return dts

class EventBlockEditHandler(utils.DefaultHandler):
    @utils.isadmin
    def get(self, eventid, eventJobid):
        event = Events.by_id(int(eventid))
        job = EventJob.get_by_id(int(eventJobid))
        #blocks = job.blocks()

        self.render('event_jobs.html', user=self.user, event=event, job=job, now=datetime.now(),errors={})


    @utils.isadmin
    def post(self, eventid, eventJobid):
        startdt = self.request.get('starttime')
        enddt = self.request.get('endtime')
        interval = float(self.request.get('interval'))
        overlap = False
        extends = False
        margin = 0

        valid = True
        errors = {}

        try:
            if self.request.get('extends'):
                extends = True
        except:
            extends = False

        try:
            if self.request.get('overlap'):
                overlap = True
                margin = float(self.request.get('margin'))
        except:
            overlap = False
            margin = 0


        start = datetime.strptime(startdt,'%Y-%m-%dT%H:%M')
        end = datetime.strptime(enddt,'%Y-%m-%dT%H:%M')

        event = Events.by_id(eventid)
        job = EventJob.get_by_id(int(eventJobid))

        if ( overlap and (margin > (interval/2)) ):
            valid = False
            errors['overlap'] = "Overlap margin can be no larger that half the length of the interval."

        if start < event.startdate or start > event.enddate+timedelta(days=1):
            valid = False
            errors['outofbounds'] = 'Blocks do not take place during the current event.'

        if end < event.startdate or end > event.enddate+timedelta(days=1):
            valid = False
            errors['outofbounds'] = 'Blocks do not take place during the current event.'

        if start > end:
            valid = False
            errors['paradox'] = 'End takes place before block Start Time.'

        if interval <= 0:
            valid = False
            errors['intervallength'] = 'Interval must be at least half an hour (0.5).'

        if not valid:
            self.render('event_jobs.html', user=self.user, event=event, job=job, now=datetime.now(),errors=errors)
            return

        dts = interval_datetimes(start, end, interval, margin, extends)
        interval = timedelta(hours=interval)

        for dt in dts:
            et = dt+interval

            if ( extends and end-et < interval ) or et > end:
                et = end

            #print dt, " to ", et
            block = Blocks(starttime=dt, endtime=et, eventJobid=eventJobid, volids=[], positions=job.positions)
            block.put()

            memcache.delete('AllBlocks',seconds=2)
            memcache.delete('%s:Blocks:%s'%(block.eventJobid, "None"),seconds=2)
            #memcache.delete('%s:Blocks:%s'%(block.eventJobid, "startTime"),seconds=2)
            memcache.delete('%s:Blocks:%s'%(block.eventJobid, "starttime"),seconds=2)
            memcache.delete('%s:Blocks'%block.eventJobid, seconds=2)
            memcache.delete('%s:EventJobs'%(eventid),seconds=2)

        #block = Blocks.add(startdt, enddt, eventJobid=int(eventJobid))
        # TODO: Need to make sure block start and end times are inside Events start and end times

        #block.put()

        self.redirect('/events/%s/jobs/%s/'%(eventid, eventJobid))


class EventJobsUpdateHandler(utils.DefaultHandler):
    @utils.isadmin
    def get(self, eventid):
        event = Events.by_id(long(eventid))
        for ejs in event.jobs():
            ejs.update()
            ejs.put()

        self.redirect('/events/%s'%eventid)
