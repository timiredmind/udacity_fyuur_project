# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#

import json
import sys

import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from models import Venue, Artist, Show, Genre, db

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object("config")
db.init_app(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#


def format_datetime(value, format="medium"):
    date = dateutil.parser.parse(value)
    if format == "full":
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == "medium":
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale="en")


app.jinja_env.filters["datetime"] = format_datetime

# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#


@app.route("/")
def index():
    recently_listed_venue = Venue.query.order_by(Venue.id.desc()).limit(10).all()
    recently_listed_artist = Artist.query.order_by(Artist.id.desc()).limit(10).all()
    return render_template("pages/home.html", new_artists=recently_listed_artist, new_venues=recently_listed_venue)


#  Venues
#  ----------------------------------------------------------------


@app.route("/venues")
def venues():
    # TODO: replace with real venues data.
    # num_upcoming_shows should be aggregated based on number of upcoming
    # shows per venue.
    form = SearchByCityForm()
    areas = db.session.query(Venue.city, Venue.state).group_by(Venue.city, Venue.state).order_by(Venue.state.asc()).all()
    data = []
    for area in areas:
        location = {"city": area.city, "state": area.state}
        venue_list = []
        for venue in Venue.query.filter(Venue.city == area.city, Venue.state == area.state).all():
            venue_detail = {
                "id": venue.id,
                "name": venue.name,
                "num_upcoming_shows": venue.upcoming_show_count(),
            }
            venue_list.append(venue_detail)
        location["venues"] = venue_list
        data.append(location)
    return render_template("pages/venues.html", areas=data, form=form)


@app.route("/venues/search", methods=["POST"])
def search_venues():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # search for Hop should return "The Musical Hop".
    # search for "Music" should return "The Musical Hop" and "Park Square Live
    # Music & Coffee"
    search_term = request.form.get("search_term", "")
    query = Venue.query.filter(Venue.name.ilike(f"%{search_term}%")).all()
    query_count = Venue.query.filter(Venue.name.ilike(f"%{search_term}%")).count()
    response = {
        'count': query_count,
        "data": [
            {"id": item.id, "name": item.name} for item in query
        ]
    }
    return render_template(
        "pages/search_venues.html",
        results=response,
        search_term=search_term,
    )


@app.route("/venues/search_by_city", methods=["POST"])
def search_venue_by_city():
    form = SearchByCityForm(request.form)
    city = form.city.data
    state = form.state.data
    search_term = f"{city}, {state}"
    query = Venue.query.filter(Venue.city == city, Venue.state == state).all()
    query_count = Venue.query.filter(Venue.city == city, Venue.state == state).count()
    response = {
        "count": query_count,
        "data": [
            {"id": item.id, "name": item.name} for item in query
        ]
    }
    return render_template(
        "pages/search_venues.html",
        results=response,
        search_term=search_term,
    )


@app.route("/venues/<int:venue_id>")
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    # TODO: replace with real venue data from the venues table, using venue_id
    venue = Venue.query.get(venue_id)
    if not venue:
        abort(404)

    data = {"id": venue.id, "name": venue.name, "genres": [genre.name for genre in venue.genres],
            "address": venue.address, "city": venue.city,
            "state": venue.state, "phone": venue.phone, "website": venue.website_link,
            "facebook_link": venue.facebook_link, "seeking_talent": venue.seeking_talent,
            "seeking_description": venue.seeking_description, "image_link": venue.image_link,
            "past_shows": [], "past_shows_count": venue.past_shows_count(),
            "upcoming_shows_count": venue.upcoming_show_count(), "upcoming_shows": []}
    for show in venue.upcoming_shows():
        artist = {
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        }
        data["upcoming_shows"].append(artist)

    for show in venue.past_shows():
        artist = {
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        }
        data["past_shows"].append(artist)
    return render_template("pages/show_venue.html", venue=data)


#  Create Venue
#  ----------------------------------------------------------------


@app.route("/venues/create", methods=["GET"])
def create_venue_form():
    form = VenueForm()
    return render_template("forms/new_venue.html", form=form)


@app.route("/venues/create", methods=["POST"])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    form = VenueForm(request.form)

    try:
        new_venue = Venue(
            name=form.name.data,
            state=form.state.data,
            city=form.city.data,
            phone=form.phone.data,
            image_link=form.image_link.data,
            facebook_link=form.facebook_link.data,
            website_link=form.website_link.data,
            seeking_talent=form.seeking_talent.data,
            seeking_description=form.seeking_description.data,
            address=form.address.data
        )

        genres = []
        for genre_name in form.genres.data:
            genre_instance = Genre.query.filter_by(name=genre_name).first()
            if genre_instance:
                genres.append(genre_instance)
            else:
                new_genre = Genre(name=genre_name)
                genres.append(new_genre)

        new_venue.genres.extend(genres)
        db.session.add(new_venue)
        db.session.commit()
    except:
        print(sys.exc_info())
        db.session.rollback()
        flash(f"An error occurred while creating new venue. Venue {form.name.data} couldn't be listed.")
    else:
        flash(f"Venue { form.name.data } was successfully listed!")
        db.session.close()
    # on successful db insert, flash success

    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template("pages/home.html")


