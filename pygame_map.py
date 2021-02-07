# IMPORTS
import math
import pyautogui as auto
import pygame
from pygame.locals import *
from random import random, randrange
import socket
import sys
import time
from log_errors import log_function
from colors import *

"""
# Keep player centered on screen
# Track player position in reference to the level map
# Move the level map according to the player input
The level map moves which gives the illusion of movement
The player position is tracked and updated which allows for collisions and triggers
The player image however will always remain in the center of the screen


To save the world that developer builds, simply save all of the values stored
in the variable block_list

"""


# CONSTANTS
PORT = 55600
SERVER = "192.168.0.1" # Put the address of the computer that will host the server code
ADDR = (SERVER, PORT)
PACKET_SIZE = 4096
SCREEN_WIDTH, SCREEN_HEIGHT = auto.size()
SCREEN_HEIGHT = SCREEN_HEIGHT - int(SCREEN_HEIGHT * .05)
GAME_CLOCK = pygame.time.Clock()
GAME_BACKGROUND = (255,255,255)
USER_SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
USER_SCREEN.convert()
BLOCK_WIDTH = 50
BLOCK_HEIGHT = 50
MAP_WIDTH = 1500
MAP_HEIGHT = 500
SPAWN_POSITIONS = [(500,500), (5000, 5000), (5050, 5050)]
WORLDBUILDER_COLOR_INDEX_LENGTH = 35
# LEVEL SIZE
# LEVEL_ONE_SURFACE = pygame.Surface((int(SCREEN_WIDTH*10), int(SCREEN_HEIGHT*10)))
LEVEL_ONE_SURFACE = pygame.Surface((MAP_WIDTH,MAP_HEIGHT))


# VARIABLES
runGame = True
#loc_dict[x_location][y_location]/["length"]/["otherValues"]
loc_dict = {} # loc_dict = {
              #     x_location: {
              #         y_location: {
              #             length: int, "0": values, "1": values, "2": values
              #                     }
              #                 }
              #            }

leftBoundary = 500
rightBoundary = -MAP_WIDTH+500
topBoundary = 500
bottomBoundary = -MAP_HEIGHT+260

player_loc = (0,0)
allow_left_move = True
allow_right_move = True
allow_up_move = True
allow_down_move = True
allow_left_up_move = True
allow_right_up_move = True
allow_left_down_move = True
allow_right_down_move = True
WAIT_FOR = 100
movement_wait = 0
allowed_to_move = True
diag = False

functions_loop_order = []
world_blocks = []
player_number = 0
block_number = 0
developer_mode = False
holding_click = False
rect_x = None
rect_y = None
moving_left = False
moving_right = False
moving_up = False
moving_down = False
movement_speed = 50
player_loc = (int(SCREEN_WIDTH/2),int(SCREEN_HEIGHT/2)) # Initial position of the player is in the middle of the screen
screen_x = 0
screen_y = 0
offset_x = -screen_x # The screen value must be the exact opposite of the offset value
offset_y = -screen_y

player_x, player_y = player_loc
player_width = 25
player_height = 25

# ENTITIES
players_list = {}


def create_player_dict(key,value):
    global player_number
    players_list[player_number] = {key:value}
    player_number += 1
    return players_list[player_number-1] # return the entity in the list



def add_player_dict(p_id,key,value):
    players_list[p_id][key] = value

block_list = {} # Stores all of the blocks in the game and their surface locations NOTE: THESE ARE NOT screen coordinates but surface coordinates!


