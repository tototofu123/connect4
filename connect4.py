import pygame
import sys
import math
import random
import copy
import time

# --- CONSTANTS ---
BLUE = (0, 0, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
GRAY = (50, 50, 50)
GREEN = (0, 200, 0)

ROW_COUNT = 6
COLUMN_COUNT = 7

PLAYER = 0
AI = 1

EMPTY = 0
PLAYER_PIECE = 1
AI_PIECE = 2

WINDOW_LENGTH = 4

# --- MINIMAX & GAME LOGIC ---

def create_board():
    return [[EMPTY for _ in range(COLUMN_COUNT)] for _ in range(ROW_COUNT)]

def drop_piece(board, row, col, piece):
    board[row][col] = piece

def is_valid_location(board, col):
    return board[ROW_COUNT-1][col] == 0

def get_next_open_row(board, col):
    for r in range(ROW_COUNT):
        if board[r][col] == 0:
            return r

def winning_move(board, piece):
    # Horizontal
    for c in range(COLUMN_COUNT - 3):
        for r in range(ROW_COUNT):
            if board[r][c] == piece and board[r][c+1] == piece and board[r][c+2] == piece and board[r][c+3] == piece:
                return True
    # Vertical
    for c in range(COLUMN_COUNT):
        for r in range(ROW_COUNT - 3):
            if board[r][c] == piece and board[r+1][c] == piece and board[r+2][c] == piece and board[r+3][c] == piece:
                return True
    # Positive Diagonal
    for c in range(COLUMN_COUNT - 3):
        for r in range(ROW_COUNT - 3):
            if board[r][c] == piece and board[r+1][c+1] == piece and board[r+2][c+2] == piece and board[r+3][c+3] == piece:
                return True
    # Negative Diagonal
    for c in range(COLUMN_COUNT - 3):
        for r in range(3, ROW_COUNT):
            if board[r][c] == piece and board[r-1][c+1] == piece and board[r-2][c+2] == piece and board[r-3][c+3] == piece:
                return True
    return False

def evaluate_window(window, piece):
    score = 0
    opp_piece = PLAYER_PIECE
    if piece == PLAYER_PIECE:
        opp_piece = AI_PIECE

    if window.count(piece) == 4:
        score += 100
    elif window.count(piece) == 3 and window.count(EMPTY) == 1:
        score += 5
    elif window.count(piece) == 2 and window.count(EMPTY) == 2:
        score += 2

    if window.count(opp_piece) == 3 and window.count(EMPTY) == 1:
        score -= 4

    return score

def score_position(board, piece):
    score = 0
    center_array = [board[r][COLUMN_COUNT//2] for r in range(ROW_COUNT)]
    center_count = center_array.count(piece)
    score += center_count * 3

    for r in range(ROW_COUNT):
        row_array = board[r]
        for c in range(COLUMN_COUNT - 3):
            window = row_array[c:c+WINDOW_LENGTH]
            score += evaluate_window(window, piece)

    for c in range(COLUMN_COUNT):
        col_array = [board[r][c] for r in range(ROW_COUNT)]
        for r in range(ROW_COUNT - 3):
            window = col_array[r:r+WINDOW_LENGTH]
            score += evaluate_window(window, piece)

    for r in range(ROW_COUNT - 3):
        for c in range(COLUMN_COUNT - 3):
            window = [board[r+i][c+i] for i in range(WINDOW_LENGTH)]
            score += evaluate_window(window, piece)

    for r in range(ROW_COUNT - 3):
        for c in range(COLUMN_COUNT - 3):
            window = [board[r+3-i][c+i] for i in range(WINDOW_LENGTH)]
            score += evaluate_window(window, piece)

    return score

def is_terminal_node(board):
    return winning_move(board, PLAYER_PIECE) or winning_move(board, AI_PIECE) or len(get_valid_locations(board)) == 0

def get_valid_locations(board):
    valid_locations = []
    for col in range(COLUMN_COUNT):
        if is_valid_location(board, col):
            valid_locations.append(col)
    return valid_locations

def minimax(board, depth, alpha, beta, maximizingPlayer):
    valid_locations = get_valid_locations(board)
    is_terminal = is_terminal_node(board)
    
    if depth == 0 or is_terminal:
        if is_terminal:
            if winning_move(board, AI_PIECE):
                return (None, 100000000000000)
            elif winning_move(board, PLAYER_PIECE):
                return (None, -10000000000000)
            else:
                return (None, 0)
        else:
            return (None, score_position(board, AI_PIECE))

    if maximizingPlayer:
        value = -math.inf
        column = random.choice(valid_locations)
        for col in valid_locations:
            row = get_next_open_row(board, col)
            b_copy = copy.deepcopy(board)
            drop_piece(b_copy, row, col, AI_PIECE)
            new_score = minimax(b_copy, depth-1, alpha, beta, False)[1]
            if new_score > value:
                value = new_score
                column = col
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return column, value

    else:
        value = math.inf
        column = random.choice(valid_locations)
        for col in valid_locations:
            row = get_next_open_row(board, col)
            b_copy = copy.deepcopy(board)
            drop_piece(b_copy, row, col, PLAYER_PIECE)
            new_score = minimax(b_copy, depth-1, alpha, beta, True)[1]
            if new_score < value:
                value = new_score
                column = col
            beta = min(beta, value)
            if alpha >= beta:
                break
        return column, value

# --- GRAPHICS & INTERFACE ---

def create_board_mask(SQUARESIZE, height):
    """ Creates a blue surface with transparent holes for the board """
    mask = pygame.Surface((COLUMN_COUNT * SQUARESIZE, height), pygame.SRCALPHA)
    mask.fill(BLUE)
    for c in range(COLUMN_COUNT):
        for r in range(ROW_COUNT):
            center_x = int(c * SQUARESIZE + SQUARESIZE / 2)
            center_y = int(r * SQUARESIZE + SQUARESIZE + SQUARESIZE / 2)
            pygame.draw.circle(mask, (0, 0, 0, 0), (center_x, center_y), int(SQUARESIZE / 2 - 5))
    return mask

def draw_header(screen, width, SQUARESIZE, text, text_color):
    """ Draws the top bar with status text """
    pygame.draw.rect(screen, BLACK, (0, 0, width, SQUARESIZE))
    font = pygame.font.SysFont("monospace", 40, bold=True)
    label = font.render(text, 1, text_color)
    label_rect = label.get_rect(center=(width/2, SQUARESIZE/2))
    screen.blit(label, label_rect)

def draw_static_board(board, screen, SQUARESIZE, height, board_mask, header_text="", header_color=WHITE):
    """ Draws the pieces and the board mask """
    screen.fill(BLACK) 
    
    # Draw Static Pieces
    for c in range(COLUMN_COUNT):
        for r in range(ROW_COUNT):
            piece = board[r][c]
            if piece != EMPTY:
                color = RED if piece == PLAYER_PIECE else YELLOW
                pos_x = int(c * SQUARESIZE + SQUARESIZE / 2)
                pos_y = height - int(r * SQUARESIZE + SQUARESIZE / 2)
                pygame.draw.circle(screen, color, (pos_x, pos_y), int(SQUARESIZE / 2 - 5))
    
    # Draw Board Overlay
    screen.blit(board_mask, (0, 0))
    
    # Draw Header (Turn Indicator)
    draw_header(screen, COLUMN_COUNT * SQUARESIZE, SQUARESIZE, header_text, header_color)

def animate_drop(board, screen, row, col, piece, SQUARESIZE, height, board_mask, header_text, header_color):
    """ Animates a piece falling """
    color = RED if piece == PLAYER_PIECE else YELLOW
    
    target_y = height - int(row * SQUARESIZE + SQUARESIZE / 2)
    start_y = int(SQUARESIZE / 2)
    current_y = start_y
    speed = 0
    gravity = 2.5 
    
    pos_x = int(col * SQUARESIZE + SQUARESIZE / 2)
    radius = int(SQUARESIZE / 2 - 5)

    clock = pygame.time.Clock()

    while current_y < target_y:
        speed += gravity
        current_y += speed
        if current_y > target_y:
            current_y = target_y

        # Draw Background & Header
        draw_static_board(board, screen, SQUARESIZE, height, board_mask, header_text, header_color)
        
        # Draw Falling Piece (under mask, over background if we weren't redrawing everything, 
        # but here we draw piece then mask)
        
        # We need to manually draw background pieces again or just accept the layering
        # The easiest way to get layering right with the mask:
        # 1. Clear Screen
        # 2. Draw falling piece
        # 3. Draw static pieces (wait, static pieces might cover falling piece if full? No)
        # 4. Draw Mask
        
        # Let's use the helper but purely for background, then draw falling, then mask
        screen.fill(BLACK)
        
        # 1. Static Pieces
        for c in range(COLUMN_COUNT):
            for r in range(ROW_COUNT):
                p = board[r][c]
                if p != EMPTY:
                    c_color = RED if p == PLAYER_PIECE else YELLOW
                    px = int(c * SQUARESIZE + SQUARESIZE / 2)
                    py = height - int(r * SQUARESIZE + SQUARESIZE / 2)
                    pygame.draw.circle(screen, c_color, (px, py), int(SQUARESIZE / 2 - 5))

        # 2. Falling Piece
        pygame.draw.circle(screen, color, (pos_x, int(current_y)), radius)

        # 3. Mask
        screen.blit(board_mask, (0,0))
        
        # 4. Header
        draw_header(screen, COLUMN_COUNT * SQUARESIZE, SQUARESIZE, header_text, header_color)

        pygame.display.update()
        clock.tick(60)

def draw_menu(screen, width, height):
    screen.fill(BLACK)
    font_title = pygame.font.SysFont("monospace", 60, bold=True)
    font_btn = pygame.font.SysFont("monospace", 30)
    
    title = font_title.render("CONNECT 4 AI", 1, BLUE)
    title_rect = title.get_rect(center=(width/2, height/6))
    screen.blit(title, title_rect)

    buttons = []
    labels = ["Random", "Easy (1)", "Medium (2)", "Hard (3)", "V. Hard (4)", "Expert (5)"]
    
    start_y = height/3
    for i, label in enumerate(labels):
        btn_rect = pygame.Rect(width/2 - 150, start_y + (i * 60), 300, 50)
        pygame.draw.rect(screen, WHITE, btn_rect)
        
        text = font_btn.render(label, 1, BLACK)
        text_rect = text.get_rect(center=btn_rect.center)
        screen.blit(text, text_rect)
        
        buttons.append((btn_rect, i))
        
    pygame.display.update()
    return buttons

def draw_game_over(screen, winner_text, winner_color, width, height):
    # Overlay
    overlay = pygame.Surface((width, height))
    overlay.set_alpha(10) # Faint overlay to keep game visible
    screen.blit(overlay, (0,0))

    font = pygame.font.SysFont("monospace", 75, bold=True)
    font_btn = pygame.font.SysFont("monospace", 40)

    # Winner Text
    label = font.render(winner_text, 1, winner_color)
    # Add a black outline/shadow for readability
    label_shadow = font.render(winner_text, 1, BLACK)
    
    label_rect = label.get_rect(center=(width/2, height/2 - 80))
    screen.blit(label_shadow, (label_rect.x+3, label_rect.y+3))
    screen.blit(label, label_rect)
    
    # Button
    btn_rect = pygame.Rect(width/2 - 120, height/2 + 20, 240, 70)
    pygame.draw.rect(screen, GREEN, btn_rect)
    pygame.draw.rect(screen, WHITE, btn_rect, 3) # Border
    
    btn_text = font_btn.render("MAIN MENU", 1, WHITE)
    btn_text_rect = btn_text.get_rect(center=btn_rect.center)
    screen.blit(btn_text, btn_text_rect)
    
    pygame.display.update()
    return btn_rect

# --- MAIN APPLICATION LOOP ---

def main():
    pygame.init()
    
    SQUARESIZE = 100
    width = COLUMN_COUNT * SQUARESIZE
    height = (ROW_COUNT + 1) * SQUARESIZE
    size = (width, height)
    radius = int(SQUARESIZE/2 - 5)

    screen = pygame.display.set_mode(size)
    pygame.display.set_caption("Connect 4 AI")
    
    board_mask = create_board_mask(SQUARESIZE, height)
    
    state = "MENU"
    board = create_board()
    turn = random.randint(PLAYER, AI)
    difficulty = 1
    
    menu_buttons = []
    game_over_btn = None

    while True:
        # --- MENU STATE ---
        if state == "MENU":
            menu_buttons = draw_menu(screen, width, height)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = event.pos
                    for btn_rect, level in menu_buttons:
                        if btn_rect.collidepoint(pos):
                            difficulty = level
                            board = create_board()
                            turn = random.randint(PLAYER, AI)
                            state = "PLAYING"
                            
                            # Initial Draw
                            txt = "YOUR TURN" if turn == PLAYER else "AI THINKING..."
                            col = RED if turn == PLAYER else YELLOW
                            draw_static_board(board, screen, SQUARESIZE, height, board_mask, txt, col)
                            pygame.display.update()

        # --- PLAYING STATE ---
        elif state == "PLAYING":
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()

                if event.type == pygame.MOUSEMOTION and turn == PLAYER:
                    # Clear Header area only
                    pygame.draw.rect(screen, BLACK, (0,0, width, SQUARESIZE))
                    draw_header(screen, width, SQUARESIZE, "YOUR TURN", RED)
                    
                    posx = event.pos[0]
                    pygame.draw.circle(screen, RED, (posx, int(SQUARESIZE/2)), radius)
                    pygame.display.update()

                if event.type == pygame.MOUSEBUTTONDOWN and turn == PLAYER:
                    pygame.draw.rect(screen, BLACK, (0,0, width, SQUARESIZE))
                    posx = event.pos[0]
                    col = int(math.floor(posx/SQUARESIZE))

                    if is_valid_location(board, col):
                        row = get_next_open_row(board, col)
                        
                        # Animate Drop
                        animate_drop(board, screen, row, col, PLAYER_PIECE, SQUARESIZE, height, board_mask, "YOUR TURN", RED)
                        drop_piece(board, row, col, PLAYER_PIECE)

                        if winning_move(board, PLAYER_PIECE):
                            state = "GAMEOVER"
                            # Draw result immediately
                            draw_static_board(board, screen, SQUARESIZE, height, board_mask, "GAME OVER", RED)
                            game_over_btn = draw_game_over(screen, "PLAYER WINS!", RED, width, height)
                        else:
                            turn = AI
                            draw_static_board(board, screen, SQUARESIZE, height, board_mask, "AI THINKING...", YELLOW)
                            pygame.display.update()

            # AI Logic (Outside Event Loop)
            if turn == AI and state == "PLAYING":
                # Wait random time with event pump
                start_wait = time.time()
                wait_duration = random.uniform(0.5, 1.5)
                while time.time() - start_wait < wait_duration:
                    pygame.event.pump()
                    
                if difficulty == 0:
                    col = random.choice(get_valid_locations(board))
                else:
                    col, minimax_score = minimax(board, difficulty, -math.inf, math.inf, True)

                if is_valid_location(board, col):
                    row = get_next_open_row(board, col)
                    
                    animate_drop(board, screen, row, col, AI_PIECE, SQUARESIZE, height, board_mask, "AI THINKING...", YELLOW)
                    drop_piece(board, row, col, AI_PIECE)

                    if winning_move(board, AI_PIECE):
                        state = "GAMEOVER"
                        draw_static_board(board, screen, SQUARESIZE, height, board_mask, "GAME OVER", YELLOW)
                        game_over_btn = draw_game_over(screen, "AI WINS!", YELLOW, width, height)
                    else:
                        turn = PLAYER
                        draw_static_board(board, screen, SQUARESIZE, height, board_mask, "YOUR TURN", RED)
                        # We force an update so the player sees the red piece immediately if their mouse is on screen
                        mx, my = pygame.mouse.get_pos()
                        pygame.draw.circle(screen, RED, (mx, int(SQUARESIZE/2)), radius)
                        pygame.display.update()

        # --- GAMEOVER STATE ---
        elif state == "GAMEOVER":
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if game_over_btn and game_over_btn.collidepoint(event.pos):
                        state = "MENU"

if __name__ == "__main__":
    main()