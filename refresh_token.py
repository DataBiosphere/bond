from google.appengine.ext import ndb


class RefreshToken(ndb.Model):
    token = ndb.StringProperty()
    issued_at = ndb.DateTimeProperty()

    @classmethod
    def kind_name(cls):
        return cls.__name__