def create_block_dict(value,color,loc_values):
    """This function is used to add block data to the block dictionary for future use in other systems. Block_list is used for rendering blocks, while loc_dict dictionary used here is for the other game systems."""
    # block_list is for rendering blocks, loc_dict is for other systems
    global block_number
    temp_checker = 0
    # TODO Get the values of block_list and save them to a database like sqlite3
    for i in range(0,block_number):
        # if block is already there/ if it is a duplicate:
        if value in block_list[i].values():
            # Change the color of the block if it is necessary
            if block_list[i]["color"] != color:
                block_list[i]["color"] = color
            temp_checker += 1
            return block_list[i] # return the entity in the list
        else:
            pass
    if temp_checker == 0: # If the values are not found in block_list, ie: it's a new block location
        block_list[block_number] = {"rect":value, "color":color}
        # Add values to the LOCATION DICTIONARY
        loc_dict_x,loc_dict_y,*loc_dict_other = value
        loc_dict_x = str(loc_dict_x)
        loc_dict_y = str(loc_dict_y)

        if loc_dict_x in loc_dict.keys(): # if the x is a key
            if loc_dict_y in loc_dict[loc_dict_x].keys(): # if the y is a key
                length = loc_dict[loc_dict_x][loc_dict_y]["length"] # Store the number of items layered at that block
                loc_dict[loc_dict_x][loc_dict_y][str(length)] = loc_values # store the values at the current index
                loc_dict[loc_dict_x][loc_dict_y]["length"] = length+1 # increase the number of items on the block by one
            else: # That block doesn't exist yet, but there are other blocks in the same column
                loc_dict[loc_dict_x][loc_dict_y] = {}
                loc_dict[loc_dict_x][loc_dict_y]["0"] = loc_values
                loc_dict[loc_dict_x][loc_dict_y]["length"] = 1
        else: # if neither x nor y are yet keys
            loc_dict[loc_dict_x] = {}
            loc_dict[loc_dict_x][loc_dict_y] = {}
            loc_dict[loc_dict_x][loc_dict_y]["0"] = loc_values
            loc_dict[loc_dict_x][loc_dict_y]["length"] = 1
        block_number += 1
        return block_list[block_number-1] # return the entity in the list
    return None


# TESTING


