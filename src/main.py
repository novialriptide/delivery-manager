"""DeliveryManager
A video game made for Rutgers University's
Creation of Game Society's Scarlet Game Jam
2022 Fall Semester.

author: Andrew Hong (andrewhong@myyahoo.com)
"""
from common import *
from utils import *
from models.connection import *
from models.maplevel import *
from models.node import *
from models.package import *
from models.truck import *
from models.ui.basebutton import *
import pygame
import time
import sys

# Misc Variables
holding_mousedown = False
holdin_shiftdown = False
camera_pos = pygame.Vector2(0, 0)
screen_scale = 0.5
target_fps = 120
shadow_distance = 8
start_time = time.time()
goal_time = start_time + TIME_TO_REACH_ENDGOAL
gas_loss = 0
dt = 0

# Scene Variables
DRAW_MAIN_WORLD = True
DRAW_TITLE_SCREEN = False
DRAW_DELIVERYTRUCK_UI = False
DRAW_WIN_SCREEN = False
DRAW_LOSE_SCREEN = False

# Initializing pygame
pygame.init()
pygame.freetype.init()
pygame.mixer.init()
_window = pygame.display.set_mode(
    pygame.Vector2(SCREEN_WIDTH, SCREEN_HEIGHT) * screen_scale, flags=pygame.RESIZABLE
)
pygame.display.set_caption(SCREEN_NAME)
screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), flags=pygame.SRCALPHA)
clock = pygame.time.Clock()

# Sounds
fanfare_snd = pygame.mixer.Sound("src/audio/fanfare.mp3")
chg_trk_snd = pygame.mixer.Sound("src/audio/change_truck_beep.wav")
gameover_snd = pygame.mixer.Sound("src/audio/gameover.wav")
repair_pkg_snd = pygame.mixer.Sound("src/audio/repair_package.wav")
slt_node_snd = pygame.mixer.Sound("src/audio/select_node_beep.wav")
srt_delivery_snd = pygame.mixer.Sound("src/audio/start_delivery_beep.wav")
music1 = pygame.mixer.Sound("src/audio/music1.mp3")

# Fonts
size20font = pygame.freetype.Font(FONT_PATH_REGULAR, 20)
size30font = pygame.freetype.Font(FONT_PATH_REGULAR, 30)
size40font = pygame.freetype.Font(FONT_PATH_REGULAR, 40)
size50font = pygame.freetype.Font(FONT_PATH_REGULAR, 50)
size60font = pygame.freetype.Font(FONT_PATH_REGULAR, 60)
size70font = pygame.freetype.Font(FONT_PATH_REGULAR, 70)

# Map Level Creation
map_center = pygame.Vector2(SCREEN_WIDTH, SCREEN_HEIGHT) / 2
map_level = MapLevel(map_center, INIT_NODES, INIT_CONNECTIONS_PER_NODE, MAP_RADIUS)
hq_node = Node(map_center, node_type=NODE_DELIVERY_HQ)
map_level.nodes.append(hq_node)
temp_nodes = copy.copy(map_level.nodes)
temp_nodes.remove(hq_node)

# Node, Connection, & Path Selection Variables & Game Setup
delivery_orders = []
delivery_trucks = []

for _ in range(INIT_CONNS_FROM_HQ):
    rand_node = random.choice(temp_nodes)
    result = map_level.add_conn(hq_node, rand_node)

for x in range(INIT_DELIVERY_TRUCKS):
    delivery_trucks.append(DeliveryTruck())


def add_package():
    global delivery_orders
    cost = random.randint(*PACKAGE_COST_RANGE)
    temp_nodes = copy.copy(map_level.nodes)
    temp_nodes.remove(hq_node)
    fragile = 0.2 > random.random()
    delivery_orders.append(
        Package(
            cost,
            round(cost * min(random.random(), 0.3), 2),
            random.choice(temp_nodes),
            is_fragile=fragile,
            max_dist=random.randint(*FAST_SHIPPING_RANGE)
            if FAST_SHIPPING_PROB > random.random()
            else -1,
        )
    )


