import webapp2, cgi, re, jinja2, os, uuid, random, string, hashlib, datetime, hmac, logging, models, functools
from datetime import timedelta
from functools import update_wrapper

def guess_autoescape(template_name):
    if template_name == 'history.html':
        return True
    else:
        return False

def dateformat(value, format='%x'):
    return value.strftime(format)

def readabledateonly(value, format='%A %B %d, %Y'):
    return value.strftime(format)

def readabledate(value, format='%A %B %d %I:%M %p'):
    return value.strftime(format)

def entrydate(value, format='%Y-%m-%dT%H:%M'):
    return value.strftime(format)

def listcount(value):
    return len(value)

def timeblock(block):
    return "%s<br>%s"%(block.starttime.strftime('%I:%M%p').lstrip("0").replace(" 0", " "),block.endtime.strftime('%I:%M%p').lstrip("0").replace(" 0", " "))

def waschecked(args):
    fields = args[0]
    block = args[1]
    return fields and fields['blocks'] and block.key().id() in [x.key().id() for x in fields['blocks']]


template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),autoescape=guess_autoescape)
jinja_env.filters['dateformat'] = dateformat
jinja_env.filters['readabledateonly'] = readabledateonly
jinja_env.filters['readabledate'] = readabledate
jinja_env.filters['entrydate'] = entrydate
jinja_env.filters['listcount'] = listcount
jinja_env.filters['timeblock'] = timeblock
jinja_env.filters['waschecked'] = waschecked

#--------------------------------------------------------------------------
# Validation functions
#--------------------------------------------------------------------------

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile(r"^.{3,20}$")
EMAIL_RE = re.compile(r"^[\S]+@[\S]+\.[\S]+$")

def valid_username(uname):
    return USER_RE.match(uname)

def valid_password(password):
    return PASS_RE.match(password)

def valid_verify(password, verify):
    return password == verify

def valid_email(email):
    if len(email) > 0:
        return EMAIL_RE.match(email)
    else:
        return True


def valid_blocks(blocks):
    for b1 in blocks:
        for b2 in blocks:
            if b1.key().id() == b2.key().id():
                continue
            if b1.starttime < b2.starttime and b1.endtime > b2.starttime:
                return False
            if b1.starttime == b2.starttime or b1.endtime==b2.endtime:
                return False
    return True


#--------------------------------------------------------------------------
# Hashing functions
#--------------------------------------------------------------------------

secret = "du.uyXi98872nasdbDIIr.&8**1,9()c0-&$asd^"



def make_salt():
    return ''.join(random.choice(string.letters+string.digits) for x in xrange(16))

def make_pw_hash(email, pw,salt=make_salt()):
    h = hashlib.sha256(email + pw + salt).hexdigest()
    return '%s|%s' % (h, salt)

def valid_pw(email, pw, h):
    salt = h.split('|')[1]
    if make_pw_hash(email,pw,salt) == h:
        return True

def make_secure_val(val):
    return "%s|%s" % (val,hmac.new(secret, val).hexdigest())

def check_secure_val(h):
    val = h.split('|')[0]
    if make_secure_val(val) == h:
        return val

#--------------------------------------------------------------------------
# Decorators
#--------------------------------------------------------------------------

def decorator(d):
    "Make function d a decorator: d wraps a function fn."

    def _d(fn):
        return functools.update_wrapper(d(fn), fn)

    return _d
decorator = decorator(decorator)

# Decorators that work on def get(self, **kwargs) or post(self, **kwargs)

@decorator
def loggedin(f):
    def _f(self, *args, **kwargs):
#        print("CHECKING LOGGED IN")
        if not self.user:
            self.redirect('/')
            return
        else:
            f(self, *args,**kwargs)

    return _f


@decorator
def isadmin(f):
    def _f(*args, **kwargs):
#        print("CHECKING IS ADMIN OR VOLUNTEER")
        if not args[0].user:
            args[0].redirect('/')
            return
        else:
            if args[0].user.volunteer:
                args[0].redirect('/')
                return
            f(*args,**kwargs)

    return _f


#--------------------------------------------------------------------------
# Handler
#--------------------------------------------------------------------------

class DefaultHandler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))

	def set_secure_cookie(self, name, val):
		cookie_val = make_secure_val(val)
		self.response.headers.add_header('Set-Cookie', '%s=%s; Path=/' % (name, cookie_val))

	def read_secure_cookie(self, name):
		cookie_val = self.request.cookies.get(name)
		return cookie_val and check_secure_val(cookie_val)

	def login(self, user):
		self.set_secure_cookie('user_id', str(user.key().id()))

	def logout(self):
		self.response.headers.add_header('Set-Cookie', 'user_id=; Path=/')

	def initialize(self, *a, **kw):
		webapp2.RequestHandler.initialize(self, *a, **kw)
		uid = self.read_secure_cookie('user_id')
		self.user = uid and models.Users.by_id(int(uid))