def collision_check():
    """Checks if there are collidable objects surrounding the player. If so then values are set to false that should prevent the player from moving."""
    #TODO This appears to work, but once it blocks a player one time, it won't let that player walk that direction again!
    
    # GRAB THE VALUE OF THE player ROUNDED TO THE NEAREST 50
    global mouse_x
    global mouse_y
    global allow_left_move
    global allow_right_move
    global allow_up_move
    global allow_down_move
    global allow_left_up_move
    global allow_right_up_move
    global allow_left_down_move
    global allow_right_down_move

    # USE THAT VALUE TO SEARCH FOR THE BLOCKS all round it
    # USE THE RESULTS FROM THESE BLOCKS TO DETERMINE WHICH DIRECTIONS A PLAYER CAN MOVE
    # IF A PLAYER CAN MOVE A CERTAIN DIRECTION AND CHOOSES TO; ALLOW THE MOVE, OTHERWISE DONT ALLOW IT

    # Store the number of items in each block

    #GET Player loc
    x,y = player_loc
    x,y = rectCoordsToSurfaceCoords((x,y,BLOCK_WIDTH,BLOCK_HEIGHT))

    # FOUR CARDINAL DIRECTIONS
    try: # LEFT
        left_val = loc_dict[str(x - BLOCK_WIDTH)][str(y)]["length"]
    except Exception as e:
        left_val = "clear"
    try: # RIGHT
        right_val = loc_dict[str(x + BLOCK_WIDTH)][str(y)]["length"]
    except Exception as e:
        right_val = "clear"
    try: # UP
        up_val = loc_dict[str(x)][str(y - BLOCK_HEIGHT)]["length"]
    except Exception as e:
        up_val = "clear"
    try: # DOWN
        down_val = loc_dict[str(x)][str(y + BLOCK_HEIGHT)]["length"]
    except Exception as e:
        down_val = "clear"

    if left_val != "clear" and left_val > 0: # If there are items at the location go through each item
        for i in range(0,left_val):
            if loc_dict[str(x - BLOCK_WIDTH)][str(y)][str(i)]["isCollidable"] == True:
                allow_left_move = False
    if right_val != "clear" and right_val > 0: # If there are items at the location go through each item
        for i in range(0,right_val):
            if loc_dict[str(x + BLOCK_WIDTH)][str(y)][str(i)]["isCollidable"] == True:
                allow_right_move = False
    if up_val != "clear" and up_val > 0: # If there are items at the location go through each item
        for i in range(0,up_val):
            if loc_dict[str(x)][str(y - BLOCK_HEIGHT)][str(i)]["isCollidable"] == True:
                allow_up_move = False
    if down_val != "clear" and down_val > 0: # If there are items at the location go through each item
        for i in range(0,down_val):
            if loc_dict[str(x)][str(y + BLOCK_HEIGHT)][str(i)]["isCollidable"] == True:
                allow_down_move = False
    
    # DIAGONALS

    # You can walk diagonally as long as there are not collidables on either side of the direction you are walking

    # LEFT-UP
    if allow_left_move == False and allow_up_move == False:
        allow_left_up_move = False
    else: # If the space is not being blocked, check to make sure that the block itself is empty
        try:
            left_up_val = loc_dict[str(x - BLOCK_WIDTH)][str(y - BLOCK_HEIGHT)]["length"]
        except:
            left_up_val = "clear"
        if left_up_val != "clear" and left_up_val > 0: # If there are items at the location go through each item
            for i in range(0,left_up_val):
                if loc_dict[str(x - BLOCK_WIDTH)][str(y - BLOCK_HEIGHT)][str(i)]["isCollidable"] == True:
                    allow_left_up_move = False
    # LEFT-DOWN
    if allow_left_move == False and allow_down_move == False:
        allow_left_down_move = False
    else:
        try:
            left_down_val = loc_dict[str(x - BLOCK_WIDTH)][str(y + BLOCK_HEIGHT)]["length"]
        except:
            left_down_val = "clear"
        if left_down_val != "clear" and left_down_val > 0: # If there are items at the location go through each item
            for i in range(0,left_down_val):
                if loc_dict[str(x - BLOCK_WIDTH)][str(y + BLOCK_HEIGHT)][str(i)]["isCollidable"] == True:
                    allow_left_down_move = False
    # RIGHT-UP
    if allow_right_move == False and allow_up_move == False:
        allow_right_up_move = False
    else:
        try:
            right_up_val = loc_dict[str(x + BLOCK_WIDTH)][str(y - BLOCK_HEIGHT)]["length"]
        except:
            right_up_val = "clear"
        if right_up_val != "clear" and right_up_val > 0: # If there are items at the location go through each item
            for i in range(0,right_up_val):
                if loc_dict[str(x + BLOCK_WIDTH)][str(y - BLOCK_HEIGHT)][str(i)]["isCollidable"] == True:
                    allow_right_up_move = False
    # RIGHT-DOWN
    if allow_right_move == False and allow_down_move == False:
        allow_right_down_move = False
    else:
        try:
            right_down_val = loc_dict[str(x + BLOCK_WIDTH)][str(y + BLOCK_HEIGHT)]["length"]
        except:
            right_down_val = "clear"
        if right_down_val != "clear" and right_down_val > 0: # If there are items at the location go through each item
            for i in range(0,right_down_val):
                if loc_dict[str(x + BLOCK_WIDTH)][str(y + BLOCK_HEIGHT)][str(i)]["isCollidable"] == True:
                    allow_right_down_move = False



# FUNCTIONS


def check_for_quit(event): # Press escape to quit the game
    global runGame
    if event.type == KEYDOWN:
        if event.key == pygame.K_ESCAPE:
            runGame = False



def create_world(): # Create the world
    pass



def create_player(username):
    global USER
    USER = create_player_dict("username", username)
    print(USER)
    # USER["location"] = (100,200)
    # print(USER)

def getBlockCenter(x,y):
    """Return the center coordinates of a block that the item should be drawn on, based on how large the screen is"""
    #Find which block the coordinate falls in (blocks are created from top left corner)
    _block_x_val = int(x/50)
    _block_y_val = int(y/50)
    _player_block_x, _player_block_y = (_block_x_val*BLOCK_WIDTH, _block_y_val*BLOCK_HEIGHT)
    # Find the center of the block
    block_center_location = ((_player_block_x+int(BLOCK_WIDTH/2)),(_player_block_y+int(BLOCK_HEIGHT/2)))
    return block_center_location

