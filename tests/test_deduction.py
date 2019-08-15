"""Test functions for deductive logic component."""

import pytest

import deduction


@pytest.mark.deduce
def test_clue_count_advanced(board_advanced):
    """Check for correct clue count on advanced board.
    Given an advanced board,
    When setting up a Game object,
    Then 48 clues should be generated.
    """
    game = deduction.Game(board_advanced, 4)
    assert (len(game.clues)) == 48


@pytest.mark.deduce
def test_clue_count_basic(board_basic):
    """Check for correct clue count on basic board.
    Given a basic board,
    When setting up a Game object,
    Then 23 clues should be generated.
    """
    game = deduction.Game(board_basic, 4)
    assert (len(game.clues)) == 23


@pytest.mark.deduce
def test_random_plays(board_known):
    """Check that players can play pieces randomly
    Given a board where all Players know their clues,
    Have all players take turns playing two random false pieces.
    """
    board, clues, _ = board_known
    game = deduction.Game(board, 4, known_clues=clues)

    for player in game.players:
        assert player.known_clue is not None

    # Make random plays
    for _ in range(2):
        for player in game.players:
            player.play(False, "random")

    # Make random positive plays
    for player in game.players:
        player.play(True, "random")

    assert len([play for play in player.plays.negatives for player in game.players]) == 8
    assert len([play for play in player.plays.positives for player in game.players]) == 4
    assert len([clue for clue in player.clues for player in game.players]) < 97


@pytest.mark.deduce
def test_unique_solution_with_known_clues(board_known):
    """Check that Game.solutions returns the correct solution when all clues are known.
    Given a game with all known clues and a solution,
    When Game.solutions is called with all players in known_players,
    Then the return should be a list with the only element being the solution.
    """

    board, clues, solution = board_known
    game = deduction.Game(board, 4, known_clues=clues)

    assert game.solutions(0, 1, 2, 3)[0][:2] == solution


@pytest.mark.deduce
def test_solution_with_plays(game_with_plays):
    game = game_with_plays

    observer_solutions = game.solutions()

    assert len(set(observer_solutions)) < 100
    assert len(game.solutions(0)) < len(observer_solutions)
    assert len(game.solutions(0, 1, 2, 3)) == 1


@pytest.mark.deduce
def test_considered_play_better_than_random(board_known):
    """Check that optimized plays result in better outcomes than random ones."""

    board, clues, _ = board_known

    game1 = deduction.Game(board, 4, known_clues=clues)
    game2 = deduction.Game(board, 4, known_clues=clues)

    for _ in range(2):
        for player in game1.players:
            player.play(False, "random")

        for player in game2.players:
            player.play(False, "cluecount")

    observer1 = game1.solutions()
    observer2 = game2.solutions()

    assert len(observer1) < len(observer2)
