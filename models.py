"""models.py - This file contains the class definitions for the Datastore
entities used by the Game. Because these classes are also regular Python
classes they can include methods (such as 'to_form' and 'new_game')."""

import random
from datetime import date
from protorpc import messages
from google.appengine.ext import ndb


class User(ndb.Model):
    """User profile"""
    name = ndb.StringProperty(required=True)
    email = ndb.StringProperty()


class Game(ndb.Model):
    """Game object"""
    num_card_types = ndb.IntegerProperty(required=True)
    board = ndb.StringProperty(required=True)
    matched_cards = ndb.StringProperty(required=True)
    last_guessed_card_1 = ndb.IntegerProperty(required=False)
    last_guessed_card_2 = ndb.IntegerProperty(required=False)
    attempts = ndb.IntegerProperty(required=True)
    game_over = ndb.BooleanProperty(required=True, default=False)
    user = ndb.KeyProperty(required=True, kind='User')
    last_move = ndb.DateTimeProperty(auto_now=True)

    @classmethod
    def new_game(cls, user, num_card_types):
        """Creates and returns a new game"""
        if num_card_types not in range(2, 14):
            raise ValueError('Number of card types must be between 2 and 13')
        board = range(0, num_card_types) * 4
        random.shuffle(board)
        game = Game(user=user,
                    num_card_types=num_card_types,
                    board=str(board),
                    matched_cards='[]',
                    attempts=0,
                    game_over=False)
        game.put()
        return game

    def to_form(self, message):
        """Returns a GameForm representation of the Game. Only revealed cards
        and matched cards are revealed to the user."""
        form = GameForm()
        form.urlsafe_key = self.key.urlsafe()
        form.user_name = self.user.get().name
        form.attempts = self.attempts

        # Board field is a stringified python list object, so we evaluate it
        board = eval(self.board)
        # Hide the cards from the player
        board_view = list('X' * 4 * self.num_card_types)

        # Uncover the cards the player has already matched
        # Card values over 9 are represented by their hex value to ensure they
        # fit in one character.
        for card in eval(self.matched_cards):
            board_view[card] = hex(board[card])[2].upper()

        # Reveal the requested cards to the player and highlight them to
        # distinguish them from matched cards
        if self.last_guessed_card_1 is not None:
            card = hex(board[self.last_guessed_card_1])[2].upper()
            board_view[self.last_guessed_card_1] = "*%s*" % card
        if self.last_guessed_card_2 is not None:
            card = hex(board[self.last_guessed_card_2])[2].upper()
            board_view[self.last_guessed_card_2] = "*%s*" % card

        form.board = ''.join(board_view)
        form.game_over = self.game_over
        form.message = message
        return form

    def add_move_to_history(self, card_1, card_2, msg):
        """Adds a player's move to the game's history"""
        move = Move(game=self.key, move=str((card_1, card_2)), result=msg)
        move.put()

    def end_game(self, won=False):
        """Ends the game - if won is True, the player won. - if won is False,
        the player lost."""
        self.game_over = True
        self.put()
        # Add the game to the score 'board'
        score = Score(user=self.user,
                      date=date.today(),
                      guesses=self.attempts,
                      num_card_types=self.num_card_types)
        score.put()


class Score(ndb.Model):
    """Score object"""
    user = ndb.KeyProperty(required=True, kind='User')
    date = ndb.DateProperty(required=True)
    guesses = ndb.IntegerProperty(required=True)
    num_card_types = ndb.IntegerProperty(required=True)

    def to_form(self):
        return ScoreForm(user_name=self.user.get().name,
                         date=str(self.date),
                         guesses=self.guesses,
                         num_card_types=self.num_card_types)


class Move(ndb.Model):
    """Move object"""
    game = ndb.KeyProperty(required=True, kind='Game')
    created_at = ndb.DateTimeProperty(auto_now_add=True)
    move = ndb.StringProperty(required=True)
    result = ndb.StringProperty(required=True)

    def to_form(self):
        return HistoryForm(move=self.move, result=self.result)


class GameForm(messages.Message):
    """GameForm for outbound game state information"""
    urlsafe_key = messages.StringField(1, required=True)
    board = messages.StringField(2, required=True)
    attempts = messages.IntegerField(3, required=True)
    game_over = messages.BooleanField(4, required=True)
    message = messages.StringField(5, required=True)
    user_name = messages.StringField(6, required=True)


class GamesForm(messages.Message):
    """Return multiple GameForms"""
    items = messages.MessageField(GameForm, 1, repeated=True)


class NewGameForm(messages.Message):
    """Used to create a new game"""
    user_name = messages.StringField(1, required=True)
    num_card_types = messages.IntegerField(2, required=True)


class MakeMoveForm(messages.Message):
    """Used to make a move in an existing game"""
    guessed_card_1 = messages.IntegerField(1, required=True)
    guessed_card_2 = messages.IntegerField(2, required=True)


class PerformanceForm(messages.Message):
    """PerformanceForm for outbound user performance information"""
    user_name = messages.StringField(1, required=True)
    performance = messages.FloatField(2, required=True)


class PerformanceForms(messages.Message):
    """Return multiple PerformanceForms"""
    items = messages.MessageField(PerformanceForm, 1, repeated=True)


class ScoreForm(messages.Message):
    """ScoreForm for outbound Score information"""
    user_name = messages.StringField(1, required=True)
    date = messages.StringField(2, required=True)
    guesses = messages.IntegerField(3, required=True)
    num_card_types = messages.IntegerField(4, required=True)


class ScoreForms(messages.Message):
    """Return multiple ScoreForms"""
    items = messages.MessageField(ScoreForm, 1, repeated=True)


class HistoryForm(messages.Message):
    """HistoryForm for outbound game history information"""
    move = messages.StringField(1, required=True)
    result = messages.StringField(2, required=True)


class HistoryForms(messages.Message):
    """Return multiple HistoryForms"""
    items = messages.MessageField(HistoryForm, 1, repeated=True)


class StringMessage(messages.Message):
    """StringMessage-- outbound (single) string message"""
    message = messages.StringField(1, required=True)