balance = INIT_BALANCE
selected_truck = 0
selected_nodes = []
potential_path_conns = []
selected_package = 0
path_enabled = True
base_gas_price = INIT_GAS_GAL_PER_MILE_PRICE
gas_price = base_gas_price
changing_gas_price = False
destoying_a_truck = False
adding_package = False
random_events = ["disable_connection", "increase_gas_price"]


def start_delivery(package):
    global selected_package
    global delivery_orders
    global selected_nodes
    global gas_price
    global gas_loss
    global balance

    if selected_nodes[-1] != package.destination_node:
        return

    for t in delivery_trucks:
        if len(t.path) == 0:
            balance -= gas_loss
            gas_loss = 0
            delivery_orders.remove(package)
            selected_package = 0
            t.path = selected_nodes
            t.package = package
            break


for x in range(5):
    add_package()

# Buttons
class PreviousPackageButton(BaseButton):
    def on_click(self, mouse_pos):
        global selected_package
        if selected_package > 0:
            selected_package -= 1


class NextPackageButton(BaseButton):
    def on_click(self, mouse_pos):
        global selected_package
        global delivery_orders
        if selected_package < len(delivery_orders) - 1:
            selected_package += 1


previous_deliverytk_button = PreviousPackageButton(
    SCREEN_WIDTH / 2 - 300 / 2 - 100 - 300,
    SCREEN_HEIGHT - 75 - 150 + 50,
    300,
    75,
)

next_deliverytk_button = NextPackageButton(
    SCREEN_WIDTH / 2 - 300 / 2 + 100 + 300,
    SCREEN_HEIGHT - 75 - 150 + 50,
    300,
    75,
)


class StartDeliveryButton(BaseButton):
    def on_click(self, mouse_pos):
        global srt_delivery_snd
        srt_delivery_snd.play()
        start_delivery(delivery_orders[selected_package])


start_delivery_button = StartDeliveryButton(
    SCREEN_WIDTH / 2 - 200,
    SCREEN_HEIGHT - 75 - 150,
    400,
    150,
)

music1.play(loops=-1)