@app.route("/venues/<int:venue_id>", methods=["DELETE"])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit
    # could fail.
    venue = Venue.query.get(venue_id)
    if not venue:
        abort(404)
    try:
        db.session.delete(venue)
        db.session.commit()
    except:
        print(sys.exc_info)
        db.session.rollback()
        flash(f"An error occurred while trying to unlist Venue {venue.id}")
    else:
        flash(f"You have successfully unlisted Venue {venue.id}")
    finally:
        db.session.close()

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the
    # homepage
    return redirect(url_for("index"))


#  Artists
#  ----------------------------------------------------------------
@app.route("/artists")
def artists():
    # TODO: replace with real data returned from querying the database
    form = SearchByCityForm()
    data = db.session.query(Artist.id, Artist.name).all()
    return render_template("pages/artists.html", artists=data, form=form)


@app.route("/artists/search", methods=["POST"])
def search_artists():
    # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
    # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
    # search for "band" should return "The Wild Sax Band".
    search_term = request.form.get("search_term", "")
    query = Artist.query.filter(Artist.name.ilike(f"%{search_term}%")).all()
    count = Artist.query.filter(Artist.name.ilike(f"%{search_term}%")).count()
    response = {
        "count": count,
        "data": [{"id": item.id, "name": item.name} for item in query]
    }

    return render_template(
        "pages/search_artists.html",
        results=response,
        search_term=search_term,
    )


@app.route("/artists/search_by_city", methods=["POST"])
def search_artist_by_city():
    form = SearchByCityForm(request.form)
    state = form.state.data
    city = form.city.data
    print(state)
    print(city)
    query = Artist.query.filter(Artist.city == city, Artist.state == state).all()
    query_count = Artist.query.filter(Artist.city == city, Artist.state == state).count()
    search_term = f"{city}, {state}"
    response = {
        'count': query_count,
        "data": [
            {"id": item.id, "name": item.name} for item in query
        ]
    }
    return render_template(
        "pages/search_venues.html",
        results=response,
        search_term=search_term,
    )