def getCoordsOnSurface(x,y):
    x = x - int(BLOCK_WIDTH/2)
    y = y - int(BLOCK_HEIGHT/2)
    return (x,y)

def login_connect_to_server():
    pass



def login_set_screen():
    pass
    


def login():
    print("Logging In")
    username = "WarKing"
    functions_loop_remove(login)
    return username
    # username = input("Username?")
    # password = input("password?")
    # if username == "WarKing" and password == "123":
    #     functions_loop_remove(login)
    #     return username
    # else:
    #     login()



def functions_loop_append(function):
    functions_loop_order.append(function)



def functions_loop_remove(function):
    functions_loop_order.remove(function)



def functions_loop():
    global functions_loop_order
    global movement_wait
    global allowed_to_move
    global WAIT_FOR
    # print(f"Ofsset_X: {offset_x}, Offset_Y: {offset_y}")
    if movement_wait == WAIT_FOR:
        allowed_to_move = True
        movement_wait = 0
    elif movement_wait < WAIT_FOR:
        movement_wait += 1
    else:
        print("ERROR: variable 'movement_wait' is more than the max 50, how did this happen!?")

    for event in pygame.event.get():
        check_for_quit(event)
        check_for_developer_mode(event)
        world_builder(event)
        zoom(event)

    if holding_click:
        create_dev_block()
    for item in functions_loop_order:
        if item == login:
            logged_in_user = item()
            create_player(logged_in_user)
        else:
            item()
    move_screen()



def network_loop():
    pass


def move_screen():
    global screen_x, screen_y, offset_x, offset_y
    global allowed_to_move, diag
    global allow_left_down_move, allow_left_up_move, allow_right_down_move, allow_right_up_move, allow_left_move, allow_right_move, allow_up_move, allow_down_move
    if (moving_left and moving_up) or (moving_left and moving_down):
        diag = True 
    if (moving_right and moving_up) or (moving_right and moving_down):
        diag = True
    
    # DIAGONALS
    if diag:
        if moving_left and moving_up and developer_mode:
            if allowed_to_move and allow_left_up_move:
                screen_x += movement_speed
                offset_x = -screen_x
                screen_y += movement_speed
                offset_y = -screen_y
                allowed_to_move = False
            if screen_x >= leftBoundary: # Boundary Left
                screen_x = leftBoundary
                ofsset_x = -screen_x
            if screen_y >= topBoundary: # Boundary Top
                screen_y = topBoundary
                offset_y = -screen_y
            allow_left_up_move = True
            diag = False
        if moving_left and moving_down and developer_mode:
            if allowed_to_move and allow_left_down_move:
                screen_x += movement_speed
                offset_x = -screen_x
                screen_y -= movement_speed
                offset_y = -screen_y
                allowed_to_move = False
            if screen_x >= leftBoundary: # Boundary Left
                screen_x = leftBoundary
                ofsset_x = -screen_x
            if screen_y <= bottomBoundary: # Boundary Bottom
                screen_y = bottomBoundary
                offset_y = -screen_y
            allow_left_down_move = True
            diag = False
        if moving_right and moving_up and developer_mode:
            if allowed_to_move and allow_right_up_move:
                screen_x -= movement_speed
                offset_x = -screen_x
                screen_y += movement_speed
                offset_y = -screen_y
                allowed_to_move = False
            if screen_x <= rightBoundary: # Boundary Right
                screen_x = rightBoundary
                offset_x = -screen_x
            if screen_y >= topBoundary: # Boundary Top
                screen_y = topBoundary
                offset_y = -screen_y
            allow_right_up_move = True
            diag = False
        if moving_right and moving_down and developer_mode:
            if allowed_to_move and allow_right_down_move:
                screen_x -= movement_speed
                offset_x = -screen_x
                screen_y -= movement_speed
                offset_y = -screen_y
                allowed_to_move = False
            if screen_x <= rightBoundary: # Boundary Right
                screen_x = rightBoundary
                offset_x = -screen_x
            if screen_y <= bottomBoundary: # Boundary Bottom
                screen_y = bottomBoundary
                offset_y = -screen_y
            allow_right_down_move = True
            diag = False

    # FOUR CARDINAL DIRECTIONS
    else:
        if moving_left and developer_mode:
            if screen_x >= leftBoundary: # Boundary Left
                screen_x = leftBoundary
                ofsset_x = -screen_x
            else:
                if allowed_to_move and allow_left_move:
                    screen_x += movement_speed
                    offset_x = -screen_x
                    allowed_to_move = False

        if moving_right and developer_mode:
            if screen_x <= rightBoundary: # Boundary Right
                screen_x = rightBoundary
                offset_x = -screen_x
            else:
                if allowed_to_move and allow_right_move:
                    screen_x -= movement_speed
                    offset_x = -screen_x
                    allowed_to_move = False

        if moving_up and developer_mode:
            if screen_y >= topBoundary: # Boundary Top
                screen_y = topBoundary
                offset_y = -screen_y
            else:
                if allowed_to_move and allow_up_move:
                    screen_y += movement_speed
                    offset_y = -screen_y
                    allowed_to_move = False

        if moving_down and developer_mode:
            if screen_y <= bottomBoundary: # Boundary Bottom
                screen_y = bottomBoundary
                offset_y = -screen_y
            else:
                if allowed_to_move and allow_down_move:
                    screen_y -= movement_speed
                    offset_y = -screen_y
                    allowed_to_move = False
    # reset values #TODO This doesn't seem like the correct place to reset these values. There must be a better spot for this.
    allow_left_move = True
    allow_right_move = True
    allow_up_move = True
    allow_down_move = True