while True:
    # Game Loop
    mouse_pos = pygame.Vector2(pygame.mouse.get_pos()) / screen_scale

    if DRAW_MAIN_WORLD:
        # Draw Background
        screen.fill((50, 50, 50))

        # Draw Node Connections
        for c in map_level.connections:
            conn_color = (0, 255, 0)
            if c.blocked:
                conn_color = (255, 0, 0)
            elif c.bumpy:
                conn_color = (100, 100, 0)

            if (
                c in potential_path_conns
                and len(selected_nodes) != 0
                and selected_nodes[0].node_type == NODE_DELIVERY_HQ
            ):
                conn_color = (255, 0, 255)

            c.draw(screen, conn_color, width=7, offset=camera_pos)

        # Draw Nodes
        for n in map_level.nodes:
            node_color = (0, 0, 255)
            node_size_mod = 1
            if n.node_type == NODE_DELIVERY_HQ:
                node_color = (255, 0, 0)
                node_size_mod = 1.5

            if n in selected_nodes:
                node_color = (255, 255, 0)

            if n == delivery_orders[selected_package].destination_node:
                node_color = (255, 0, 255)

            pygame.draw.circle(
                screen,
                (20, 20, 20),
                n.position - camera_pos + pygame.Vector2(0, shadow_distance),
                NODE_DRAW_RADIUS * node_size_mod,
            )
            pygame.draw.circle(
                screen,
                pygame.Vector3(node_color) / 2,
                n.position - camera_pos,
                NODE_DRAW_RADIUS * node_size_mod,
            )
            pygame.draw.circle(
                screen,
                node_color,
                n.position - camera_pos,
                NODE_DRAW_RADIUS * node_size_mod,
                width=10,
            )

        # Draw Connection Distance on Top of the Node Connections and Nodes
        for c in map_level.connections:
            conn_color = (0, 255, 0)
            if c.blocked:
                conn_color = (255, 0, 0)
            elif c.bumpy:
                conn_color = (100, 100, 0)

            if (
                c in potential_path_conns
                and len(selected_nodes) != 0
                and selected_nodes[0].node_type == NODE_DELIVERY_HQ
            ):
                conn_color = (255, 0, 255)

            dist_text, dist_rect = size30font.render(f"{c.distance}m")
            node1 = pygame.Vector2(c.node1.position)
            node2 = pygame.Vector2(c.node2.position)
            dist_rect.size = pygame.Vector2(dist_rect.size) * 1.4
            pos = node1 - (node1 - node2) / 2
            dist_rect.center = pos
            pygame.draw.rect(screen, conn_color, dist_rect)
            screen.blit(dist_text, dist_rect.topleft)

        # Add Package
        if (
            int(goal_time - time.time()) % SECONDS_PER_PACKAGE == 0
            and not adding_package
        ):
            add_package()
            adding_package = True
        elif int(goal_time - time.time()) % SECONDS_PER_PACKAGE != 0:
            adding_package = False

        # Draw Delivery Trucks
        for t in delivery_trucks:
            if len(t.path) == 0:
                continue

            node_color = pygame.Vector3(255, 255, 255)
            node_size_mod = 0.7

            if t.current_conn is not None:
                if t.current_conn.bumpy and t.package.is_fragile:
                    t.package.health -= dt * HEALTH_DEC_SPEED

            if t.package.max_dist != -1:
                dist_traveled = t.dist_traveled(map_level)
                if t.package.max_dist < dist_traveled:
                    t.package.health -= dt * HEALTH_DEC_SPEED

            if t.package.health <= 0:
                balance -= t.package.cost
                t.reset_delivery()
                continue

            pygame.draw.circle(
                screen,
                (20, 20, 20),
                t.pos - camera_pos + pygame.Vector2(0, shadow_distance),
                NODE_DRAW_RADIUS * node_size_mod,
            )
            pygame.draw.circle(
                screen,
                pygame.Vector3(node_color) / 2,
                t.pos - camera_pos,
                NODE_DRAW_RADIUS * node_size_mod,
            )
            pygame.draw.circle(
                screen,
                node_color,
                t.pos - camera_pos,
                NODE_DRAW_RADIUS * node_size_mod,
                width=int(10 * node_size_mod),
            )
            health_text, health_rect = size30font.render(
                f"Health: {int(t.package.health)}", (255, 255, 255), (0, 0, 0)
            )
            screen.blit(health_text, t.pos - camera_pos)
            package = copy.deepcopy(t.package)
            if t.update(dt, map_level):
                balance += package.delivery_fee

        # Economy
        if int(goal_time - time.time()) % 2 == 0 and not changing_gas_price:
            gas_price = min(
                max(
                    base_gas_price, gas_price + random.random() * random.randint(-2, 2)
                ),
                MAX_GAS_PRICE,
            )
            changing_gas_price = True
        elif int(goal_time - time.time()) % 2 == 1:
            changing_gas_price = False

        gas_loss_str = ""
        gas_loss = 0
        total_dist_str = ""
        total_dist = 0
        if len(potential_path_conns) > 0:
            for x in potential_path_conns:
                gas_loss += x.distance * gas_price
                total_dist += x.distance
            total_dist_str = f"(Total Dist: {int(total_dist)})"

        bal_text, bal_rect = size40font.render(
            f"Balance: ${round(balance, 2)} {gas_loss_str}", (255, 255, 255)
        )
        screen.blit(bal_text, (25, 25))
        gas_text, gas_rect = size40font.render(
            f"Gas/Mile Price: {round(gas_price, 2)}", (255, 255, 255)
        )
        screen.blit(gas_text, (25, 25 + bal_rect.height + 10))
        time_text, time_rect = size40font.render(
            f"Time Left: {int(goal_time - time.time())} {total_dist_str}",
            (255, 255, 255),
        )
        screen.blit(time_text, (25, 25 + gas_rect.height + 10 + bal_rect.height + 10))

        # Delivery Truck UI Management Scene
        if DRAW_DELIVERYTRUCK_UI:
            border_radius = 10

            # Background
            pygame.draw.rect(
                screen,
                (100, 100, 100),
                (0, SCREEN_HEIGHT * 2 / 3, SCREEN_WIDTH, SCREEN_HEIGHT),
                border_radius=100,
            )

            # Start Delivery Button
            secondary_button_color = (200, 200, 200)
            button_color = pygame.Vector3(200, 0, 0)
            text_color = pygame.Vector3(0, 0, 0)
            if len(potential_path_conns) > 0 and len(delivery_orders) > 0:
                button_color = pygame.Vector3(0, 200, 0)
                text_color = pygame.Vector3(255, 255, 255)
                start_delivery_button.update(mouse_pos, holding_mousedown)

            pygame.draw.rect(
                screen, button_color / 2, start_delivery_button.rect, border_radius=50
            )
            pygame.draw.rect(
                screen,
                button_color,
                start_delivery_button.rect,
                width=20,
                border_radius=50,
            )
            text_surf, text_rect = size30font.render(
                "Start Delivery", fgcolor=text_color
            )
            screen.blit(
                text_surf,
                start_delivery_button.rect.center - pygame.Vector2(text_rect.size) / 2,
            )

            # Previous Delivery Button
            previous_deliverytk_button.update(mouse_pos, holding_mousedown)
            pygame.draw.rect(
                screen,
                secondary_button_color,
                previous_deliverytk_button.rect,
                border_radius=50,
            )
            text_surf, text_rect = size30font.render(
                "Previous Package", fgcolor=text_color
            )
            screen.blit(
                text_surf,
                previous_deliverytk_button.rect.center
                - pygame.Vector2(text_rect.size) / 2,
            )

            # Next Delivery Button
            next_deliverytk_button.update(mouse_pos, holding_mousedown)
            pygame.draw.rect(
                screen,
                secondary_button_color,
                next_deliverytk_button.rect,
                border_radius=50,
            )
            text_surf, text_rect = size30font.render("Next Package", fgcolor=text_color)
            screen.blit(
                text_surf,
                next_deliverytk_button.rect.center - pygame.Vector2(text_rect.size) / 2,
            )

            # Available Delivery Trucks
            available_trucks = 0
            for t in delivery_trucks:
                if len(t.path) == 0:
                    available_trucks += 1

            text = "No packages are available for delivery"
            if len(delivery_orders) > 0:
                text = f"Selected Package: {str(delivery_orders[selected_package])}"

            if available_trucks == 0:
                text = f"All of your trucks are busy."

            text_surf, text_rect = size30font.render(text, fgcolor=(0, 0, 0))
            screen.blit(
                text_surf,
                start_delivery_button.rect.center
                - pygame.Vector2(text_rect.size) / 2
                + pygame.Vector2(0, -120),
            )

    # Win Logic Implementation
    if balance >= MONEY_GOAL:
        DRAW_MAIN_WORLD = False
        fanfare_snd.play()
        screen.fill((0, 255, 0))
        text_surf, text_rect = size40font.render("You won!", (0, 0, 0))
        screen.blit(
            text_surf,
            pygame.Vector2(screen.get_size()) / 2
            - pygame.Vector2(text_surf.get_size()) / 2,
        )

    # Bankrupt Implementation
    if balance <= 0:
        DRAW_MAIN_WORLD = False
        gameover_snd.play()
        screen.fill((255, 0, 0))
        text_surf1, text_rect1 = size60font.render("You lost.", (0, 0, 0))
        screen.blit(
            text_surf1,
            pygame.Vector2(screen.get_size()) / 2
            - pygame.Vector2(text_surf1.get_size()) / 2,
        )
        text_surf2, text_rect2 = size40font.render(
            "You're bankrupt. Please reopen your game to try again.", (0, 0, 0)
        )
        screen.blit(
            text_surf2,
            pygame.Vector2(screen.get_size()) / 2
            + pygame.Vector2(0, text_surf1.get_height())
            - pygame.Vector2(text_surf2.get_size()) / 2,
        )

    # Ran out of Time Logic Implementation
    if goal_time - time.time() <= 0:
        DRAW_MAIN_WORLD = False
        gameover_snd.play()
        screen.fill((255, 0, 0))
        text_surf1, text_rect1 = size60font.render("You lost.", (0, 0, 0))
        screen.blit(
            text_surf1,
            pygame.Vector2(screen.get_size()) / 2
            - pygame.Vector2(text_surf1.get_size()) / 2,
        )
        text_surf2, text_rect2 = size40font.render(
            "You ran out of time. Please reopen your game to try again.", (0, 0, 0)
        )
        screen.blit(
            text_surf2,
            pygame.Vector2(screen.get_size()) / 2
            + pygame.Vector2(0, text_surf1.get_height())
            - pygame.Vector2(text_surf2.get_size()) / 2,
        )

    # Window Ratio Consistency
    temp_screen = pygame.transform.scale(screen, _window.get_size())
    _window.blit(temp_screen, (0, 0))
    pygame.display.flip()

    # Game Input
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # Window Ratio Consistency on Resize
        elif e.type == pygame.VIDEORESIZE:
            screen_scale = e.w / SCREEN_WIDTH
            screen_scaled = pygame.Vector2(SCREEN_WIDTH, SCREEN_HEIGHT) * screen_scale
            _window = pygame.display.set_mode(
                screen_scaled,
                flags=pygame.RESIZABLE,
            )

        elif e.type == pygame.KEYDOWN:
            if e.key == pygame.K_LSHIFT:
                holdin_shiftdown = True

            if e.key == pygame.K_TAB:
                DRAW_DELIVERYTRUCK_UI = not DRAW_DELIVERYTRUCK_UI

        elif e.type == pygame.KEYUP:
            if e.key == pygame.K_LSHIFT:
                holdin_shiftdown = False

        elif e.type == pygame.MOUSEBUTTONDOWN:
            holding_mousedown = True

            # Main World Inputs
            if not DRAW_DELIVERYTRUCK_UI:
                # Heal Trucks
                for t in delivery_trucks:
                    if len(t.path) > 0 and circle_collision(
                        mouse_pos,
                        t.pos - camera_pos,
                        NODE_DRAW_RADIUS * node_size_mod * 1.5,
                    ):
                        repair_pkg_snd.play()
                        t.package.health += CLICK_HEAL
                        balance -= HEAL_COST

                # Node Unselection Detection
                if not holdin_shiftdown:
                    col = False
                    for x in selected_nodes:
                        if circle_collision(mouse_pos, x.position, NODE_DRAW_RADIUS):
                            col = True
                            break

                    if len(selected_nodes) != 0 and not col:
                        selected_nodes = []
                        potential_path_conns = []
                        path_enabled = True

                # Node Singular Selection Detection
                for n in map_level.nodes:
                    dist = mouse_pos.distance_squared_to(n.position)
                    if circle_collision(mouse_pos, n.position, NODE_DRAW_RADIUS):
                        # Another Node Unselection Detection
                        if n in selected_nodes and not holdin_shiftdown:
                            selected_nodes = []
                            potential_path_conns = []
                            path_enabled = True
                            break

                        # Node Multi Selection Detection
                        elif n in selected_nodes and holdin_shiftdown:
                            selected_nodes.append(n)
                            slt_node_snd.play()
                            break

                        selected_nodes.append(n)
                        slt_node_snd.play()

                        # Connection Path Selection
                        if len(selected_nodes) >= 2 and path_enabled:
                            path_enabled = True
                            n1 = selected_nodes[len(selected_nodes) - 1]
                            n2 = selected_nodes[len(selected_nodes) - 2]
                            found_conn = False
                            for c in map_level.connections:
                                if (c.node1 == n1 and c.node2 == n2) or (
                                    c.node2 == n1 and c.node1 == n2
                                ):
                                    potential_path_conns.append(c)
                                    found_conn = True

                            if not found_conn:
                                potential_path_conns = []
                                path_enabled = False

                        break

        elif e.type == pygame.MOUSEBUTTONUP:
            holding_mousedown = False

    # Node Selected Drag
    if holding_mousedown and not DRAW_DELIVERYTRUCK_UI:
        if len(selected_nodes) == 1:
            selected_nodes[0].position = mouse_pos

    # Delta Time Logic
    dt = clock.tick(target_fps) / target_fps
