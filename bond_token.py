from google.appengine.ext import ndb


class BondToken(ndb.Model):
    token_dict = ndb.TextProperty()
