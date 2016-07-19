#!/usr/bin/env python

"""main.py - This file contains handlers that are called by cronjobs."""
import datetime
import webapp2
from google.appengine.api import mail, app_identity

from models import User, Game
from google.appengine.ext import ndb


class SendReminderEmail(webapp2.RequestHandler):

    def get(self):
        """Send a reminder email to each User with an email who has
        unfinished games. Called every 24 hours using a cron job."""
        app_id = app_identity.get_application_id()
        day_ago = datetime.datetime.now() - datetime.timedelta(hours=24)
        users = User.query(User.email is not None)
        for user in users:
            games = Game.query(ndb.AND(Game.user == user.key,
                                       Game.game_over is False,
                                       Game.last_move < day_ago))
            if games.count == 0:
                continue

            subject = 'Reminder for unfinished Concentration game'
            body = 'Hi {}, you have an unfinished Concentration game.'.format(
                user.name)
            # This will send test emails, the arguments to send_mail are:
            # from, to, subject, body
            mail.send_mail('noreply@{}.appspotmail.com'.format(app_id),
                           user.email,
                           subject,
                           body)


app = webapp2.WSGIApplication([
    ('/crons/send_reminder', SendReminderEmail),
], debug=True)
