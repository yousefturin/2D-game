import arcade
import os


# Constants
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 800
SCREEN_TITLE = "SUPERPUBER"

# Constants used to scale our sprites from their original size
CHARACTER_SCALING = 0.8
TILE_SCALING = 0.5
COIN_SCALING = 0.5
key_SCALING = 0.5
SPRITE_PIXEL_SIZE = 128
GRID_PIXEL_SIZE = (SPRITE_PIXEL_SIZE * TILE_SCALING)

# Speed of player
PLAYER_MOVEMENT_SPEED = 5
GRAVITY = 1
PLAYER_JUMP_SPEED = 20

# Pixel Scrolling

LEFT_VIEWPORT_MARGIN = 250
RIGHT_VIEWPORT_MARGIN = 250
BOTTOM_VIEWPORT_MARGIN = 50
TOP_VIEWPORT_MARGIN = 100

PLAYER_START_X = SPRITE_PIXEL_SIZE * TILE_SCALING * 2
PLAYER_START_Y = 400

# Facing constants
RIGHT_FACING = 0
LEFT_FACING = 1


def load_texture_pair(filename):
    return [
        arcade.load_texture(filename), arcade.load_texture(filename, mirrored=True)
    ]


class PlayerCharacter(arcade.Sprite):

    def __init__(self):

        # Set up parent class
        super().__init__()

        # Default to face-right
        self.character_face_direction = RIGHT_FACING

        # Used for flipping between image sequences
        self.cur_texture = 0
        self.scale = CHARACTER_SCALING

        # Track our state
        self.jumping = False
        self.climbing = False
        self.is_on_ladder = False

        # Textures
        main_path = ":resources:images/animated_characters/female_person/femaleperson"

        # Textures for idle standing
        self.idle_texture_pair = load_texture_pair(f"{main_path}_idle.png")
        self.jump_texture_pair = load_texture_pair(f"{main_path}_jump.png")
        self.fall_texture_pair = load_texture_pair(f"{main_path}_fall.png")

        # Load textures for walking
        self.walk_textures = []
        for i in range(8):
            texture = load_texture_pair(f"{main_path}_walk{i}.png")
            self.walk_textures.append(texture)

        # Load textures for climbing
        self.climbing_textures = []
        texture = arcade.load_texture(f"{main_path}_climb0.png")
        self.climbing_textures.append(texture)
        texture = arcade.load_texture(f"{main_path}_climb1.png")
        self.climbing_textures.append(texture)

        # Set the initial texture
        self.texture = self.idle_texture_pair[0]
        self.set_hit_box(self.texture.hit_box_points)

    def update_animation(self, delta_time: float = 1 / 60):

        # Climbing animation
        if self.is_on_ladder:
            self.climbing = True
        if not self.is_on_ladder and self.climbing:
            self.climbing = False
        if self.climbing and abs(self.change_y) > 1:
            self.cur_texture += 1
            if self.cur_texture > 7:
                self.cur_texture = 0
        if self.climbing:
            self.texture = self.climbing_textures[self.cur_texture // 4]
            return

        # Face left / right
        if self.change_x < 0 and self.character_face_direction == RIGHT_FACING:
            self.character_face_direction = LEFT_FACING
        elif self.change_x > 0 and self.character_face_direction == LEFT_FACING:
            self.character_face_direction = RIGHT_FACING

        # Jumping animation
        if self.change_y > 0 and not self.is_on_ladder:
            self.texture = self.jump_texture_pair[self.character_face_direction]
            return
        elif self.change_y < 0 and not self.is_on_ladder:
            self.texture = self.fall_texture_pair[self.character_face_direction]
            return

        # idle animation
        if self.change_x == 0:
            self.texture = self.idle_texture_pair[self.character_face_direction]
            return

        # walking animation
        self.cur_texture += 1
        if self.cur_texture > 7:
            self.cur_texture = 0
        self.texture = self.walk_textures[self.cur_texture][self.character_face_direction]


class MyGame(arcade.Window):
    """
    Main application class.
    """

    def __init__(self):

        # Call the parent class and set up the window
        super().__init__(SCREEN_WIDTH, SCREEN_HEIGHT, SCREEN_TITLE, fullscreen=True)

        # Setting the path to start with this program
        file_path = os.path.dirname(os.path.abspath(__file__))
        os.chdir(file_path)
        """""
        width, height = self.get_size()
        self.set_viewport(0, width, 0, height)
        """""

        # Track the current state of what key is pressed
        self.left_pressed = False
        self.right_pressed = False
        self.up_pressed = False
        self.down_pressed = False
        self.jump_needs_reset = False
        self.game_over = False
        self.end_of_map = False

        self.coin_list = None
        self.wall_list = None
        self.dont_touch_list = None
        self.player_list = None
        self.background_list = None
        self.ladder_list = None
        self.enemy_list = None
        self.moving_wall_list = None
        self.key_list = None
        self.health_list = None

        # Separate variable that holds the player sprite
        self.player_sprite = None

        # Our engine
        self.physics_engine = None

        self.view_bottom = 0
        self.view_left = 0

        # Level
        self.level = 1

        # Our score
        self.score = 0

        # Our score
        self.score_key = 0

        self.end_of_map = 0

        # Player Health
        self.health = 3

        # Load sounds
        self.collect_coin_sound = arcade.load_sound(":resources:sounds/coin1.wav")
        self.collect_key_sound = arcade.load_sound(":resources:sounds/coin4.wav")
        self.collect_health_sound = arcade.load_sound(":resources:sounds/upgrade1.wav")
        self.jump_sound = arcade.load_sound(":resources:sounds/jump1.wav")
        # self.game_sound = arcade.load_sound(":resources:sounds/Super Mario Bros.ogg")
        self.game_finish = arcade.load_sound(":resources:sounds/gameover2.wav")
        self.game_danc = arcade.load_sound(":resources:sounds/dancing funeral.wav")

    def setup(self, level):
        """ Set up the game here. Call this function to restart the game. """

        # arcade.play_sound(self.game_sound)  # We need to check again

        self.view_bottom = 0
        self.view_left = 0
        self.game_over = False

        # Create the Sprite lists
        self.player_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()
        self.background_list = arcade.SpriteList()
        self.coin_list = arcade.SpriteList()
        self.key_list = arcade.SpriteList()
        self.health_list = arcade.SpriteList()
        self.enemy_list = arcade.SpriteList()
        self.moving_wall_list = arcade.SpriteList()

        # Set up the player
        self.player_sprite = PlayerCharacter()
        self.player_sprite.center_x = PLAYER_START_X
        self.player_sprite.center_y = PLAYER_START_Y
        self.player_list.append(self.player_sprite)
        self.score_key = 0

        # We will add the map here...

        platforms_layer_name = 'Platforms'
        coins_layer_name = 'Coins'
        dont_touch_layer_name = "Don't Touch"
        moving_platforms_layer_name = 'Moving Platforms'
        key_layer_name = 'key'
        health_layer_name = 'health'

        # Map name
        map_name = f":resources:tmx_maps/ws500_{level}.tmx"

        # Read in the tiled map
        my_map = arcade.tilemap.read_tmx(map_name)

        # Calculate the right edge of the my_map in pixels
        self.end_of_map = my_map.map_size.width * GRID_PIXEL_SIZE

        # PLATFORMS
        self.wall_list = arcade.tilemap.process_layer(my_map, platforms_layer_name, TILE_SCALING)

        #  Moving Platforms
        moving_platforms_list = arcade.tilemap.process_layer(my_map, moving_platforms_layer_name, TILE_SCALING)
        for sprite in moving_platforms_list:
            self.wall_list.append(sprite)

        # -- Background objects
        self.background_list = arcade.tilemap.process_layer(my_map, "Background", TILE_SCALING)

        # Background objects
        self.ladder_list = arcade.tilemap.process_layer(my_map, "Ladder", TILE_SCALING)

        # Coins
        self.coin_list = arcade.tilemap.process_layer(my_map, coins_layer_name, TILE_SCALING)
        # key
        self.key_list = arcade.tilemap.process_layer(my_map, key_layer_name, TILE_SCALING)
        # health
        self.health_list = arcade.tilemap.process_layer(my_map, health_layer_name, TILE_SCALING)

        # Create the 'physics engine'
        self.physics_engine = arcade.PhysicsEnginePlatformer(self.player_sprite,
                                                             self.wall_list,
                                                             gravity_constant=GRAVITY,
                                                             ladders=self.ladder_list)

        # Don't Touch Layer
        self.dont_touch_list = arcade.tilemap.process_layer(my_map, dont_touch_layer_name, TILE_SCALING)

        if self.level == 1:
            # Draw a enemy on the platform1 for level 1
            enemy = arcade.Sprite(":resources:images/enemies/wormGreen.png", CHARACTER_SCALING / 2)

            enemy.bottom = GRID_PIXEL_SIZE * 17

            # for the position of the enemy
            enemy.left = GRID_PIXEL_SIZE * 19

            enemy.boundary_right = GRID_PIXEL_SIZE * 5
            enemy.boundary_left = GRID_PIXEL_SIZE * 2

            # Set enemy initial speed
            enemy.change_x = 2.5
            self.enemy_list.append(enemy)

            # Draw a enemy on the platform2 for level 1
            enemy = arcade.Sprite(":resources:images/enemies/wormGreen.png", CHARACTER_SCALING / 2)

            enemy.bottom = GRID_PIXEL_SIZE * 9

            # for the position of the enemy
            enemy.left = GRID_PIXEL_SIZE * 7

            enemy.boundary_right = GRID_PIXEL_SIZE * 5
            enemy.boundary_left = GRID_PIXEL_SIZE * 2

            # Set enemy initial speed
            enemy.change_x = 2.5
            self.enemy_list.append(enemy)

            # Draw a enemy on the platform2
            enemy = arcade.Sprite(":resources:images/enemies/fly.png", CHARACTER_SCALING / 2)

            enemy.bottom = GRID_PIXEL_SIZE * 3

            # for the position of the enemy
            enemy.left = GRID_PIXEL_SIZE * 22

            enemy.boundary_right = GRID_PIXEL_SIZE * 5
            enemy.boundary_left = GRID_PIXEL_SIZE * 2

            # Set enemy initial speed
            enemy.change_x = 3
            self.enemy_list.append(enemy)

            # Draw a enemy on the platform3
            enemy = arcade.Sprite(":resources:images/enemies/fly.png", CHARACTER_SCALING / 2)

            enemy.bottom = GRID_PIXEL_SIZE * 3

            # for the position of the enemy
            enemy.left = GRID_PIXEL_SIZE * 30

            enemy.boundary_right = GRID_PIXEL_SIZE * 5
            enemy.boundary_left = GRID_PIXEL_SIZE * 2

            # Set enemy initial speed
            enemy.change_x = 3
            self.enemy_list.append(enemy)

            # Draw a enemy on the platform4
            enemy = arcade.Sprite(":resources:images/enemies/fly.png", CHARACTER_SCALING / 2)

            enemy.bottom = GRID_PIXEL_SIZE * 3

            # for the position of the enemy
            enemy.left = GRID_PIXEL_SIZE * 60

            enemy.boundary_right = GRID_PIXEL_SIZE * 5
            enemy.boundary_left = GRID_PIXEL_SIZE * 2

            # Set enemy initial speed
            enemy.change_x = 3
            self.enemy_list.append(enemy)

        if self.level == 2:
            # Draw a enemy on the platform1 for level 1
            enemy = arcade.Sprite(":resources:images/enemies/wormGreen.png", CHARACTER_SCALING / 2)

            enemy.bottom = GRID_PIXEL_SIZE * 16

            # for the position of the enemy
            enemy.left = GRID_PIXEL_SIZE * 19

            enemy.boundary_right = GRID_PIXEL_SIZE * 5
            enemy.boundary_left = GRID_PIXEL_SIZE * 2

            # Set enemy initial speed
            enemy.change_x = 3
            self.enemy_list.append(enemy)

            # Draw a enemy on the platform2 for level 1
            enemy = arcade.Sprite(":resources:images/enemies/wormGreen.png", CHARACTER_SCALING / 2)

            enemy.bottom = GRID_PIXEL_SIZE * 23

            # for the position of the enemy
            enemy.left = GRID_PIXEL_SIZE * 50

            enemy.boundary_right = GRID_PIXEL_SIZE * 5
            enemy.boundary_left = GRID_PIXEL_SIZE * 2

            # Set enemy initial speed
            enemy.change_x = 3
            self.enemy_list.append(enemy)

            # Draw a enemy on the platform2
            enemy = arcade.Sprite(":resources:images/enemies/fly.png", CHARACTER_SCALING / 2)

            enemy.bottom = GRID_PIXEL_SIZE * 15

            # for the position of the enemy
            enemy.left = GRID_PIXEL_SIZE * 50

            enemy.boundary_right = GRID_PIXEL_SIZE * 5
            enemy.boundary_left = GRID_PIXEL_SIZE * 2

            # Set enemy initial speed
            enemy.change_x = 3
            self.enemy_list.append(enemy)

            # Draw a enemy on the platform3
            enemy = arcade.Sprite(":resources:images/enemies/fly.png", CHARACTER_SCALING / 2)

            enemy.bottom = GRID_PIXEL_SIZE * 40

            # for the position of the enemy
            enemy.left = GRID_PIXEL_SIZE * 50

            enemy.boundary_right = GRID_PIXEL_SIZE * 5
            enemy.boundary_left = GRID_PIXEL_SIZE * 2

            # Set enemy initial speed
            enemy.change_x = 3
            self.enemy_list.append(enemy)

            # Draw a enemy on the platform4
            enemy = arcade.Sprite(":resources:images/enemies/fly.png", CHARACTER_SCALING / 2)

            enemy.bottom = GRID_PIXEL_SIZE * 29

            # for the position of the enemy
            enemy.left = GRID_PIXEL_SIZE * 8

            enemy.boundary_right = GRID_PIXEL_SIZE * 5
            enemy.boundary_left = GRID_PIXEL_SIZE * 2

            # Set enemy initial speed
            enemy.change_x = 3
            self.enemy_list.append(enemy)

        if self.level == 3:
            # Draw a enemy on the platform1 for level 1
            enemy = arcade.Sprite(":resources:images/enemies/wormGreen.png", CHARACTER_SCALING / 2)

            enemy.bottom = GRID_PIXEL_SIZE * 26

            # for the position of the enemy
            enemy.left = GRID_PIXEL_SIZE * 14

            enemy.boundary_right = GRID_PIXEL_SIZE * 5
            enemy.boundary_left = GRID_PIXEL_SIZE * 2

            # Set enemy initial speed
            enemy.change_x = 3
            self.enemy_list.append(enemy)

            # Draw a enemy on the platform2 for level 1
            enemy = arcade.Sprite(":resources:images/enemies/wormGreen.png", CHARACTER_SCALING / 2)

            enemy.bottom = GRID_PIXEL_SIZE * 41

            # for the position of the enemy
            enemy.left = GRID_PIXEL_SIZE * 15

            enemy.boundary_right = GRID_PIXEL_SIZE * 5
            enemy.boundary_left = GRID_PIXEL_SIZE * 2

            # Set enemy initial speed
            enemy.change_x = 3
            self.enemy_list.append(enemy)

            # Draw a enemy on the platform2
            enemy = arcade.Sprite(":resources:images/enemies/fly.png", CHARACTER_SCALING / 2)

            enemy.bottom = GRID_PIXEL_SIZE * 15

            # for the position of the enemy
            enemy.left = GRID_PIXEL_SIZE * 47

            enemy.boundary_right = GRID_PIXEL_SIZE * 5
            enemy.boundary_left = GRID_PIXEL_SIZE * 2

            # Set enemy initial speed
            enemy.change_x = 3
            self.enemy_list.append(enemy)

            # Draw a enemy on the platform3
            enemy = arcade.Sprite(":resources:images/enemies/fly.png", CHARACTER_SCALING / 2)

            enemy.bottom = GRID_PIXEL_SIZE * 15

            # for the position of the enemy
            enemy.left = GRID_PIXEL_SIZE * 110

            enemy.boundary_right = GRID_PIXEL_SIZE * 5
            enemy.boundary_left = GRID_PIXEL_SIZE * 2

            # Set enemy initial speed
            enemy.change_x = 3
            self.enemy_list.append(enemy)

            # Draw a enemy on the platform4
            enemy = arcade.Sprite(":resources:images/enemies/fly.png", CHARACTER_SCALING / 2)

            enemy.bottom = GRID_PIXEL_SIZE * 28

            # for the position of the enemy
            enemy.left = GRID_PIXEL_SIZE * 56

            enemy.boundary_right = GRID_PIXEL_SIZE * 5
            enemy.boundary_left = GRID_PIXEL_SIZE * 2

            # Set enemy initial speed
            enemy.change_x = 3
            self.enemy_list.append(enemy)

    def on_draw(self):
        """ Render the screen. """

        # Clear the screen to the background color
        arcade.start_render()
        # Draw our sprites
        self.wall_list.draw()
        self.background_list.draw()
        self.ladder_list.draw()
        self.coin_list.draw()
        self.key_list.draw()
        self.player_list.draw()
        self.dont_touch_list.draw()
        self.enemy_list.draw()
        self.moving_wall_list.draw()
        self.health_list.draw()
        if self.game_over:
            arcade.draw_text("Game Over", 330 + self.view_left, self.view_bottom + 200, arcade.color.BLACK, 30)
            arcade.draw_text("Do You Want To Restart ?", 260 + self.view_left, self.view_bottom + 150, arcade.color.
                             BLACK, 30)
            arcade.set_background_color(arcade.csscolor.DARK_RED)

        # For Showing Score
        score_text = f"Score: {self.score}"
        arcade.draw_text(score_text, 10 + self.view_left, 710 + self.view_bottom, arcade.csscolor.WHITE, 18)

        # For Showing Score_key
        score_key = f"Key: {self.score_key}/3"
        arcade.draw_text(score_key, 10 + self.view_left, 690 + self.view_bottom, arcade.csscolor.WHITE, 18)

        # For showing Health
        score_health = f"Health: {self.health}"
        arcade.draw_text(score_health, 10 + self.view_left, 750 + self.view_bottom, arcade.csscolor.WHITE, 18)

        # For showing Level
        score_level = f"Level: {self.level}"
        arcade.draw_text(score_level, 10 + self.view_left, 730 + self.view_bottom, arcade.csscolor.WHITE, 18)
        if self.level == 1:
            arcade.set_background_color(arcade.csscolor.CORNFLOWER_BLUE)
        if self.level == 2:
            arcade.set_background_color(arcade.csscolor.SNOW)
        if self.level == 3:
            arcade.set_background_color(arcade.csscolor.LIGHT_GOLDENROD_YELLOW)

    """
        #create a wall for the end of the map ,but its make the game so slowly
        if self.score_key != 3:
            for y in range(0, 500, 1000):
                wall = arcade.Sprite(":resources:images/tiles/boxCrate_double.png", TILE_SCALING)
                wall.center_x = 465
                wall.center_y = y
                self.wall_list.append(wall)
                """
    def process_keychange(self):
        # Called when we change a key up/down or we move on/off a ladder.

        # process up/down
        if self.up_pressed and not self.down_pressed:
            if self.physics_engine.is_on_ladder():
                self.player_sprite.change_y = PLAYER_MOVEMENT_SPEED
            elif self.physics_engine.can_jump() and not self.jump_needs_reset:
                self.player_sprite.change_y = PLAYER_JUMP_SPEED
                self.jump_needs_reset = True
                arcade.play_sound(self.jump_sound)
        elif self.down_pressed and not self.up_pressed:
            if self.physics_engine.is_on_ladder():
                self.player_sprite.change_y = -PLAYER_MOVEMENT_SPEED

        # Process up/down when no movement
        if self.physics_engine.is_on_ladder():
            if not self.up_pressed and not self.down_pressed:
                self.player_sprite.change_y = 0
            elif self.up_pressed and self.down_pressed:
                self.player_sprite.change_y = 0

        # process left/right
        if self.right_pressed and not self.left_pressed:
            self.player_sprite.change_x = PLAYER_MOVEMENT_SPEED
        elif self.left_pressed and not self.right_pressed:
            self.player_sprite.change_x = -PLAYER_MOVEMENT_SPEED
        else:
            self.player_sprite.change_x = 0

    def on_key_press(self, key, modifiers):  # Keyboard functions
        if key == arcade.key.UP or key == arcade.key.W:
            self.up_pressed = True
        elif key == arcade.key.DOWN or key == arcade.key.S:
            self.down_pressed = True
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.left_pressed = True
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.right_pressed = True
        if key == arcade.key.F:
            # User hits f. Flip between full and not full screen.
            self.set_fullscreen(not self.fullscreen)

            width, height = self.get_size()
            self.set_viewport(0, width, 0, height)

        if key == arcade.key.ESCAPE:
            # User hits s. Flip between full and not full screen.
            self.set_fullscreen(not self.fullscreen)

            self.set_viewport(0, SCREEN_WIDTH, 0, SCREEN_HEIGHT)
        if key == arcade.key.Y:
            self.game_over = False
            # MyGame()
            arcade.set_background_color(arcade.csscolor.CORNFLOWER_BLUE)

        self.process_keychange()

    def on_key_release(self, key, modifiers):

        if key == arcade.key.UP or key == arcade.key.W:
            self.up_pressed = False
            self.jump_needs_reset = False
        elif key == arcade.key.DOWN or key == arcade.key.S:
            self.down_pressed = False
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.left_pressed = False
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.right_pressed = False

        self.process_keychange()

    def on_update(self, delta_time):

        # We're calling physics engine
        self.physics_engine.update()

        # Update animations
        if self.physics_engine.can_jump():
            self.player_sprite.can_jump = False
        else:
            self.player_sprite.can_jump = True

        if self.physics_engine.is_on_ladder() and not self.physics_engine.can_jump():
            self.player_sprite.is_on_ladder = True
            self.process_keychange()
        else:
            self.player_sprite.is_on_ladder = False
            self.process_keychange()
        self.enemy_list.update()
        self.coin_list.update_animation(delta_time)
        self.key_list.update_animation(delta_time)
        self.player_list.update_animation(delta_time)
        self.health_list.update_animation(delta_time)
        self.ladder_list.draw()
        # Update walls, used with moving platforms
        self.wall_list.update()

        # Update the player based on the physics engine
        if not self.game_over:
            # Move the enemies
            self.enemy_list.update()

        # Check each enemy
        for enemy in self.enemy_list:
            # If the enemy hit a wall, reverse
            if len(arcade.check_for_collision_with_list(enemy, self.wall_list)) > 0:
                enemy.change_x *= -1

        # See if the wall hit a boundary and needs to reverse direction.
        for wall in self.wall_list:

            if wall.boundary_right and wall.right > wall.boundary_right and wall.change_x > 0:
                wall.change_x *= -1
            if wall.boundary_left and wall.left < wall.boundary_left and wall.change_x < 0:
                wall.change_x *= -1
            if wall.boundary_top and wall.top > wall.boundary_top and wall.change_y > 0:
                wall.change_y *= -1
            if wall.boundary_bottom and wall.bottom < wall.boundary_bottom and wall.change_y < 0:
                wall.change_y *= -1

        # if you hit any coins
        coin_hit_list = arcade.check_for_collision_with_list(self.player_sprite, self.coin_list)

        for coin in coin_hit_list:
            self.score += 1
            # Remove the coin
            coin.remove_from_sprite_lists()
            # Play sound
            arcade.play_sound(self.collect_coin_sound)

        # if you hit any key
        key_hit_list = arcade.check_for_collision_with_list(self.player_sprite, self.key_list)

        for key in key_hit_list:
            self.score_key += 1
            # Remove the key
            key.remove_from_sprite_lists()
            # Play sound
            arcade.play_sound(self.collect_key_sound)

        # if you hit any health
        health_hit_list = arcade.check_for_collision_with_list(self.player_sprite, self.health_list)

        for health in health_hit_list:
            self.health += 1
            # Remove the health
            health.remove_from_sprite_lists()
            # Play sound
            arcade.play_sound(self.collect_health_sound)
        changed_viewport = False

        # if player falls
        if self.player_sprite.center_y < -100:
            self.player_sprite.center_x = PLAYER_START_X
            self.player_sprite.center_y = PLAYER_START_Y

            # Set the camera
            self.view_left = 0
            self.view_bottom = 0
            changed_viewport = True
            self.health -= 1
            arcade.play_sound(self.game_finish)

        # Did the player touch something they should not?anything
        if arcade.check_for_collision_with_list(self.player_sprite, self.dont_touch_list):
            self.player_sprite.change_x = 0
            self.player_sprite.change_y = 0
            self.player_sprite.center_x = PLAYER_START_X
            self.player_sprite.center_y = PLAYER_START_Y
            self.health -= 1
            arcade.play_sound(self.game_finish)
        # Did the player touch something they should not?anything
        if arcade.check_for_collision_with_list(self.player_sprite, self.enemy_list):
            self.player_sprite.change_x = 0
            self.player_sprite.change_y = 0
            self.player_sprite.center_x = PLAYER_START_X
            self.player_sprite.center_y = PLAYER_START_Y
            self.health -= 1
            arcade.play_sound(self.game_finish)

        # See if the user got to the end of the level
            """
        if self.player_sprite.center_x >= self.end_of_map:
            # Advance to the next level
            self.level += 1
            # Load the next level
            self.setup(self.level)

            # Set the camera to the start
            self.view_left = 0
            self.view_bottom = 0
            changed_viewport = True
            """

        if self.health == 0:
            self.game_over = True

        if self.score == 50:
            self.health += 1
            self.score = 0

        if self.score_key == 3:
            if self.player_sprite.center_x >= self.end_of_map:
                self.level += 1
                # Load the next level
                self.setup(self.level)
                self.view_left = 0
                self.view_bottom = 0
                changed_viewport = True

        # Manage Scrolling

        # Scroll left
        left_boundary = self.view_left + LEFT_VIEWPORT_MARGIN
        if self.player_sprite.left < left_boundary:
            self.view_left -= left_boundary - self.player_sprite.left
            changed_viewport = True

        # Scroll right
        right_boundary = self.view_left + SCREEN_WIDTH - RIGHT_VIEWPORT_MARGIN
        if self.player_sprite.right > right_boundary:
            self.view_left += self.player_sprite.right - right_boundary
            changed_viewport = True

        # Scroll up
        top_boundary = self.view_bottom + SCREEN_HEIGHT - TOP_VIEWPORT_MARGIN
        if self.player_sprite.top > top_boundary:
            self.view_bottom += self.player_sprite.top - top_boundary
            changed_viewport = True

        # Scroll down
        bottom_boundary = self.view_bottom + BOTTOM_VIEWPORT_MARGIN
        if self.player_sprite.bottom < bottom_boundary:
            self.view_bottom -= bottom_boundary - self.player_sprite.bottom
            changed_viewport = True

        if changed_viewport:
            self.view_bottom = int(self.view_bottom)
            self.view_left = int(self.view_left)

            # Done the Scrolling

            arcade.set_viewport(self.view_left, SCREEN_WIDTH + self.view_left, self.view_bottom,
                                SCREEN_HEIGHT + self.view_bottom)


def main():
    """ Main method """
    window = MyGame()
    window.setup(window.level)
    arcade.run()


if __name__ == "__main__":
    main()
