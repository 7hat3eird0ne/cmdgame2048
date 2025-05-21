import random
from pynput import keyboard
import os
import copy
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
        max_character_lengths: typing.List[int] = [len(self.tiles[max(column)]) for column in zip(*self.grid)]
        for row in self.grid:
            result += "\n"
            first: bool = True
            for tile, tile_index, column_max_length in zip(row, range(len(row)), max_character_lengths):
                tile_string: str = self.tiles[tile]
                padded_length: int = column_max_length - len(tile_string)
                front_padding: int = padded_length//2 + 1
                back_padding: int = front_padding + padded_length%2
                if tile_index == len(row) - 1:
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

    def _snapshot(self):
        self.moves_list.append((copy.deepcopy(self.grid), self.score, (self.swaps_left, self.deletes_left)))
        if len(self.moves_list) > self.moves_limit:
            self.moves_list.pop(0)

    def _spawn(self)-> typing.Literal[-1, 1, 2]:
        """Spawn a 2 or 4 tile at random empty position of the grid"""
        flattened_grid: typing.List[int] = []
        for row in self.grid:
            flattened_grid.extend(row)
        
        empty_spots: int = flattened_grid.count(0)
        if empty_spots == 0:
            return -1
        
        new_spot: int = (empty_spots * random.random()).__floor__()
        chosen_level: int
        if random.random() > 0.9:
            chosen_level = 2
        else:
            chosen_level = 1
        current_spot: int = 0
        for tile_index, tile in enumerate(flattened_grid):
            if tile == 0 and current_spot == new_spot:
                flattened_grid[tile_index] = chosen_level
                break
            elif tile == 0:
                current_spot += 1
        
        self.grid = [flattened_grid[row_start_index:row_start_index + 4] for row_start_index in range(0, len(flattened_grid), len(self.grid))]
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
        for row_index, row in enumerate(copy.deepcopy(rotated_grid)):
            if row.count(0) != 0:
                empty_available = True
            non_empty_seen: bool = False
            for tile in row[::-1]:
                if tile != 0:
                    non_empty_seen = True
                elif non_empty_seen:
                    definitely_changed = True
            for tile in range(row.count(0)):
                row.remove(0)

            new_row: typing.List[int] = []
            next_tile_used: bool = False
            for tile_index, tile in enumerate(row):
                if tile_index == len(row) - 1:
                    next_tile = 0
                else:
                    next_tile = row[tile_index + 1]
                if next_tile == tile and not next_tile_used:
                    new_row.append(tile + 1)
                    while tile + 1 >= len(new_tiles):
                        new_tiles.append(str(2*int(new_tiles[-1])))
                    new_score += int(new_tiles[tile + 1])
                    if self.powerups:
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

            new_row.extend([0] * (len(self.grid[0]) - len(new_row)))
            new_rotated_grid.append(new_row)

        if not empty_available:
            return -1
        elif check_only or not definitely_changed:
            return 0
        else:
            for i in range(direction):
                new_rotated_grid = list(map(list, zip(*new_rotated_grid[::-1])))
            self._snapshot()
            self.grid = new_rotated_grid
            self.tiles = new_tiles
            self.score = new_score
            self.moves += 1
            spawn_level: typing.Literal[-1, 1, 2] = self._spawn()
            return spawn_level

    def _check(self)-> typing.Literal[-3, -2, -1, 1, 2, 3]:
        """Check the game_state and update accordingly in case"""
        max_number: int = max([max(row) for row in self.grid])
        if max_number == 11 and abs(self.game_state) == 1:
            self.game_state *= 2

        for direction in range(4):
            if self._move(direction, True) != -1:
                break
        else:
            self.game_state *= -1
            self.lose_time = time.time()
            return self.game_state
        self.game_state = abs(self.game_state)
        return self.game_state

    def public_move(self, direction: int)-> bool:
        """Make a move in any direction
        
        Parameters:

            direction = an integer, 0 means left, going up by 1 rotates the direction by 90 degrees clockwise
        """
        if self.game_state < 0:
            return False
        self._move(direction)
        self._check()
        return True

    def undo(self)-> typing.Literal[-2, -1, 0]:
        "Undo a move"
        if self.undos_left == 0:
            return -1
        elif len(self.moves_list) == 0:
            return -2
        
        new_game_position: typing.Tuple[typing.List[typing.List[int]], int] = self.moves_list.pop()
        self.grid = new_game_position[0]
        self.score = new_game_position[1]
        self.undos_left = max(self.undos_left - 1, -1)
        self.swaps_left = new_game_position[2][0]
        self.deletes_left = new_game_position[2][1]
        self.powerups_used += 1

        self._check()
        return 0

    def swap(self, coord_1: typing.List[int], coord_2: typing.List[int])-> typing.Literal[-2, -1, 0]:
        """Swap two tiles"""
        if self.swaps_left == 0:
            return -1
        if self.get_tile(coord_1) == 0 or self.get_tile(coord_2) == 0 or self.get_tile(coord_1) == self.get_tile(coord_2):
            return -2

        self._snapshot()
        coord_1_tile: int = self.get_tile(coord_1)
        coord_2_tile: int = self.get_tile(coord_2)
        self.grid[coord_1[1]][coord_1[0]] = coord_2_tile
        self.grid[coord_2[1]][coord_2[0]] = coord_1_tile
        self.swaps_left = max(self.swaps_left - 1, -1)
        self.powerups_used += 1
        self.moves += 1

        self._check()
        return 0
    
    def delete(self, coordinates: typing.List[int])-> typing.Literal[-2, -1, 0]:
        """Delete all tiles with the number of the tile on the coordinates"""
        if self.deletes_left == 0:
            return -1
        if self.get_tile(coordinates) == 0:
            return -2
        
        self._snapshot()
        deleted_number = self.get_tile(coordinates)
        new_grid = [[0 if tile == deleted_number else tile for tile in enumerate(row)] for row in self.grid]
        self.grid = new_grid
        self.deletes_left = max(self.deletes_left - 1, -1)
        self.powerups_used += 1
        self.moves += 1

        self._check()
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

        max_number: int = max([max(row) for row in self.grid])
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
        self._check()
        self.moves_list: typing.List[typing.Tuple[typing.List[typing.List[int]], int, typing.Tuple[int, int]]] = []
        self.lose_time: float = -1.0
        self.get_tile = lambda coords: self.grid[coords[1]][coords[0]]

    def __init__(self, *, custom_grid: typing.List[typing.List[int]] | None = None, powerup_mode: typing.Literal[0, 1, 2] | None = None):
        """Create a new Game2048 object, its parameters are same self.restart() method"""
        self.restart(custom_grid = custom_grid, powerup_mode = powerup_mode)


