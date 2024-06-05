"""
1. CS 404 - Assignment 3: Hashi Game AI
2.  Team Members: Ada Canoglu (29022), Kourosh Sharifi (30438)

3. Key points: Islands are tuples (x, y, w)
    - Islands are kept in a list in the same order read from left to right top to bottom on grids
    - Adjacency matrix to store bridges, which is symmetric
    - Terminal state is when no valid moves exists
    - State transition function is make_move
    - The alpha beta pruning algorithm works by assuming that you (human) are really smart and
        always respond with the most optimal choice. It does not consider you making bad moves
"""

import time
import logging

# for tracing
logging.basicConfig(filename='hashi_game.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# numbers for comparison in alpha-beta pruning
MIN = float('-inf')
MAX = float('inf')

def lines_intersect(ax1, ay1, ax2, ay2, bx1, by1, bx2, by2):
        # Both lines are horizontal and on the same y-coordinate
        if ay1 == ay2 and by1 == by2:
            return ay1 == by1 and max(ax1, ax2) > min(bx1, bx2) and min(ax1, ax2) < max(bx1, bx2)
        # Both lines are vertical and on the same x-coordinate
        elif ax1 == ax2 and bx1 == bx2:
            return ax1 == bx1 and max(ay1, ay2) > min(by1, by2) and min(ay1, ay2) < max(by1, by2)
        # First line horizontal, second vertical
        elif ay1 == ay2 and bx1 == bx2:
            return (by1 < ay1 and by2 > ay1) and (bx1 > min(ax1, ax2) and bx1 < max(ax1, ax2))
        # First line vertical, second horizontal
        elif ax1 == ax2 and by1 == by2:
            return (bx1 < ax1 and bx2 > ax1) and (by1 > min(ay1, ay2) and by1 < max(ay1, ay2))
        else:
            return False

class IslandGame:
    def __init__(self, islands, size):
        # the max of width or height will be set as the length of the square map
        self._size = size
        
        # the list of tuples containing individual islands (each island has 3 parameters)
        self._islands = islands
        
        # by default, no two adjacent islands exist
        self._adjacency_matrix = [[0] * len(islands) for _ in range(len(islands))]
        
        # player A is human, and B is AI; both start with zero points
        self._points = {"Player A": 0, "Player B": 0}
        
        # construct the actual adjacency matrix
        self._initialize_adjacency_matrix()
        
        # store the coordinates of all islands
        self._island_dict = {(x, y): i for i, (x, y, _) in enumerate(islands)}

    def _initialize_adjacency_matrix(self):
        for x, y, value in self._islands:
            if not self._is_valid_coordinate(x, y):
                logging.error(f"Invalid coordinates for island: {(x, y, value)}")
                raise ValueError(f"[ERROR] Invalid coordinates for island: {(x, y, value)}")

    def _is_valid_coordinate(self, x, y):
        return 0 <= x < self._size and 0 <= y < self._size

    def _get_bridge_count(self, index):
        # count the number of bridges connected to an island
        return sum(self._adjacency_matrix[index])    
        
    
    def _is_valid_bridge(self, index1, index2): # Pray to god that this works (or change it idk how it works honestly)
        x1, y1, value1 = self._islands[index1]
        x2, y2, value2 = self._islands[index2]

        # Cannot connect to itself
        if(index1 == index2):
            return False

        # Ensure the islands are aligned vertically or horizontally
        if not (x1 == x2 or y1 == y2):
            return False

        # Ensure the maximum bridge count hasn't been exceeded for either island
        if self._get_bridge_count(index1) >= value1 or self._get_bridge_count(index2) >= value2:
            return False

        # Check if the bridge would cross any existing islands
        if x1 == x2:  # Vertical bridge
            y_start, y_end = sorted([y1, y2])
            for y in range(y_start + 1, y_end):
                if (x1, y) in self._island_dict:
                    return False
        elif y1 == y2:  # Horizontal bridge
            x_start, x_end = sorted([x1, x2])
            for x in range(x_start + 1, x_end):
                if (x, y1) in self._island_dict:
                    return False

        # Ensure no crossing bridges
        for i in range(len(self._islands)):
            for j in range(i + 1, len(self._islands)):
                if self._adjacency_matrix[i][j] > 0:
                    xi1, yi1, _ = self._islands[i]
                    xi2, yi2, _ = self._islands[j]
                    if not (index1 == i and index2 == j or index1 == j and index2 == i):
                        if lines_intersect(x1, y1, x2, y2, xi1, yi1, xi2, yi2):
                            return False
                    
        # Ensure at most two bridges can connect a pair of islands
        return self._adjacency_matrix[index1][index2] < 2

    def _update_points(self, player, points):
        # update both players' scores
        self._points[player] += points
        opponent = "Player B" if player == "Player A" else "Player A"
        self._points[opponent] -= points

    def insert_value(self, index, value):
        # perform checks for invalid placements
        if not (0 <= index < len(self._islands)):
            logging.error("Invalid island index.")
            print("[ERROR] Invalid island index.")
            return False
        x, y, current_value = self._islands[index]
        if current_value != 0:
            logging.error("Cannot appoint a label to a non-empty island.")
            print("[ERROR] Cannot appoint a label to a non-empty island.")
            return False
        if value not in [3, 4]:
            # labels can't be anything other than 3 or 4
            logging.error("Invalid label. Can only choose 3 or 4.")
            print("[ERROR] Invalid label. Can only choose 3 or 4.")
            return False

        # place the given weight for said island
        self._islands[index] = (x, y, value)
        return True

    def make_move(self, player, action):
        # can't have any other type of plaer besides A (human) and B (AI)
        if player not in ["Player A", "Player B"]:
            logging.error("Invalid player.")
            print("[ERROR] Invalid player.")
            return False

        if action is None:
            logging.warning("No valid moves available.")
            print("[WARNING] No valid moves available.")
            return False

        if len(action) == 3 and action[2] == "bridge":
            index1, index2, _ = action
            if not (0 <= index1 < len(self._islands) and 0 <= index2 < len(self._islands)):
                logging.error("Invalid island indices.")
                print("[ERROR] Invalid island indices.")
                return False

            if not self._is_valid_bridge(index1, index2):
                logging.error("Invalid bridge placement.")
                print("[ERROR] Invalid bridge placement.")
                return False

            # since it's symmetric, increase for both islands
            self._adjacency_matrix[index1][index2] += 1
            self._adjacency_matrix[index2][index1] += 1

            # update points for the two affected islands
            for index in [index1, index2]:
                x, y, value = self._islands[index]
                if self._get_bridge_count(index) == value:
                    self._update_points(player, value)

        elif len(action) == 3 and action[2] == "label":
            index, value = action[0], action[1]
            if not self.insert_value(index, value):
                return False

            # update points for the affected island
            x, y, _ = self._islands[index]
            if self._get_bridge_count(index) == value:
                self._update_points(player, value)

        else:
            logging.error("Invalid action.")
            print("[ERROR] Invalid action.")
            return False

        return True

    def visualize_game_state(self):
        size = self._size
        visual_map = [['.'] * (size * 2 - 1) for _ in range(size * 2 - 1)]
        island_positions = {(x, y): value for x, y, value in self._islands}

        for i in range(len(self._islands)):
            for j in range(i + 1, len(self._islands)):
                x1, y1, _ = self._islands[i]
                x2, y2, _ = self._islands[j]

                if self._adjacency_matrix[i][j] > 0:
                    if x1 == x2:  # horizontal bridge because `x` corresponds to row number
                        bridge_symbol = '-' if self._adjacency_matrix[i][j] == 1 else '='
                        for y in range(min(y1, y2) * 2 + 1, max(y1, y2) * 2):
                            visual_map[x1 * 2][y] = bridge_symbol
                    elif y1 == y2:  # vertical bridge because `y` corresponds to column number
                        bridge_symbol = '|' if self._adjacency_matrix[i][j] == 1 else 'X'
                        for x in range(min(x1, x2) * 2 + 1, max(x1, x2) * 2):
                            visual_map[x][y1 * 2] = bridge_symbol

        for x, y in island_positions:
            visual_map[x * 2][y * 2] = str(island_positions[(x, y)])

        print()
        logging.info("\n")
        for row in visual_map:
            print(' '.join(row))
            logging.info(' '.join(row))
    
    def valid_moves(self):
        # return the list of valid moves
        moves = []

        # check for bridge connections
        for i, (x1, y1, value1) in enumerate(self._islands):
            for j, (x2, y2, value2) in enumerate(self._islands):
                if i != j and self._is_valid_bridge(i, j):
                    moves.append((i, j, "bridge"))

        # check for inserting a value into an empty island
        for i, (x, y, value) in enumerate(self._islands):
            if value == 0:  # only insert into empty islands (weight is zero)
                if self.insert_value(i, 3):
                    moves.append((i, 3, "label"))
                    self._islands[i] = (x, y, 0)  # reset after testing
                if self.insert_value(i, 4):
                    moves.append((i, 4, "label"))
                    self._islands[i] = (x, y, 0)  # reset after testing

        return moves

    def print_points(self):
        print(f"\nPlayer A: {self._points['Player A']}, Player B: {self._points['Player B']}")
        logging.info(f"Player A: {self._points['Player A']}, Player B: {self._points['Player B']}")
            
    def get_results(self):
        # find whether win or tie
        if self._points['Player A'] > self._points['Player B']:
            print("You won!")
            logging.info("You won!")
        elif self._points['Player A'] < self._points['Player B']:
            print("AI won :(")
            logging.info("AI won :(")
        else:
            print("It's a tie.")
            logging.info("It's a tie.")

    def evaluate(self):
        return self._points["Player B"] - self._points["Player A"]

    def clone(self):
        # create a deep copy of the game
        clone = IslandGame(self._islands[:], self._size)
        clone._adjacency_matrix = [row[:] for row in self._adjacency_matrix]
        clone._points = self._points.copy()
        clone._island_dict = self._island_dict.copy()
        return clone

    def minimax(self, depth, nodeIndex, maximizingPlayer, alpha, beta): 
        # game tree search with alpha beta pruning
        if depth == 10 or not self.valid_moves():
            # if explored too deep or reached a terminal state (no possible moves)
            return self.evaluate(), None
 
        if maximizingPlayer: 
            best = MIN
            best_move = None
            valid_moves = self.valid_moves()
 
            # recur for left and right children 
            for i, action in enumerate(valid_moves): 
                new_state = self.clone()
                new_state.make_move("Player B", action)
                val, _ = new_state.minimax(depth + 1, nodeIndex * 2 + i, False, alpha, beta)
                best = max(best, val) 
                if best == val:
                    best_move = action
                alpha = max(alpha, best) 
 
                if beta <= alpha: 
                    break
          
            return best, best_move
          
        else: 
            best = MAX
            best_move = None
            valid_moves = self.valid_moves()
 
            # recur for left and right children 
            for i, action in enumerate(valid_moves): 
                new_state = self.clone()
                new_state.make_move("Player A", action)
                val, _ = new_state.minimax(depth + 1, nodeIndex * 2 + i, True, alpha, beta)
                best = min(best, val)
                if best == val:
                    best_move = action 
                beta = min(beta, best) 
 
                if beta <= alpha: 
                    break
          
            return best, best_move


def get_map_dimensions(islands):
    # to use for setting the size of the map
    max_x = max(island[0] for island in islands)
    min_x = min(island[0] for island in islands)
    max_y = max(island[1] for island in islands)
    min_y = min(island[1] for island in islands)

    width = max_x - min_x + 1
    height = max_y - min_y + 1

    return width, height


def read_islands_from_file(filename):
    # turn the content of the txt file into a list of tuples
    islands = []
    with open(filename, 'r') as file:
        lines = file.readlines()
        for x, line in enumerate(lines):
            y = 0
            for char in line.strip():
                if char.isdigit():
                    islands.append((x, y, int(char)))
                    y += 1  # Move to the next non-space character
                elif char != ' ':  # Ignore spaces
                    y += 1  # Move to the next non-space character
    return islands


def play_against_ai(islands):
    width, height = get_map_dimensions(islands)
    game = IslandGame(islands, max(width, height))
    
    time.sleep(0.6)
    print("Before starting the game...")
    logging.info("Before starting the game...")
    
    game.visualize_game_state()
    game.print_points()

    while game.valid_moves():
        # for when AI wants go first
        # comment until the sleep timer
        
        # Player A's turn (human)
        print("\nPlayer A's turn:")
        logging.info("\nPlayer A's turn:")
        move_type = input("> Type your desired type of action:\n\t1. Insert a bridge\n\t2. Adjust a label\n>> ")
        if "insert" in move_type.lower() or "bridge" in move_type.lower() or "1" in move_type:
            index1 = int(input("> Enter the index of first island (L->R, T->B):\n>> "))
            index2 = int(input("> Enter the index of second island (L->R, T->B):\n>> "))
            move = (index1, index2, "bridge")
        elif "adjust" in move_type.lower() or "label" in move_type.lower() or "2" in move_type:
            index = int(input("> Enter the index of island to insert value (L->R, T->B):\n>> "))
            value = int(input("> Choose a value between 3 or 4:\n>> "))
            move = (index, value, "label")
        else:
            print("[ERROR] Invalid move type.")
            logging.error("Invalid move type.")
            continue

        if not game.make_move("Player A", move):
            print("[ERROR] Invalid move. Try again.")
            logging.error("Invalid move. Try again.")
            continue

        game.visualize_game_state()
        game.print_points()

        if not game.valid_moves():
            break
        
        time.sleep(0.6) # for times where it decides too fast to enhance UX
        # !comment until here for AI first!
        
        # Player B's turn (AI)
        print("\nPlayer B's turn (AI):")
        logging.info("\nPlayer B's turn (AI):")
        print("... Waiting for AI's move...") # for better UX
        _, best_action = game.minimax(0, 0, True, MIN, MAX)
        if best_action is None:
            print("No valid moves available for Player B.")
            logging.info("No valid moves available for Player B.")
            break
        print("Best move for Player B:", best_action)
        game.make_move("Player B", best_action)
        game.visualize_game_state()
        game.print_points()
        
        if not game.valid_moves():
            break
        
        # for when human goes second
        # # Player A's turn (human)
        # print("\nPlayer A's turn:")
        # logging.info("\nPlayer A's turn:")
        # move_type = input("> Type your desired type of action:\n\t1. Insert a bridge\n\t2. Adjust a label\n>> ")
        # if "insert" in move_type.lower() or "bridge" in move_type.lower() or "1" in move_type:
        #     index1 = int(input("> Enter the index of first island (L->R, T->B):\n>> "))
        #     index2 = int(input("> Enter the index of second island (L->R, T->B):\n>> "))
        #     move = (index1, index2, "bridge")
        # elif "adjust" in move_type.lower() or "label" in move_type.lower() or "2" in move_type:
        #     index = int(input("> Enter the index of island to insert value (L->R, T->B):\n>> "))
        #     value = int(input("> Choose a value between 3 or 4:\n>> "))
        #     move = (index, value, "label")
        # else:
        #     print("[ERROR] Invalid move type.")
        #     logging.error("Invalid move type.")
        #     continue

        # if not game.make_move("Player A", move):
        #     print("[ERROR] Invalid move. Try again.")
        #     logging.error("Invalid move. Try again.")
        #     continue

        # game.visualize_game_state()
        # game.print_points()

        # if not game.valid_moves():
        #     break
        
    # display who won or tie
    game.get_results()


def main():
    print("\nWelcome to the Hashi game, where you can play against our AI agent!\nLet's begin...\n")
    logging.info("\nWelcome to the Hashi game, where you can play against our AI agent!\nLet's begin...\n")
    
    filename = input("> Enter the filename:\n>> ")
    # the preprocessor for turning txt files into list of islands
    islands = read_islands_from_file(filename)
    print(f"\nAfter preprocessing the txt file, the `islands` list is: \n{islands}")
    logging.info(f"\nAfter preprocessing the txt file, the `islands` list is: \n{islands}")
    
    # start the game
    play_against_ai(islands)
    
    print("\nGame finished. Thank you for playing!\n")
    logging.info("\nGame finished. Thank you for playing!\n")


if __name__ == "__main__":
    main()
