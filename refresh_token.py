from google.cloud import ndb


class RefreshToken(ndb.Model):
    token = ndb.StringProperty()
    issued_at = ndb.DateTimeProperty()
    username = ndb.StringProperty()

    @classmethod
    def kind_name(cls):
        return cls.__name__