def refresh(game_object: Game2048):
    """Clear the command line and reprint the board"""
    os.system("cls" if os.name == "nt" else "clear")
    print(str(game_object))

def set_mode(game_object: Game2048, move_mode: typing.List[int], target_mode: int, coordinates: typing.List[int], coordinates_list: typing.List[typing.List[int]]):
    move_mode.append(target_mode)
    for i in range(max(game_object.grid, game_object.grid[0])):
        move_coordinates(game_object, coordinates, 0)
        move_coordinates(game_object, coordinates, 1)
    refresh(game_object)
    if move_mode[-1] == 1:
        move_coordinates(game_object, coordinates, 0)
        print("Entered swap selection")
    elif move_mode[-1] == 2:
        move_coordinates(game_object, coordinates, 0)
        print("Entered deletion selection")
    else:
        print("Exitted tile selection")

    while len(coordinates) != 0:
        coordinates.pop()
    coordinates.extend([0,0])
    while len(coordinates_list) != 0:
        coordinates_list.pop()

def move_coordinates(game_object: Game2048, coordinates: typing.List[int], direction: int):
    """Move coordinates by 1 in the direction and refresh the screen"""
    convert_coordinates_str = lambda coords: f"{coords[1] + 1}{["A", "B", "C", "D"][coords[0]]}"
    direction %= 4
    if direction == 0:
        coordinates[0] -= 1
    elif direction == 1:
        coordinates[1] -= 1
    elif direction == 2:
        coordinates[0] += 1
    else:
        coordinates[1] += 1

    coordinates[0] = min(3, coordinates[0])
    coordinates[1] = min(3, coordinates[1])
    coordinates[0] = max(0, coordinates[0])
    coordinates[1] = max(0, coordinates[1])

    refresh(game_object)
    print(f"Current coordinates (1A is top left and 1D is top right): {convert_coordinates_str(coordinates)}")

