import random
from pynput import keyboard
import os
import typing
import time
import sys

class Game2048:
    """Class describing a game of 2048
    
    Methods:
    self.public_move(direction: int) - Makes a move in the said direction
    self.restart() Restarts the game
    self.undo() - Undoes the last move if supported
    self.swap() - Swaps two tiles if supported
    self.delete() - Deletes all tiles with that number if supported
    """
    def __str__(self)-> str:
        """Return a string representation of the board and statistics"""
        additional_info: str = ""
        if abs(self.game_state) == 2:
            additional_info = " (GAME WON)"
        elif abs(self.game_state) == 3:
            additional_info = " (CUSTOM GRID USED)"
        secondary_add_info = ""
        if self.powerups:
            secondary_add_info = f" Powerups used: {self.powerups_used}"
        if self.practice:
            secondary_add_info += " (PRACTICE MODE)"
        result: str = f"Score: {self.score}, Moves: {self.moves}{secondary_add_info}{additional_info}"
        max_character_lengths: list[int] = []
        for i in zip(*self.grid):
            max_character_lengths.append(len(self.tiles[max(i)]))
        for i in self.grid:
            result += "\n"
            first: bool = True
            for k in range(len(i)):
                j: int = i[k]
                column_max_length: int = max_character_lengths[k]
                tile_string: str = self.tiles[j]
                padded_length: int = column_max_length - len(tile_string)
                front_padding: int = padded_length//2 + 1
                back_padding: int = front_padding + padded_length%2
                if k == len(i) - 1:
                    back_padding = 0
                tile_string: str = " "*front_padding + tile_string + " "*back_padding
                if first:
                    first = False
                else:
                    tile_string = "|" + tile_string
                result += tile_string
        if self.powerups:
            result += f"\nUndos left: {self.undos_left}, swaps left: {self.swaps_left}, deletes left: {self.deletes_left}"
        if self.game_state < 0:
            result += "\nGAME OVER,"
            playtime: int = int(self.lose_time - self.start_time)
            playtime_hours: int = playtime // 3600
            playtime_minutes: int = (playtime%3600) // 60
            playtime_seconds: int = playtime % 60
            playtime_string: str = ""
            add_padding_zero = lambda number, next_one_padded: "0" + str(number) if len(str(number)) == 1 and next_one_padded else str(number)
            next_one_padded: bool = False
            if playtime_hours != 0:
                playtime_string += str(playtime_hours) + " hours "
                next_one_padded = True
            if playtime_minutes != 0 or next_one_padded:
                playtime_string += add_padding_zero(playtime_minutes, next_one_padded) + " minutes "
                next_one_padded = True
            if playtime_seconds != 0 or next_one_padded:
                playtime_string += add_padding_zero(playtime_seconds, next_one_padded) + " seconds "

            result += f" PLAYTIME: {playtime_string}"

        return result

    def _spawn(self)-> typing.Literal[-1, 1, 2]:
        """Spawn a 2 or 4 tile at random empty position of the grid"""
        flattened_grid: typing.List[int] = []
        for i in self.grid:
            flattened_grid.extend(i)
        
        empty_spots: int = flattened_grid.count(0)
        if empty_spots == 0:
            return -1
        
        new_spot: int = (empty_spots * random.random()).__floor__()
        i: int = 0
        chosen_level: int
        if random.random() > 0.9:
            chosen_level = 2
        else:
            chosen_level = 1
        for k in range(len(flattened_grid)):
            j = flattened_grid[k]
            if j == 0 and i == new_spot:
                flattened_grid[k] = chosen_level
                break
            elif j == 0:
                i += 1
        
        self.grid = [flattened_grid[i:i+4] for i in range(0, 16, 4)]
        return chosen_level
    
    def _move(self, direction: int, check_only: bool = False)-> typing.Literal[-1, 0, 1, 2]:
        """Do a raw move in any direction
        
        Parameters:

            direction = an integer, 0 means left, going up by 1 rotates the direction by 90 degrees clockwise

            check_only = a boolean, denoting if the move should change the board and statistics, used by _check method
        """
        #left - 0, up - 1, right - 2, down - 3
        direction %= 4
        rotated_grid = self.grid.copy()
        for i in range(direction):
            rotated_grid = list(map(list, zip(*rotated_grid)))[::-1]

        empty_available: bool = False
        definitely_changed: bool = False
        new_tiles: typing.List[str] = self.tiles.copy()
        new_score = self.score
        new_rotated_grid: typing.List[typing.List[int]] = []
        for row_index in range(4):
            row = rotated_grid[row_index].copy()
            if row.count(0) != 0:
                empty_available = True
            non_empty_seen: bool = False
            for i in row[::-1]:
                if i != 0:
                    non_empty_seen = True
                elif non_empty_seen:
                    definitely_changed = True
            for i in range(row.count(0)):
                row.remove(0)

            new_row: typing.List[int] = []
            next_tile_used: bool = False
            for tile_index in range(len(row)):
                tile = row[tile_index]
                if tile_index == len(row) - 1:
                    next_tile = 0
                else:
                    next_tile = row[tile_index + 1]
                if next_tile == tile and not next_tile_used:
                    new_row.append(tile + 1)
                    while tile + 1 >= len(new_tiles):
                        new_tiles.append(str(2*int(new_tiles[-1])))
                    new_score += int(new_tiles[tile + 1])
                    if tile == 6 and not self.practice:
                        self.undos_left = min(self.undos_left + 1, 2)
                    elif tile == 7:
                        self.swaps_left = min(self.swaps_left + 1, 2)
                    elif tile == 8:
                        self.deletes_left = min(self.deletes_left + 1, 2)
                    next_tile_used = True
                    empty_available = True
                    definitely_changed = True
                elif not next_tile_used:
                    new_row.append(tile)
                else:
                    next_tile_used = False

            for i in range(4 - len(new_row)):
                new_row.append(0)
            new_rotated_grid.append(new_row)

        if not empty_available:
            return -1
        elif check_only or not definitely_changed:
            return 0
        else:
            for i in range(direction):
                new_rotated_grid = list(map(list, zip(*new_rotated_grid[::-1])))
            self.grid = new_rotated_grid
            self.tiles = new_tiles
            self.score = new_score
            self.moves += 1
            spawn_level: typing.Literal[-1, 1, 2] = self._spawn()
            self.moves_list.append(self.last_move)
            self.last_move = (self.grid.copy(), self.score, self.game_state)
            if len(self.moves_list) > self.moves_limit + 1:
                self.moves_list.pop(0)
            return spawn_level

    def _check(self, check_argument: typing.Literal[-1, 0, 1, 2])-> typing.Literal[-3, -2, -1, 1, 2, 3]:
        """Check the game_state and update accordingly in case"""
        if check_argument != -1:
            max_number: int = 0
            for row in self.grid:
                for tile in row:
                    if tile > max_number:
                        max_number = tile
            if max_number == 11:
                self.game_state = 1
        else:
            move_found: bool = False
            for i in range(4):
                if self._move(i, True) != -1:
                    move_found = True
                    break
            if not move_found:
                self.game_state *= -1
                self.lose_time = time.time()
        return self.game_state

    def public_move(self, direction: int)-> bool:
        """Make a move in the game of 2048 in any direction
        
        Parameters:

            direction = an integer, 0 means left, going up by 1 rotates the direction by 90 degrees clockwise
        """
        if self.game_state == -1:
            return False
        self._check(self._move(direction))
        return True

    def undo(self)-> typing.Literal[-2, -1, 0]:
        "Undo a move in the game of 2048"
        if self.undos_left == 0:
            return -1
        elif len(self.moves_list) <= 1:
            return -2
        
        new_game_position: typing.Tuple[typing.List[typing.List[int]], int, typing.Literal[-2, -1, 1, 2]] = self.moves_list.pop()
        self.grid = new_game_position[0]
        self.score = new_game_position[1]
        self.game_state = new_game_position[2]
        self.undos_left = max(self.undos_left - 1, -1)
        self.powerups_used += 1
        self.last_move = new_game_position
        return 0

    def restart(self, *, custom_grid: typing.List[typing.List[int]] | None = None, powerup_mode: typing.Literal[0, 1, 2] | None = None):
        """Sets all the main variables, is used by __init__
        
        Parameters:

            custom_grid = a 2D 4x4 list of integers, corresponding to the board the game will start with

            powerup_mode = 0 (default) disables any powerups, 1 enables them and 2 starts the game with practice mode"""
        self.start_time: float = time.time()
        self.grid: typing.List[typing.List[int]]
        self.custom_grid: bool
        self.original_grid: typing.List[typing.List[int]]
        if hasattr(self, "original_grid") and custom_grid is None:
            self.grid = self.original_grid
        elif custom_grid is None:
            self.grid = [[0]*4] * 4
            self.original_grid = [[0]*4] * 4
            self.custom_grid = False
        else:
            self.grid: typing.List[typing.List[int]] = custom_grid.copy()
            self.original_grid = custom_grid.copy()
            self.custom_grid = True

        self.game_state: typing.Literal[-2, -1, 1, 2] = 1
        self.tiles: typing.List[str] = ["", "2", "4"]
        self.score: int = 0
        self.moves: int = 0
        self._spawn()
        self._spawn()
        max_number: int = 0
        for row in self.grid:
            for tile in row:
                if tile > max_number:
                    max_number = tile
        while max_number >= len(self.tiles):
            self.tiles.append(str(2*int(self.tiles[-1])))

        if hasattr(self, "powerup_mode") and powerup_mode is None:
            powerup_mode = self.powerup_mode
        elif powerup_mode is None:
            self.powerup_mode = 0
            powerup_mode = 0
        else:
            self.powerup_mode = powerup_mode
        self.practice = bool(powerup_mode // 2)
        self.powerups = bool(round(powerup_mode/2 + 0.3))
        self.powerups_used: int = 0
        if self.powerups:
            self.undos_left: int = 2
            self.swaps_left: int = 1
            self.deletes_left: int = 0
            self.moves_limit: int = 1
        else:
            self.undos_left: int = 0
            self.swaps_left: int = 0
            self.deletes_left: int = 0
            self.moves_limit: int = 0
        if self.practice:
            self.undos_left: int = -1
            self.moves_limit: int = 128
        self.moves_list: typing.List[typing.Tuple[typing.List[typing.List[int]], int, typing.Literal[-2, -1, 1, 2]]] = [(self.grid.copy(), self.score, self.game_state)]
        self.last_move: typing.Tuple[typing.List[typing.List[int]], int, typing.Literal[-2, -1, 1, 2]] = (self.grid.copy(), self.score, self.game_state)
        self.lose_time: float = -1.0

    def __init__(self, *, custom_grid: typing.List[typing.List[int]] | None = None, powerup_mode: typing.Literal[0, 1, 2] | None = None):
        """Create a new game of 2048 object, its parameters are same self.restart() method"""
        self.restart(custom_grid = custom_grid, powerup_mode = powerup_mode)


def refresh(game_object: Game2048):
    """Clear the command line and reprint a board of 2048"""
    (lambda : os.system("cls") if os.name == "nt" else os.system("clear"))()
    print(str(game_object))

def restart(game_object: Game2048):
    """Restart a game of 2048 and refresh the screen"""
    game_object.restart()
    refresh(game_object)

def move(game_object: Game2048, direction: int):
    """Do a move in a game of 2048 and refresh the screen
    
    Parameters:

        direction = an integer, 0 means left, going up by 1 rotates the direction by 90 degrees clockwise
    """
    game_object.public_move(direction)
    refresh(game_object)

def undo(game_object: Game2048):
    """Undo a move in a game of 2048 and refresh the screen"""
    result: typing.Literal[-2, -1, 0] = game_object.undo()
    refresh(game_object)
    if result == 0:
        print("Last move undone")
    elif result == -1:
        print("You don't have any uses left, make 128 tiles to get more uses")
    elif result == -2:
        print("There is no move you can undo")


def set_list_false(changed_list: typing.List[bool]):
    changed_list.append(False)

def main(args: typing.List[str] = [""]):
    """Start the game of 2048 with keybinds on"""
    if len(args) > 1:
        start_input: str = args[1]
    else:
        print("By pressing enter, you agree that the terminal will be cleared and that the game of 2048 will start.")
        print("Controls are WASD or arrow keys, Q to quit and R to restart.")
        print("Write p to enable power ups (controlled by pressing SHIFT + U, S and T respectively) and add + at the end of the string to start in practice mode (unlimited undo's).")
        print("Practice mode is impossible to enable without powerups. Write any invalid string and enter to avoid starting the game: ", end = "")
        start_input: str = input()
    if start_input == "":
        mode: int = 0
    elif start_input == "p":
        mode: int = 1
    elif start_input == "p+":
        mode: int = 2
    else:
        mode: int = -1
    if mode >= 0:
        condition = [True]
        game = Game2048(powerup_mode = mode)
        restart(game)
        keybinds: typing.Dict[str, typing.Callable] = {
            "w": lambda: move(game, 1),
            "s": lambda: move(game, 3),
            "a": lambda: move(game, 0),
            "d": lambda: move(game, 2),
            "<up>": lambda: move(game, 1),
            "<down>": lambda: move(game, 3),
            "<left>": lambda: move(game, 0),
            "<right>": lambda: move(game, 2),
            "r": lambda: restart(game),
            "q": lambda: set_list_false(condition)
        }
        if game.powerups:
            keybinds["<shift>+u"] = lambda: undo(game)
        listener = keyboard.GlobalHotKeys(keybinds)
        listener.start()
        while condition[-1]:
            time.sleep(1)
        quit()

if __name__ == "__main__":
    main(sys.argv)