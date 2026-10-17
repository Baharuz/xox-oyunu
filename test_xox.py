"""Three core scenarios. Run: python -m unittest -v test_xox.py"""
import unittest
from xox import Game, best_move, winning_line


class XOXTests(unittest.TestCase):
    def test_two_players_win_and_occupied_cell(self):
        game = Game(now=0)
        for index in (0, 3, 1, 4, 2):
            self.assertTrue(game.move(index, now=0))
        self.assertEqual(game.winner, "X")
        self.assertEqual(winning_line(game.board), (0, 1, 2))
        self.assertFalse(game.move(5, now=0))
        self.assertEqual(game.board[5], "")

    def test_computer_takes_immediate_win(self):
        board = ["O", "O", "", "X", "X", "", "", "", ""]
        self.assertEqual(best_move(board), 2)

    def test_fixed_clocks_timeout_and_reset(self):
        game = Game(timed=True, now=0)
        self.assertTrue(game.move(0, now=5))
        self.assertEqual(game.clock["X"], 55)
        self.assertFalse(game.move(0, now=6))
        self.assertEqual(game.clock["O"], 59)
        game.tick(now=65)
        self.assertEqual(game.winner, "X")
        self.assertEqual(game.clock["O"], 0)
        game.tick(now=100)
        self.assertEqual(game.clock, {"X": 55, "O": 0})
        self.assertFalse(game.move(1, now=100))
        fresh = Game(timed=True, now=100)
        self.assertEqual(fresh.clock, {"X": 60, "O": 60})


if __name__ == "__main__":
    unittest.main()