def select_coordinates(game_object: Game2048, coordinates_list: typing.List[typing.List[int]], coordinates: typing.List[int]):
    """Put coordinates into the coordinates_list and refreshes the screen"""
    convert_coordinates_str = lambda coords: f"{coords[1] + 1}{["A", "B", "C", "D"][coords[0]]}"
    coordinates_list.append(coordinates.copy())
    
    refresh(game_object)
    print(f"Selected {convert_coordinates_str(coordinates)}")

def submit_coordinates(game_object: Game2048, func: typing.Callable, coordinates_list: typing.List[typing.List[int]], move_mode: int):
    """Swap or delete tiles determined by func, coordinates_list and coordinates"""
    function_name: str
    function_requirement: str
    function_name_past: str
    if func == game_object.swap:
        function_name = "swap"
        function_requirement = "256"
        function_name_past = "swapped"
    elif func == game_object.delete:
        function_name = "delete"
        function_requirement = "512"
        function_name_past = "deleted"
    result = func(*coordinates_list)
    set_mode(game_object, move_mode, 0, [0, 0], coordinates_list)
    refresh(game_object)
    if result == 0:
        print(f"Tiles successfully {function_name_past}")
    if result == -1:
        print(f"You don't have any uses left, make {function_requirement} tiles to get more uses")
    elif result == -2:
        print(f"Failed to {function_name}")

def restart(game_object: Game2048):
    """Restart the game and refresh the screen"""
    game_object.restart()
    refresh(game_object)

def move(game_object: Game2048, direction: int):
    """Do a move in the game and refresh the screen
    
    Parameters:

        direction = an integer, 0 means left, going up by 1 rotates the direction by 90 degrees clockwise
    """
    game_object.public_move(direction)
    refresh(game_object)

def undo(game_object: Game2048):
    """Undo a move in the game and refresh the screen"""
    result: typing.Literal[-2, -1, 0] = game_object.undo()
    refresh(game_object)
    if result == 0:
        print("Last move undone")
    elif result == -1:
        print("You don't have any uses left, make 128 tiles to get more uses")
    elif result == -2:
        print("There is no move you can undo")

def start_pause(confirm_await_list):
    confirm_await_list[0] = True
    print("Waiting for ESC press to pause")

def confirm_pause(game_object: Game2048, paused_list: typing.List[bool], confirm_await_list: typing.List[bool], move_mode: typing.List[int], coordinates: typing.List[int]):
    paused_list[0] = not paused_list[0]
    confirm_await_list[0] = False
    refresh(game_object)
    if paused_list[0]:
        print("\nCURRENTLY PAUSED")
    elif move_mode[0] != 0:
        if coordinates[1] != 0:
            move_coordinates(game_object, coordinates, 1)
            move_coordinates(game_object, coordinates, 3)
        else:
            move_coordinates(game_object, coordinates, 3)
            move_coordinates(game_object, coordinates, 1)

