"""api.py - Contains logic for Concentration game.

Concentration is a simple player card matching game. The user begins a game and
is presented with a "board" of face-down cards denoted by the character "X".
The user may choose the size of the board and difficulty of the game by
choosing the number of card types. The size of the board is four times the
number of card types.

At each turn, the user chooses two cards to reveal from the board, denoted
by asterisk characters (*) surrounding the cards. If the cards
are the same value, the user gets a match and the cards are permanently
revealed on the board. If the cards don't match, the cards are hidden on the
next turn. Once cards are matched, they cannot be matched or guessed again.
The game ends when the user successfully matches every card on the board.

"""

from math import factorial
import logging
import endpoints
import datetime
from protorpc import remote, messages
from google.appengine.ext import ndb

from models import User, Game, Score, Move
from models import StringMessage, NewGameForm, GameForm, MakeMoveForm,\
    ScoreForms, GamesForm, HistoryForm, PerformanceForm, PerformanceForms,\
    HistoryForms
from utils import get_by_urlsafe


NEW_GAME_REQUEST = endpoints.ResourceContainer(NewGameForm)
GET_GAME_REQUEST = endpoints.ResourceContainer(
    urlsafe_game_key=messages.StringField(1),)
MAKE_MOVE_REQUEST = endpoints.ResourceContainer(
    MakeMoveForm,
    urlsafe_game_key=messages.StringField(1),)
USER_REQUEST = endpoints.ResourceContainer(user_name=messages.StringField(1),
                                           email=messages.StringField(2))
HIGH_SCORE_REQUEST = endpoints.ResourceContainer(
    num_card_types=messages.IntegerField(1),
    number_of_results=messages.IntegerField(2))


