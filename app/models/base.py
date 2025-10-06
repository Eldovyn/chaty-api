import mongoengine as me
import datetime


class BaseDocument(me.Document):
    meta = {"abstract": True}

    created_at = me.DateTimeField(default=datetime.datetime.now(datetime.timezone.utc))
    updated_at = me.DateTimeField(default=datetime.datetime.now(datetime.timezone.utc))
    deleted_at = me.DateTimeField(null=True)

    def save(self, *args, **kwargs):
        if not self.created_at:
            self.created_at = datetime.datetime.now(datetime.timezone.utc)
        self.updated_at = datetime.datetime.now(datetime.timezone.utc)
        return super(BaseDocument, self).save(*args, **kwargs)

    def soft_delete(self):
        self.deleted_at = datetime.datetime.now(datetime.timezone.utc)
        return super(BaseDocument, self).save()