def main(args: typing.List[str] = [""]):
    """Start the game of 2048 with keybinds, reacts to keys being pressed even when out of focus"""
    if len(args) > 1:
        start_input: str = args[1]
    else:
        print("By pressing enter, you agree that the terminal will be cleared and that the game of 2048 will start.")
        print("The game will react to key presses even when it is not in focus. Press SPACE and ESC right after to pause and unpause when unfocusing the window temporarily.")
        print("Controls are WASD or arrow keys, ESC to quit and ENTER to restart.")
        print("Write p to enable power ups (controlled by pressing SHIFT + U, I and O respectively) and add + at the end of the string to start in practice mode (unlimited undo's).")
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
        move_mode: typing.List[int] = [0]
        paused_list: typing.List[bool] = [False]
        confirm_await_list: typing.List[bool] = [False]
        coordinates: typing.List[int] = [0, 0]
        coordinates_list: typing.List[typing.List[int]] = []
        condition: typing.List[bool] = [True]
        game: Game2048 = Game2048(powerup_mode = mode)
        restart(game)
        keybinds: typing.Dict[str, typing.Callable] = {
            "w": lambda: (move(game, 1) if move_mode[-1] == 0 else move_coordinates(game, coordinates, 1)) if not paused_list[0] else None,
            "s": lambda: (move(game, 3) if move_mode[-1] == 0 else move_coordinates(game, coordinates, 3)) if not paused_list[0] else None,
            "a": lambda: (move(game, 0) if move_mode[-1] == 0 else move_coordinates(game, coordinates, 0)) if not paused_list[0] else None,
            "d": lambda: (move(game, 2) if move_mode[-1] == 0 else move_coordinates(game, coordinates, 2)) if not paused_list[0] else None,
            "<up>": lambda: (move(game, 1) if move_mode[-1] == 0 else move_coordinates(game, coordinates, 1)) if not paused_list[0] else None,
            "<down>": lambda: (move(game, 3) if move_mode[-1] == 0 else move_coordinates(game, coordinates, 3)) if not paused_list[0] else None,
            "<left>": lambda: (move(game, 0) if move_mode[-1] == 0 else move_coordinates(game, coordinates, 0)) if not paused_list[0] else None,
            "<right>": lambda: (move(game, 2) if move_mode[-1] == 0 else move_coordinates(game, coordinates, 2)) if not paused_list[0] else None,
            "<enter>": lambda: ((select_coordinates(game, coordinates_list, coordinates) if len(coordinates_list) != 2 else submit_coordinates(game, game.swap, coordinates_list, move_mode)) if move_mode[-1] == 1 else ((select_coordinates(game, coordinates_list, coordinates) if len(coordinates_list) !=1 else submit_coordinates(game, game.delete, coordinates_list, move_mode)) if move_mode[-1] == 2 else restart(game))) if not paused_list[0] else None,
            "<esc>": lambda: confirm_pause(game, paused_list, confirm_await_list, move_mode, coordinates) if confirm_await_list[0] else ((condition.append(False) if move_mode[-1] == 0 else set_mode(game, move_mode, 0, coordinates, coordinates_list)) if not paused_list[0] else None),
            "<space>": lambda: start_pause(confirm_await_list) if not confirm_await_list[0] else None
        }
        if game.powerups:
            keybinds["<shift>+u"] = lambda: (undo(game) if move_mode[-1] == 0 else None) if not paused_list[0] else None
            keybinds["<shift>+i"] = lambda: (set_mode(game, move_mode, 1, coordinates, coordinates_list) if move_mode[-1] == 0 and game.swaps_left != 0 else (print("You don't have any uses left, make 256 tiles to get more uses") if game.swaps_left == 0 else None)) if not paused_list[0] else None
            keybinds["<shift>+o"] = lambda: (set_mode(game, move_mode, 2, coordinates, coordinates_list) if move_mode[-1] == 0 and game.deletes_left != 0 else (print("You don't have any uses left, make 512 tiles to get more uses") if game.deletes_left == 0 else None)) if not paused_list[0] else None
        listener: keyboard.GlobalHotKeys = keyboard.GlobalHotKeys(keybinds)
        listener.start()
        while condition[-1]:
            time.sleep(1)
            if confirm_await_list[0]:
                time.sleep(1)
                if confirm_await_list[0]:
                    confirm_await_list[0] = False
                    print("ESC key was not pressed")
            move_mode = [move_mode[-1]]
        quit()

if __name__ == "__main__":
    main(sys.argv)