@endpoints.api(name='concentration', version='v1')
class ConcentrationAPI(remote.Service):
    """Game API"""
    @endpoints.method(request_message=USER_REQUEST,
                      response_message=StringMessage,
                      path='user',
                      name='create_user',
                      http_method='POST')
    def create_user(self, request):
        """Create a User. Requires a unique username.

        Args:
            user_name (str): The username.
            email (str): The e-mail address of the user.

        Returns:
            message (str): The game object containing the board.

        Raises:
            ConflictException: If username is not unique.
        """

        if User.query(User.name == request.user_name).get():
            raise endpoints.ConflictException(
                'A User with that name already exists!')
        user = User(name=request.user_name, email=request.email)
        user.put()
        return StringMessage(message='User {} created!'.format(
            request.user_name))

    @endpoints.method(request_message=NEW_GAME_REQUEST,
                      response_message=GameForm,
                      path='game',
                      name='new_game',
                      http_method='POST')
    def new_game(self, request):
        """Create new game for a user.

        Args:
            user_name (str): The username.
            num_card_types (int): The number of card types for the new game.

        Returns:
            game (Game): The representation of the Game instance.

        Raises:
            NotFoundException: If user_name is not found.
            BadRequestException: If num_card_types is not valid.
        """

        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                'A User with that name does not exist!')
        try:
            game = Game.new_game(user.key, request.num_card_types)
        except ValueError:
            raise endpoints.BadRequestException(
                'Number of card types must be between 2 and 13')

        return game.to_form(
            'Board size is %d cards ' % (game.num_card_types * 4) +
            '(0-%d). ' % (game.num_card_types * 4 - 1) +
            'Good luck playing Concentration!')

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='get_game',
                      http_method='GET')
    def get_game(self, request):
        """Return the current game state.

        Args:
            urlsafe_game_key (str): The game URL.

        Returns:
            game (Game): The representation of the Game instance.

        Raises:
            NotFoundException: If game does not exist.
        """

        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if game:
            if not game.game_over:
                return game.to_form('Time to make a move!')
            else:
                return game.to_form('Great job!')
        else:
            raise endpoints.NotFoundException('Game not found!')

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=HistoryForms,
                      path='game/{urlsafe_game_key}/history',
                      name='get_game_history',
                      http_method='GET')
    def get_game_history(self, request):
        """Return a game's move history.

        Args:
            urlsafe_game_key (str): The game URL.

        Returns:
            moves (Move[]): An array of Move instances containing the game's
                            move history.

        Raises:
            NotFoundException: If game does not exist.
        """

        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found!')
        moves = Move.query(Move.game == game.key).order(Move.created_at)
        return HistoryForms(items=[move.to_form() for move in moves])

    @endpoints.method(request_message=GET_GAME_REQUEST,
                      response_message=StringMessage,
                      path='game/{urlsafe_game_key}/cancel',
                      name='cancel_game',
                      http_method='DELETE')
    def cancel_game(self, request):
        """Cancel an active game.

        Args:
            urlsafe_game_key (str): The game URL.

        Returns:
            message(str): Cancel confirmation message.

        Raises:
            NotFoundException: If game does not exist.
            ForbiddenException: If the game is already over.
        """

        game = get_by_urlsafe(request.urlsafe_game_key, Game)
        if not game:
            raise endpoints.NotFoundException('Game not found!')
        elif game.game_over is True:
            raise endpoints.ForbiddenException('Game already over')
        else:
            game.key.delete()
            return StringMessage(message='Game canceled.')

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=GamesForm,
                      path='games/user/{user_name}',
                      name='get_user_games',
                      http_method='GET')
    def get_user_games(self, request):
        """Return all unfinished games of the given user.

        Args:
            user_name (str): The username.

        Returns:
            games(Game[]): An array of Game instances that are unfinished.

        Raises:
            NotFoundException: If no games are found for the user.
            NotFoundException: If user_name is not found.
        """

        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                'A User with that name does not exist!')
        games = Game.query(
            ndb.AND(Game.user == user.key, Game.game_over is False))
        if games.count() == 0:
            raise endpoints.NotFoundException(
                'No games found for that user.')
        return GamesForm(items=[game.to_form('') for game in games])

    @endpoints.method(request_message=MAKE_MOVE_REQUEST,
                      response_message=GameForm,
                      path='game/{urlsafe_game_key}',
                      name='make_move',
                      http_method='PUT')
    def make_move(self, request):
        """Makes a move. Returns a game state with message.

        Args:
            urlsafe_game_key (str): The game URL.
            guessed_card_1 (int): First of two cards the user is uncovering.
            guessed_card_2 (int): Second of two cards the user is uncovering.

        Returns:
            game (Game): The representation of the Game instance.
        """

        game = get_by_urlsafe(request.urlsafe_game_key, Game)

        if game.game_over:
            return game.to_form('Game already over!')

        rng = range(game.num_card_types * 4)
        if (request.guessed_card_1 not in rng or
                request.guessed_card_2 not in rng):
            msg = 'Invalid card chosen: card number must be from 0 to %d.' %\
                  game.num_card_types * 4 - 1
            game.add_move_to_history(
                request.guessed_card_1, request.guessed_card_2, msg)
            game.put()
            return game.to_form(msg)
        if (request.guessed_card_1 in eval(game.matched_cards) or
                request.guessed_card_2 in eval(game.matched_cards)):
            msg = 'One of the cards you selected has already been matched.'
            game.add_move_to_history(
                request.guessed_card_1, request.guessed_card_2, msg)
            game.put()
            return game.to_form(msg)

        game.attempts += 1
        if (eval(game.board)[request.guessed_card_1] ==
                eval(game.board)[request.guessed_card_2]):
            msg = 'You got a match!'
            matched_cards = eval(game.matched_cards)
            matched_cards.append(request.guessed_card_1)
            matched_cards.append(request.guessed_card_2)
            game.matched_cards = str(matched_cards)

            if len(eval(game.matched_cards)) == game.num_card_types * 4:
                msg += ' You win!'
                game.end_game(True)
        else:
            msg = 'Try again.'

        game.last_guessed_card_1 = request.guessed_card_1
        game.last_guessed_card_2 = request.guessed_card_2
        game.add_move_to_history(
            request.guessed_card_1, request.guessed_card_2, msg)
        game.put()
        return game.to_form(msg)

    @endpoints.method(response_message=ScoreForms,
                      path='scores',
                      name='get_scores',
                      http_method='GET')
    def get_scores(self, request):
        """Return all scores for all users.

        Returns:
            scores(Score[]): An array of Score instances.
        """
        return ScoreForms(items=[score.to_form() for score in Score.query()])

    @endpoints.method(request_message=HIGH_SCORE_REQUEST,
                      response_message=ScoreForms,
                      path='high_scores',
                      name='get_high_scores',
                      http_method='GET')
    def get_high_scores(self, request):
        """Return the high scores for a given card type. Low scores are good
        for Concentration

        A "high score" is the fewest number of guesses required to match all of
        the cards, so this method returns Score instances by the number of
        guesses in ascending order. Because scores can't be compared across
        board sizes, the number of card types is a required argument.

        Args:
            num_card_types (int): The number of card types.
            number_of_results (int): The number of results to return.

        Returns:
            scores(Score[]): An array of Score instances sorted by guesses.

        Raises:
            BadRequestException: If num_card_types is not between 2 and 13, or
                                 if number_of_results is not greater than zero.
        """

        if request.num_card_types not in range(2, 14):
            raise endpoints.BadRequestException(
                'Number of card types must be between 2 and 13')
        if request.number_of_results < 1:
            raise endpoints.BadRequestException(
                'Number of results must be greater than zero.')

        scores = Score.query(Score.num_card_types ==
                             request.num_card_types).order(
            Score.guesses).fetch(
            limit=request.number_of_results)
        return ScoreForms(items=[score.to_form() for score in scores])

    @endpoints.method(response_message=PerformanceForms,
                      path='user_performance',
                      name='get_user_performance',
                      http_method='GET')
    def get_user_performance(self, request):
        """Returns user performance rankings. High scores are good.

        The performance score is calculated by using the combinations formula
        (nCr) to calculate the total number of possible card combinations,
        divided by the number of attempts made by the user. This ensures that
        users with bigger boards are rewarded appropriately.

        Returns:
            performances: An array of usernames sorted by performance scores.
        """

        f = factorial
        users = User.query()
        rankings = []
        for user in users:
            games = Game.query(
                ndb.AND(Game.user == user.key, Game.game_over is True))
            if games.count() == 0:
                # don't consider user if has no games
                continue
            performance = 0.0
            for game in games:
                # determine possible move combinations (nCr)
                # based on number of cards
                total_possible_combos = f(
                    game.num_card_types * 4) / f(2) /\
                    f(game.num_card_types * 4 - 2)
                # games with bigger boards are awarded higher scores
                performance += total_possible_combos / float(game.attempts)
            performance /= games.count()
            rankings.append((user.name, performance))
        # sort players using the performance scores computed above
        sorted(rankings, key=lambda ranking: ranking[1])
        return PerformanceForms(
            items=[PerformanceForm(
                   user_name=ranking[0],
                   performance=ranking[1]) for ranking in rankings])

    @endpoints.method(request_message=USER_REQUEST,
                      response_message=ScoreForms,
                      path='scores/user/{user_name}',
                      name='get_user_scores',
                      http_method='GET')
    def get_user_scores(self, request):
        """Return all of an individual user's scores.

        Args:
            user_name (str): The username.

        Returns:
            scores(Score[]): An array of Score instances.

        Raises:
            NotFoundException: If user_name is not found.
        """

        user = User.query(User.name == request.user_name).get()
        if not user:
            raise endpoints.NotFoundException(
                'A User with that name does not exist!')
        scores = Score.query(Score.user == user.key)
        return ScoreForms(items=[score.to_form() for score in scores])


api = endpoints.api_server([ConcentrationAPI])