def render_screen():
    # Shows the level on the user screen, with the level offset according to the screen_x and screen_y
    USER_SCREEN.blit(LEVEL_ONE_SURFACE, (screen_x,screen_y))
    # USER_SCREEN.blit(LEVEL_ONE_SURFACE, (0,0))



def render_blocks():
    """data: block_list[block]["rect"]"""
    for block_key, block_value in block_list.items():
        try:
            b_color = None
            b_rect = None
            # Grab the rect and color values from the block_list dictionary
            for block_second_key, block_second_value in block_value.items():
                if block_second_key == "rect":
                    b_rect = block_second_value
                if block_second_key == "color":
                    b_color = block_second_value
            if b_color != None and b_rect != None:
                pygame.draw.rect(LEVEL_ONE_SURFACE, b_color, b_rect)
        except Exception as e:
            print(f"ERROR: {e}/{block_number}")



def render_dev_tools():
    if developer_mode:
        mouse_x, mouse_y = pygame.mouse.get_pos()
        # The square get drawns on the user_screen and never shows up off the screen
        # The square is slightly to the right of the mouse
        pygame.draw.rect(USER_SCREEN, world_builder_list[current_wb], (mouse_x+20,mouse_y,20,20))


def render_player():
    pygame.draw.circle(USER_SCREEN, RED, player_loc, 25)


def render_loop():
    render_screen()
    render_blocks()
    render_dev_tools()
    render_player()
    pygame.display.update()
    USER_SCREEN.fill(GAME_BACKGROUND)
    mouse_x, mouse_y = pygame.mouse.get_pos()


def save_world():
    for item in block_list.values():
        print(f"SAVING ITEMS: {item}")

def screenToSurface(x,y):
    """Converts a screen coordinate position to a surface coordinate position utilizing the offset values. Returns the surface coordinates."""
    x += offset_x
    y += offset_y
    return (x,y)

