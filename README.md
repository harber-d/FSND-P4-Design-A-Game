## Set-Up Instructions:
1.  Update the value of application in app.yaml to the app ID you have registered
 in the App Engine admin console and would like to use to host your instance of this sample.
2.  Run the app with the devserver using dev_appserver.py DIR, and ensure it's
 running by visiting the API Explorer - by default localhost:8080/_ah/api/explorer.
3.  (Optional) Generate your client library(ies) with the endpoints tool.
 Deploy your application.
 

## Game Description:
Concentration is a simple player card matching game. The user begins a game and
is presented with a "board" of face-down cards denoted by the character "X". The
user may choose the size of the board and difficulty of the game by choosing the
 number of card types. The size of the board is four times the number of card 
types.

At each turn, the user chooses two cards to reveal from the board, denoted 
by asterisk characters (*) surrounding the cards. If the cards
are the same value, the user gets a match and the cards are permanently 
revealed on the board. If the cards don't match, the cards are hidden on the 
next turn. Once cards are matched, they cannot be matched or guessed again. 
The game ends when the user successfully matches every card on the board.

## Files Included:
 - api.py: Contains endpoints and game playing logic.
 - app.yaml: App configuration.
 - cron.yaml: Cronjob configuration.
 - main.py: Handler for taskqueue handler.
 - models.py: Entity and message definitions including helper methods.
 - utils.py: Helper function for retrieving ndb.Models by urlsafe Key string.

## Endpoints Included:
 - **create_user**
    - Path: 'user'
    - Method: POST
    - Parameters: user_name, email (optional)
    - Returns: Message confirming creation of the User.
    - Description: Creates a new User. user_name provided must be unique. Will 
    raise a ConflictException if a User with that user_name already exists.
    
 - **new_game**
    - Path: 'game'
    - Method: POST
    - Parameters: user_name, num_card_types
    - Returns: GameForm with initial game state.
    - Description: Creates a new Game. user_name provided must correspond to an
    existing user - will raise a NotFoundException if not. Num_card_types must
    be between 2 and 13.
     
 - **get_game**
    - Path: 'game/{urlsafe_game_key}'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: GameForm with current game state.
    - Description: Returns the current state of a game.
 
 - **get_game_history**
    - Path: 'game/{urlsafe_game_key}/history'
    - Method: GET
    - Parameters: urlsafe_game_key
    - Returns: HistoryForms with move history of the game.
    - Description: Return a game's move history.

 - **cancel_game**
    - Path: 'game/{urlsafe_game_key}/cancel'
    - Method: DELETE
    - Parameters: urlsafe_game_key
    - Returns: Message indicating the game has been canceled.
    - Description: Cancel an active game.

 - **get_user_games**
    - Path: 'games/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: GameForms with user's unfinished games.
    - Description: Returns all unfinished games of the given user.

 - **make_move**
    - Path: 'game/{urlsafe_game_key}'
    - Method: PUT
    - Parameters: urlsafe_game_key, guessed_card_1, guessed_card_2
    - Returns: GameForm with new game state.
    - Description: Accepts two cards. Returns a game state with message.
    If this causes a game to end, a corresponding Score entity will be created.
    
 - **get_scores**
    - Path: 'scores'
    - Method: GET
    - Parameters: None
    - Returns: ScoreForms.
    - Description: Returns all Scores in the database (unordered).
 
 - **get_high_scores**
    - Path: 'high_scores'
    - Method: GET
    - Parameters: num_card_types, number_of_results
    - Returns: ScoreForms.
    - Description: Returns the high scores for a given card type. Low scores
    are good for this game.
    
 - **get_user_performance**
    - Path: 'get_user_performance'
    - Method: GET
    - Parameters: None
    - Returns: PerformanceForms.
    - Description: Returns user performance rankings. High scores are good.
        
 - **get_user_scores**
    - Path: 'scores/user/{user_name}'
    - Method: GET
    - Parameters: user_name
    - Returns: ScoreForms. 
    - Description: Returns all Scores recorded by the provided player (unordered).
    Will raise a NotFoundException if the User does not exist.

## Models Included:
 - **User**
    - Stores unique user_name and (optional) email address.
    
 - **Game**
    - Stores unique game states. Associated with User model via KeyProperty.
    
 - **Score**
    - Records completed games. Associated with Users model via KeyProperty.

 - **Move**
    - Records game moves. Associated with Game model via KeyProperty.

## Forms Included:
 - **GameForm**
    - Representation of a Game's state (urlsafe_key, board, attempts,
    game_over flag, message, user_name).
 - **GamesForm**
    - Multiple GameForm container.
 - **NewGameForm**
    - Used to create a new game (user_name, num_card_types)
 - **MakeMoveForm**
    - Inbound make move form (guessed_card_1, guessed_card_2).
 - **PerformanceForm**
    - Representation of user performance information (user_name, performance)
 - **PerformanceForms**
    - Multiple PerformanceForm container.
 - **ScoreForm**
    - Representation of a completed game's Score (user_name, date, won flag,
    guesses).
 - **ScoreForms**
    - Multiple ScoreForm container.
 - **HistoryForm**
    - Representation of game move history information (move, result)
 - **HistoryForms**
    - Multiple HistoryForm container.    
 - **StringMessage**
    - General purpose String container.
