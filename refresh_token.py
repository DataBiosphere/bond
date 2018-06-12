from google.appengine.ext import ndb


class RefreshToken(ndb.Model):
    token = ndb.StringProperty()

    @classmethod
    def kind_name(cls):
        return cls.__name__
