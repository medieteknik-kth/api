from api.db import db
import datetime

from api.models.post_tag import PostTag
class Event(db.Model):
    __tablename__ = "events"
    event_id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String)
    date = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    description = db.Column(db.Text)
    location = db.Column(db.String)
    committee_id = db.Column(db.Integer, db.ForeignKey('committee.id'))
    committee = db.relationship("Committee", back_populates = "events")
    header_image = db.Column(db.String)
    #tags = db.relationship("PostTag")

    

    def to_dict(self):
        return {
            "id": self.event_id,
            "title": self.title,
            "date": self.date,
            "description": self.description,
            "location": self.location,
            "headerImage": self.header_image,
            "committeee": self.committee_id,
            #"tags": [t.to_dict() for t in self.tags]
        }