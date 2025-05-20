# About
This is a recreation of the [2048 game](https://play2048.co/) by Gabriele Circulli in command line.
## How to play
To play, press either WASD or arrow keys. This moves all the tiles in a certain direction. If two same tiles move and are next to each other in the moving direction, they merge to a higher power of two. If three tiles are next to each other, only the first two merge. If there are four same tiles next to each other, the pairs merge to the higher powers.

You get score from merging two tiles together. The goal is to eventually make a 2048 tile and then reach the highest score you can. You lose moment you can't merge or move any tiles in any direction.

You can restart the game by pressing ENTER and quit by pressing ESC
### power-ups
There are three types of power-ups - undo a move, swap two tiles, and delete tiles by number. Only the first is supported right now.
- Undo a move -  Activated by doing SHIFT+U. Undoes the last move you did, you can't undo two moves in a row. You start with 2 uses and need to make a 128 tile to get more. Power up counts as a move, therefore it is possible to undo a power up.
- Swap two tiles - Activated by doing SHIFT+I. Pushing moving keys moves coordinates on bottom. Pressing ENTER selects the tile coordinates point to. Once two tiles are selected, press ENTER to swap the selected tiles. Press ESC to quit the swap selection mode. Trying to select an empty tile fails. You start with 1 use and need to make a 256 tile to get more.
- Delete all tiles with a number - Activated by doing SHIFT+O. Pushing moving keys moves coordinates on bottom. Pressing ENTER selects the tile coordinates point to. Once is the tile selected press ENTER again to delete all the intented tiles. If the selected tile is not empty, it will remove all tiles with that number. Press ESC to quit delete selection mode. You start with no uses and need to make a 512 tile to get more.

The power-ups are implemented based of the remake of the 2048 game made by the same creator as of the original.