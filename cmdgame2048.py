import random
from pynput import keyboard
import os
import typing

clean = lambda : os.system("cls") if os.name == "nt" else os.system("clear")

SpawnOutput = typing.Literal[-1, 1, 2]
MoveOutput = typing.Literal[-1, 0, 1, 2]
Grid = typing.List[typing.List[int]]
GameState = typing.Literal[-1, 0, 1]

class Game2048:
    def __str__(self)-> str:
        additional_info: str = ""
        if self.game_state == -1:
            additional_info = " (LOST)"
        if self.game_state == 1:
            additional_info = " (WON)"
        result: str = f"Score: {self.score}, Moves: {self.moves}{additional_info}"
        max_character_lengths = []
        for i in zip(*self.grid):
            max_character_lengths.append(len(self.tiles[max(i)]))
        for i in self.grid:
            result += "\n"
            first: bool = True
            for k in range(len(i)):
                j = i[k]
                column_max_length = max_character_lengths[k]
                tile_string: str = self.tiles[j]
                padded_length: int = column_max_length - len(tile_string)
                front_padding: int = padded_length//2
                back_padding: int = front_padding + padded_length%2 + 1
                if k == len(i) - 1:
                    back_padding = 0
                tile_string: str = tile_string + " "*back_padding
                if first:
                    first = False
                else:
                    tile_string = "| " + " "*front_padding + tile_string
                result += tile_string
        
        return result

    def _spawn(self)-> SpawnOutput:
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
    
    def _move(self, direction: int, check_only: bool = False)-> MoveOutput:
        #left - 0, up - 1, right - 2, down - 3
        direction %= 4
        rotated_grid = self.grid.copy()
        for i in range(direction):
            rotated_grid = list(map(list, zip(*rotated_grid)))[::-1]

        empty_available: bool = False
        definitely_changed: bool = False
        new_tiles: typing.List[str] = self.tiles.copy()
        new_score = self.score
        new_rotated_grid: Grid = []
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
            return self._spawn()

    def _check(self, check_argument: MoveOutput)-> GameState:
        if check_argument != -1:
            max_number: int = 0
            for row in self.grid:
                for tile in row:
                    if tile > current_max:
                        current_max = tile
            if max_number == 11:
                self.game_state = 1
        else:
            move_found: bool = False
            for i in range(4):
                if self._move(i, True) != -1:
                    move_found = True
                    break
            if not move_found:
                self.game_state = -1
        return self.game_state

    def public_move(self, direction: int)-> bool:
        if self.game_state == -1:
            return False
        self._check(self._move(direction))
        return True

    def restart(self):
        self.grid: Grid = [[0]*4]*4
        self.tiles: typing.List[str] = ["", "2", "4"]
        self.score: int = 0
        self.moves: int = 0
        self.game_state: GameState = 0
        self._spawn()
        self._spawn()

    def __init__(self):
        self.restart()


def restart(game_object: Game2048):
    game_object.restart()
    clean()
    print(str(game_object))


def move(game_object: Game2048, direction: int):
    game_object.public_move(direction)
    clean()
    print(str(game_object))


def main():
    if input("By pressing enter, you agree that the terminal will be cleared and that the game of 2048 will start. Controls are WASD or arrow keys, ENTER to quit and R to restart. Press any key and enter to avoid starting the game: ") == "":
        game = Game2048()
        restart(game)
        listener = keyboard.GlobalHotKeys({
            "w": (lambda: move(game, 1))(),
            "s": (lambda: move(game, 3))(),
            "a": (lambda: move(game, 0))(),
            "d": (lambda: move(game, 2))(),
            "<up>": (lambda: move(game, 1))(),
            "<down>": (lambda: move(game, 3))(),
            "<left>": (lambda: move(game, 0))(),
            "<right>": (lambda: move(game, 2))(),
            "r": (lambda: restart(game))()
            
        })
        listener.start()
        print("Pressing enter will end the game, press any key to remove this text", end = "")
        input("")

main()