def rectCoordsToSurfaceCoords(rect):
    """The main reason for this function is to determine which block a rectangle is a part of so that checks can be done around the rectangle for collision, combat, a* algorithm, etc.
    NOTE: The rectangle passed in must have the coordinates of the screen and not of the surface. Otherwise it is offsetting the surface coords from their actual surface location!"""
    x,y,w,h = rect
    # get the center location
    # Why do I need this step? What benefit does the center coords have over the top-left coords?, The reason is it standardizes every input regardless of where the square or circle was drawn. This function requires that it is a rect value that is passed in. So even if a circle is passed in it first has to be converted to rect. This ensures a consistent way of looking at things.
    x,y = getBlockCenter(x,y)
    # convert this screen location to the surface location utilizing the offset
    x,y = screenToSurface(x,y)
    # go from a center location back to the rect location so that the x,y values can be used to grab the correct index
    x,y = getCoordsOnSurface(x,y)
    return (x,y)

def zoom(event):
    if not developer_mode:
        if event.type == MOUSEBUTTONDOWN:
                if event.button == 4: # Mouse scroll upwards
                    print("Zooming In")
                elif event.button == 5: # Mouse scroll downwards
                    print("Zooming Out")
                    



def game_loop():
    while runGame:
        functions_loop()
        network_loop()
        render_loop()



def game_startup():
    global player_loc
    pygame.init()
    pygame.display.set_caption("Tripple F - Formations, Family, Friends")
    USER_SCREEN.fill(GAME_BACKGROUND)
    LEVEL_ONE_SURFACE.fill(BLUE)
    functions_loop_append(login)
    player_loc = getBlockCenter(player_x,player_y)



def game_shutdown():
    # Send server logout signal
    
    pygame.quit()   #logout of pygame
    quit()  #logout of program



def main():
    game_startup()
    game_loop()
    game_shutdown()

# EXECUTIONS
# for column in range(0,MAP_HEIGHT):
#     for row in range(0,MAP_WIDTH):
#         create_block(row*BLOCK_WIDTH, column*BLOCK_HEIGHT, GREEN)


# DEVELOPER TOOLS
            
def check_for_developer_mode(event):
    global developer_mode, moving_left, moving_right, moving_up, moving_down
    if event.type == KEYDOWN:
        collision_check()
        if event.key == pygame.K_d:
            developer_mode = not developer_mode
            save_world()
        if event.key == pygame.K_LEFT:
            moving_left = True
        elif event.key == pygame.K_RIGHT:
            moving_right = True
        elif event.key == pygame.K_UP:
            moving_up = True
        elif event.key == pygame.K_DOWN:
            moving_down = True

    if event.type == KEYUP:
        if event.key == pygame.K_LEFT:
            moving_left = False
        elif event.key == pygame.K_RIGHT:
            moving_right = False
        elif event.key == pygame.K_UP:
            moving_up = False
        elif event.key == pygame.K_DOWN:
            moving_down = False

world_builder_list = COLORS
current_wb = 0



def create_dev_block():
    """Create a colored block at the given screen location which gets added to the surface below the screen."""
    global mouse_x
    global mouse_y
    x,y = rectCoordsToSurfaceCoords((mouse_x,mouse_y,BLOCK_WIDTH,BLOCK_HEIGHT))
    create_block_dict((x, y,BLOCK_WIDTH,BLOCK_HEIGHT), world_builder_list[current_wb], ({"isCollidable": True}))
    


def world_builder(event):
    if developer_mode:
        global current_wb
        global holding_click
        global rect_x
        global rect_y
        global mouse_x
        global mouse_y
        mouse_x, mouse_y = pygame.mouse.get_pos()
        if event.type == MOUSEBUTTONDOWN:
            if event.button == 4: # Mouse scroll upwards
                current_wb -= 1
                if current_wb < 0:
                    current_wb = WORLDBUILDER_COLOR_INDEX_LENGTH
            elif event.button == 5: # Mouse scroll downwards
                current_wb += 1
                if current_wb > WORLDBUILDER_COLOR_INDEX_LENGTH:
                    current_wb = 0
            elif event.button == 1:
                holding_click = True
        elif event.type == MOUSEBUTTONUP:
            if event.button == 1 and holding_click == True: # if the user lets up on the mouse button
                holding_click = False
main()