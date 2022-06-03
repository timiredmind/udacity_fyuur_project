from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class Venue(db.Model):
    __tablename__ = "venues"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120), nullable=False)
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean)
    seeking_description = db.Column(db.String)
    shows = db.relationship("Show", backref="venue", lazy=True, cascade="all, delete-orphan")
    genres = db.relationship("Genre", secondary="venue_genre", lazy="subquery",
                             backref=db.backref('venues', lazy=True))

    def __repr__(self):
        return f"<Venue {self.id}: {self.name}>"

    def upcoming_shows(self):
        # return [show for show in self.shows if show.start_time > datetime.now()]
        return db.session.query(Show).filter(Show.venue_id == self.id, Show.start_time > datetime.now()).all()

    def past_shows(self):
        # return [show for show in self.shows if show.start_time <= datetime.now()]
        return db.session.query(Show).filter(Show.venue_id == self.id, Show.start_time <= datetime.now()).all()

    def upcoming_show_count(self):
        return db.session.query(Show).filter(Show.venue_id == self.id, Show.start_time > datetime.now()).count()

    def past_shows_count(self):
        return db.session.query(Show).filter(Show.venue_id == self.id, Show.start_time <= datetime.now()).count()


artist_genre = db.Table("artist_genre",
                        db.Column("artist_id", db.Integer, db.ForeignKey("artists.id"), primary_key=True),
                        db.Column("genre_id", db.Integer, db.ForeignKey("genres.id"), primary_key=True)
                        )

venue_genre = db.Table("venue_genre",
                       db.Column("venue_id", db.Integer, db.ForeignKey("venues.id"), primary_key=True),
                       db.Column("genre_id", db.Integer, db.ForeignKey("genres.id"), primary_key=True)
                       )


class Genre(db.Model):
    __tablename__ = "genres"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable=False)
    # TODO: implement any missing fields, as a database migration using
    # Flask-Migrate
    def __repr__(self):
        return f"<Genre {self.id}>"


class Artist(db.Model):
    __tablename__ = "artists"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False, unique=True)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean)
    seeking_description = db.Column(db.String)
    shows = db.relationship("Show", backref="artist", lazy=True)
    genres = db.relationship("Genre", secondary=artist_genre, lazy="subquery",
                             backref=db.backref("artists", lazy=True))
    time_available_from = db.Column(db.Time, nullable=False)
    time_available_to = db.Column(db.Time, nullable=False)

    def __repr__(self):
        return f"<Artist {self.id} {self.name}>"

    def upcoming_shows(self):
        return db.session.query(Show).filter(Show.artist_id == self.id, Show.start_time > datetime.now()).all()

    def past_shows(self):
        return db.session.query(Show).filter(Show.artist_id == self.id, Show.start_time <= datetime.now()).all()

    def upcoming_shows_count(self):
        return db.session.query(Show).filter(Show.artist_id == self.id, Show.start_time > datetime.now()).count()

    def past_shows_count(self):
        return db.session.query(Show).filter(Show.artist_id == self.id, Show.start_time <= datetime.now()).count()
    # TODO: implement any missing fields, as a database migration using
    # Flask-Migrate


# TODO Implement Show and Artist models, and complete all model
# relationships and properties, as a database migration.
class Show(db.Model):
    __tablename__ = "shows"
    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey("artists.id"), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey("venues.id"), nullable=False)
    start_time = db.Column(db.DateTime(), nullable=False)

    def __repr__(self):
        return f"<Show {self.id}  starts {self.start_time}>"