@app.route("/artists/<int:artist_id>")
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    # TODO: replace with real artist data from the artist table, using
    # artist_id
    artist = Artist.query.get(artist_id)
    data = {"id": artist.id, "name": artist.name, "city": artist.city, "state": artist.state,
            "phone": artist.phone, "website": artist.website_link, "facebook_link": artist.facebook_link,
            "seeking_venue": artist.seeking_venue, "seeking_description": artist.seeking_description,
            "image_link": artist.image_link, "genres": [genre.name for genre in artist.genres], "past_shows": [],
            "upcoming_shows": [], "past_shows_count": artist.past_shows_count(),
            "upcoming_shows_count": artist.upcoming_shows_count(), "time_available_from" : artist.time_available_from,
            "time_available_to":artist.time_available_to}
    for show in artist.past_shows():
        show_detail = {
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "venue_image_link": show.venue.image_link,
            "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        }
        data["past_shows"].append(show_detail)

    for show in artist.upcoming_shows():
        show_detail = {
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "venue_image_link": show.venue.image_link,
            "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        }
        data["upcoming_shows"].append(show_detail)
    return render_template("pages/show_artist.html", artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route("/artists/<int:artist_id>/edit", methods=["GET"])
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.get(artist_id)
    # TODO: populate form with fields from artist with ID <artist_id>
    return render_template("forms/edit_artist.html", form=form, artist=artist)


@app.route("/artists/<int:artist_id>/edit", methods=["POST"])
def edit_artist_submission(artist_id):
    form = ArtistForm(request.form)
    artist = Artist.query.get(artist_id)
    if not artist:
        abort(404)
    try:
        artist.name = form.name.data
        artist.city = form.city.data
        artist.state = form.state.data
        artist.phone = form.phone.data
        artist.website_link = form.website_link.data
        artist.facebook_link = form.facebook_link.data
        artist.image_link = form.image_link.data
        artist.seeking_venue = form.seeking_venue.data
        artist.seeking_description = form.seeking_description.data
        artist.time_available_from = form.time_available_from.data
        artist.time_available_to = form.time_available_to.data
        if form.genres.data:
            genres = []
            for genre in form.genres.data:
                genre_instance = Genre.query.filter_by(name=genre).first()
                if genre_instance:
                    genres.append(genre_instance)
                else:
                    new_genre_instance = Genre(name=genre)
                    db.session.add(new_genre_instance)
                    genres.append(new_genre_instance)
            artist.genres = genres

        db.session.commit()
    except:
        print(sys.exc_info())
        db.session.rollback()
    finally:
        db.session.close()

    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    return redirect(url_for("show_artist", artist_id=artist_id))


@app.route("/venues/<int:venue_id>/edit", methods=["GET"])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.get(venue_id)
    # TODO: populate form with values from venue with ID <venue_id>
    return render_template("forms/edit_venue.html", form=form, venue=venue)


@app.route("/venues/<int:venue_id>/edit", methods=["POST"])
def edit_venue_submission(venue_id):
    form = VenueForm(request.form)
    venue = Venue.query.get(venue_id)
    if not venue:
        abort(404)
    try:
        venue.name = form.name.data
        venue.state = form.state.data
        venue.city = form.city.data
        venue.address = form.address.data
        venue.phone = form.phone.address.data
        venue.website_link = form.website_link.data
        venue.facebook_link = form.facebook_link.data
        venue.seeking_talent = form.seeking_talent.data
        venue.seeking_description = form.seeking_description.data
        venue.image_link = form.image_link.data

        genres = []
        for genre in form.genres.data:
            genre_instance = Genre.query.filter_by(name=genre).first()
            if genre_instance:
                genres.append(genre_instance)
            else:
                new_genre_instance = Genre(name=genre)
                genre.append(new_genre_instance)

        venue.genres = genres
        db.session.commit()

    except:
        print(sys.exc_info())
        db.session.rollback()
    finally:
        db.session.close()

    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    return redirect(url_for("show_venue", venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------


@app.route("/artists/create", methods=["GET"])
def create_artist_form():
    form = ArtistForm()
    return render_template("forms/new_artist.html", form=form)


@app.route("/artists/create", methods=["POST"])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    form = ArtistForm(request.form)

    try:
        new_artist = Artist(
            name=form.name.data,
            city=form.city.data,
            state=form.state.data,
            phone=form.phone.data,
            image_link=form.image_link.data,
            facebook_link=form.facebook_link.data,
            website_link=form.website_link.data,
            seeking_venue=form.seeking_venue.data,
            seeking_description=form.seeking_description.data,
            time_available_to=form.time_available_to.data,
            time_availbale_from=form.time_available_from.data,
        )
        genres = []
        for genre_name in form.genres.data:
            genre_instance = Genre.query.filter_by(name=genre_name).first()
            if genre_instance:
                genres.append(genre_instance)
            else:
                new_genre = Genre(name=genre_name)
                genres.append(new_genre)

        new_artist.genres.extend(genres)
        db.session.add(new_artist)
        db.session.commit()

    except:
        db.session.rollback()
        flash(f"An error occured. Artist {form.name.data} could not be listed.")
    else:
        # on successful db insert, flash success
        flash("Artist " + request.form["name"] + " was successfully listed!")
    finally:
        db.session.close()
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Artist ' + data.name + ' could not be
    # listed.')
    return render_template("pages/home.html")


#  Shows
#  ----------------------------------------------------------------


@app.route("/shows")
def shows():
    # displays list of shows at /shows
    # TODO: replace with real venues data.
    data = []
    # first = Show.query.first()
    # string = first.start_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    # print(string)
    for show in Show.query.all():
        show_info = {
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "artist_id" : show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": show.start_time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
        }
        data.append(show_info)
    return render_template("pages/shows.html", shows=data)


@app.route("/shows/create")
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template("forms/new_show.html", form=form)


@app.route("/shows/create", methods=["POST"])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    form = ShowForm(request.form)
    artist = Artist.query.get(form.artist_id.data)
    time = form.start_time.data.time()
    if not artist:
        abort(404)

    if artist.time_available_from > time or artist.time_available_to <= time:
        flash(f"Artist {artist.name} will not be available for the show")
        return redirect(url_for("create_shows"))

    try:
        new_show = Show(
            artist_id=form.artist_id.data,
            venue_id=form.venue_id.data,
            start_time=form.start_time.data
        )
        db.session.add(new_show)
        db.session.commit()
    except:
        print(sys.exc_info())
        db.session.rollback()
        flash("An error occurred. Show couldn't be listed.")
    # on successful db insert, flash success
    else:
        flash("Show was successfully listed!")
    # TODO: on unsuccessful db insert, flash an error instead.
    # e.g., flash('An error occurred. Show could not be listed.')
    # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
    return render_template("pages/home.html")


@app.errorhandler(404)
def not_found_error(error):
    return render_template("errors/404.html"), 404


@app.errorhandler(500)
def server_error(error):
    return render_template("errors/500.html"), 500


if not app.debug:
    file_handler = FileHandler("error.log")
    file_handler.setFormatter(Formatter(
        "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"))
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info("errors")

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == "__main__":
    app.run()

# Or specify port manually:
"""
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
"""
