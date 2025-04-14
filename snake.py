import pygame
import random
import psycopg2
import json

pygame.init()

conn = psycopg2.connect(
    dbname="snake_game",
    user="postgres",
    password="123456",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

# Create tables if they don't exist
cursor.execute('''
    ALTER TABLE IF EXISTS user_score
    ADD COLUMN IF NOT EXISTS speed INTEGER;
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS "user" (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_score (
        user_id INTEGER,
        score INTEGER,
        level INTEGER,
        speed INTEGER,  -- Add speed column
        PRIMARY KEY (user_id),
        FOREIGN KEY (user_id) REFERENCES "user" (id)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_snake (
        user_id INTEGER,
        snake_body TEXT,  -- Store snake body as a string (a list of coordinates)
        PRIMARY KEY (user_id),
        FOREIGN KEY (user_id) REFERENCES "user" (id)
    )
''')

conn.commit()

# Function to get user data from the database

def get_user_data(username):
    cursor.execute('SELECT * FROM "user" WHERE username = %s', (username,))
    user = cursor.fetchone()
    
    if user:
        user_id = user[0]
        cursor.execute('SELECT * FROM user_score WHERE user_id = %s', (user_id,))
        user_score = cursor.fetchone()
        if user_score:
            return user_id, user_score[1], user_score[2]
        else:
            return user_id, 0, 1
    else:
        cursor.execute('INSERT INTO "user" (username) VALUES (%s) RETURNING id', (username,))
        conn.commit()
        user_id = cursor.fetchone()[0]
        return user_id, 0, 1

# Function to save snake body and speed

def save_game_state(user_id, snake_body, score, level, speed):
    snake_body_str = json.dumps(snake_body)
    cursor.execute('''
        INSERT INTO user_snake (user_id, snake_body)
        VALUES (%s, %s)
        ON CONFLICT (user_id)
        DO UPDATE SET snake_body = %s
    ''', (user_id, snake_body_str, snake_body_str))

    # Save speed, score, and level

    cursor.execute('''
        INSERT INTO user_score (user_id, score, level, speed)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (user_id)
        DO UPDATE SET score = %s, level = %s, speed = %s
    ''', (user_id, score, level, speed, score, level, speed))
    conn.commit()

# Function to load the snake body and speed

def load_game_state(user_id):
    cursor.execute('SELECT snake_body FROM user_snake WHERE user_id = %s', (user_id,))
    result = cursor.fetchone()
    
    if result:
        snake_body = json.loads(result[0])
    else:
        snake_body = [[80, 100], [90, 100], [100, 100]]
    
    # Load speed, score, and level

    cursor.execute('SELECT score, level, speed FROM user_score WHERE user_id = %s', (user_id,))
    result = cursor.fetchone()
    
    if result:
        score, level, speed = result
    else:
        score, level, speed = 0, 1, 200

    if speed is None:
        speed = 200
    else:
        speed = int(speed)
    
    return snake_body, score, level, speed

# Game setup

width = 800
height = 600
screen = pygame.display.set_mode((width, height))

# Variables and their initialization

level = 1
speed = 200
fruits_eaten = 0
score = 0
fruit_eaten = False

# Gold apple

gold_active = False
gold_timer = 0
gold_coor = [0, 0]
gold_weight = 50

# Spawn the first fruit

fr_x = random.randrange(1, width // 10) * 10
fr_y = random.randrange(1, height // 10) * 10
fruit_coor = [fr_x, fr_y]

# Snake's body

head_square = [100, 100]
squares = [
    [80,100],
    [90,100],
    [100,100]
]

direction = "right"
next_dir = "right"

# Game over message

done = False
paused = False

def game_over(font, size, color):
    global done
    g_o_font = pygame.font.SysFont(font, size)
    g_o_surface = g_o_font.render("Game Over, your score: " + str(score), True, color)
    g_o_rect = g_o_surface.get_rect(center = (width // 2, height // 2))

    screen.blit(g_o_surface, g_o_rect)
    pygame.display.update()

    pygame.time.delay(4000)
    pygame.quit()

# User input for username

username = input("Enter your username: ")
user_id, score, level = get_user_data(username)
print(f"Welcome, {username}! Current Level: {level}")

# Load the snake body from the database

squares, score, level, speed = load_game_state(user_id)

# Function to display the pause screen

def show_pause_screen():
    font = pygame.font.SysFont("times new roman", 50)
    text_surface = font.render("PAUSED", True, (255, 0, 0))
    text_rect = text_surface.get_rect(center=(width // 2, height // 3))
    screen.blit(text_surface, text_rect)
    
    font_small = pygame.font.SysFont("times new roman", 20)
    text_surface_small = font_small.render("Press 'P' to resume", True, (255, 255, 255))
    text_rect_small = text_surface_small.get_rect(center=(width // 2, height // 2))
    screen.blit(text_surface_small, text_rect_small)
    
    pygame.display.update()


# Function to reset the game stats and database after death

def reset_game():
    global score, level, squares
    score = 0
    level = 1
    speed = 200
    squares = [[80, 100], [90, 100], [100, 100]]  # Default starting snake body
    
    # Reset the stats in the database

    cursor.execute('''
        UPDATE user_score
        SET score = %s, level = %s
        WHERE user_id = %s
    ''', (score, level, user_id))
    conn.commit()
    
    # Reset the snake's body in the database

    save_game_state(user_id, squares, score, level, speed)

# Start of gameplay loop

while not done:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_p:  # Press P to pause
                paused = not paused  # Toggle pause
            if not paused:
                if event.key == pygame.K_DOWN:
                    next_dir = "down"
                if event.key == pygame.K_UP:
                    next_dir = "up"
                if event.key == pygame.K_LEFT:
                    next_dir = "left"
                if event.key == pygame.K_RIGHT:
                    next_dir = "right"

    if paused:
        show_pause_screen()
        continue  # Skip game logic if paused

    # Game over conditions

    for square in squares[:-1]:
        if head_square[0] == square[0] and head_square[1] == square[1]:
            game_over("times new roman", 45, (128, 128, 128))
            reset_game()

    if head_square[0] < 0 or head_square[0] >= width or head_square[1] < 0 or head_square[1] >= height:
        game_over("times new roman", 45, (128, 128, 128))
        reset_game()
    
    # Change of Direction

    if next_dir == "right" and direction != "left":
        direction = "right"
    if next_dir == "up" and direction != "down":
        direction = "up"
    if next_dir == "left" and direction != "right":
        direction = "left"
    if next_dir == "down" and direction != "up":
        direction = "down"

    if direction == "right":
        head_square[0] += 10
    if direction == "left":
        head_square[0] -= 10
    if direction == "up":
        head_square[1] -= 10
    if direction == "down":
        head_square[1] += 10

    new_square = [head_square[0], head_square[1]]

    squares.append(new_square)
    squares.pop(0)

    # When fruit is eaten

    if head_square[0] == fruit_coor[0] and head_square[1] == fruit_coor[1]:
        fruit_eaten = True
        score +=10

        fruits_eaten += 1

        # Grow body

        squares.insert(0, squares[0][:])

        # Change of Speed

        if fruits_eaten % 3 == 0:
            level += 1
            speed = max(50, speed - 20)
    
    # Spawn new fruit

    if fruit_eaten:

        fr_x = random.randrange(1, width // 10) * 10
        fr_y = random.randrange(1, height // 10) * 10
        fruit_coor = [fr_x, fr_y]
        fruit_eaten = False

    # Gold apple eaten

    if gold_active and head_square[0] == gold_coor[0] and head_square[1] == gold_coor[1]:
        score += gold_weight
        fruits_eaten += 1
        gold_active = False
        squares.insert(0, squares[0][:])  # Grow body

        if fruits_eaten % 3 == 0:
            level += 1
            speed = max(50, speed - 20)

    # Randomly spawn gold apple (10% chance)

    if not gold_active and random.randint(1, 100) <= 10:
        gold_x = random.randrange(1, width // 10) * 10
        gold_y = random.randrange(1, height // 10) * 10
        gold_coor = [gold_x, gold_y]
        gold_timer = pygame.time.get_ticks()
        gold_active = True

    # Remove gold apple after 10 seconds

    if gold_active and pygame.time.get_ticks() - gold_timer > 10000:
        gold_active = False

    # Drawing section

    screen.fill((0, 0, 0))

    score_font = pygame.font.SysFont("times new roman", 20)
    score_surface = score_font.render(f"Score: {score} Level: {level}", True, (128, 128, 128))
    score_rect = score_surface.get_rect()

    screen.blit(score_surface,score_rect)

    # Regular apple

    if not fruit_eaten:
        pygame.draw.circle(screen, (255, 0, 0), (fruit_coor[0] + 5, fruit_coor[1] + 5), 5)

    # Gold apple

    if gold_active:
        pygame.draw.circle(screen, (255, 215, 0), (gold_coor[0] + 5, gold_coor[1] + 5), 6)

        # Draw timer above the gold apple

        time_left = max(0, 10 - (pygame.time.get_ticks() - gold_timer) // 1000)
        gold_font = pygame.font.SysFont("times new roman", 16)
        gold_timer_surface = gold_font.render(str(time_left), True, (255, 215, 0))
        gold_timer_rect = gold_timer_surface.get_rect(center=(gold_coor[0] + 5, gold_coor[1] - 10))
        screen.blit(gold_timer_surface, gold_timer_rect)



    for el in squares:
        pygame.draw.rect(screen, (0, 255, 64),
                         pygame.Rect(el[0], el[1], 10, 10))

    pygame.display.flip()
    pygame.time.delay(int(speed))

    # Save the game every time the fruit is eaten

    if fruit_eaten:
        save_game_state(user_id, squares, score, level, speed)

# Save the game before quitting

save_game_state(user_id, squares, score, level, speed)

pygame.quit()