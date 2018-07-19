import os
import logging
import objects
from interface import terminal_interface, python_interface
from interactions.lib import choices, conditions, events
from objects import item, entry
import core

log = logging.getLogger('game')


class Game(object):
    """
    main game object, holds everything.
    """

    def __init__(self, *args):
        self.args = args  # for future use?
        # components
        self.level_dir = core.levels_dir
        self.player = None
        self.interface = None
        self._interface_map = {
            'terminal': self.set_terminal_interface,
            'python': self.set_python_interface,
        }
        # flag holder
        self.game_flags = {}
        # level holder
        self.levels = {}
        # operation
        self.operating = False
        # navigation | menu
        self.menu_enter_location = None
        # navigation | screen
        self.screen_history = []
        self.next_screen = None
        self.current_screen = None
        self.previous_screen = None
        # navigation | scenes
        self.scene_history = []
        self.current_scene = None
        self.previous_scene = None
        # navigation | rooms
        self.room_history = []
        self.current_room = None
        self.previous_room = None
        # navigation | level
        self.level_history = []
        self.current_level = None
        self.previous_level = None
        super(Game, self).__init__()
    
    def set_flag(self, flag, value):
        self.game_flags[flag] = value

    def is_flag_value(self, flag, value, default=None):
        if default is None and flag not in self.game_flags:
            return False
        return bool(self.game_flags.get(flag, default) == value)
    
    def add_player(self):
        self.player = objects.player.Player()
        self.player.attach_game(self)
        # starting items
        self.player.inventory.add_item(item.crossbow)
        self.player.inventory.add_item(item.holy_cross)
        self.player.inventory.add_item(item.holy_water)
        self.player.inventory.add_item(item.flammable_oil)
        # starting journal
        self.player.journal.add_entry(entry.equipped)

    def set_terminal_interface(self):
        interface = terminal_interface.TerminalInterface(
            menu_choices=[choices.ChoiceInventory(), choices.ChoiceJournal()],
            choice_hook=self._choice_hook
        )
        self._set_interface(interface)

    def set_python_interface(self):
        interface = python_interface.PythonInterface(
            menu_choices=[choices.ChoiceInventory(), choices.ChoiceJournal()],
            # choice_hook=self._choice_hook
        )
        self._set_interface(interface)

    def set_interface(self, interface_type='terminal'):
        interface_init_func = self._interface_map[interface_type]
        interface_init_func()

    def _set_interface(self, interface):
        interface.attach_game(self)
        self.interface = interface

    def change_screen(self, screen):
        self.screen_history.append(screen)
        self.previous_screen = self.current_screen
        self.current_screen = screen
    
    def change_scene(self, scene):
        self.scene_history.append(scene)
        self.previous_scene = self.current_scene
        self.current_scene = scene

    def change_room(self, room):
        self.room_history.append(room)
        self.previous_room = self.current_room
        self.current_room = room

    def change_level(self, level):
        self.level_history.append(level)
        self.previous_level = self.current_level
        self.current_level = level

    def do_screen(self, screen):
        self.change_screen(screen)
        screen.set_seen()
        events_that_happened = self.handle_screen_events(screen)
        return events_that_happened

    def do_menu(self, menu):
        menu_scene = menu.generate_menu_scene()
        self.next_screen = menu_scene.get_current_screen()

    def handle_screen_events(self, screen):
        if not screen.events:
            return None
        events_that_happened = []
        for event in screen.events:
            event_result = self.handle_event(event)
            events_that_happened.append(event_result)
        return events_that_happened

    def handle_event(self, event):
        log.debug('handling event: event={}'.format(event))
        return event.do_event(self)

    def parse_choices(self, choice_list, return_all=False):
        """parses choices, enabling or disabling choices based on conditions"""
        return_list = []
        for choice in choice_list:
            if choice.conditions:
                self.handle_choice_conditions(choice)
            if choice.enabled or return_all:
                return_list.append(choice)

        return return_list

    def handle_choice_conditions(self, choice):
        # if any conditions disable the choice, we should return to prevent accidental enables,
        # but if they enable it - keep going so that we could disable it if needed,
        # and that it will be enabled if it was not enabled
        condition_modifier = self.check_conditions(choice.conditions, choice=choice)
        if condition_modifier == -1:
            choice.disable_choice()
        elif condition_modifier == 0:
            pass
        elif condition_modifier == 1:
            choice.enable_choice()
        else:
            log.error('illegal modifier for condition: modifier={} condition_list={}'.format(
                condition_modifier, choice.conditions))
            raise core.exceptions.GameRunTimeException('illegal modifier for condition: {}'.format(condition_modifier))

    def check_conditions(self, condition_list, **kwargs):
        """
        checks the conditions,
        if the list of conditions contains any conditions disable, will return -1
        if the list of conditions does not require any action, will return 0
        if the list of conditions should enable, will return 1
        :param condition_list:
        :return:
        """
        modifier = 0
        for condition in condition_list:
            log.debug('handling condition: condition={}'.format(condition))
            action = condition.check_condition(self, **kwargs)
            if action == -1:
                modifier = -1
                break
            elif action == 0:
                pass
            elif action == 1:
                modifier = 1
            else:
                log.error('invalid action for condition: action={} condition={}'.format(action, condition))
                raise core.exceptions.GameRunTimeException('invalid action for condition: {}'.format(action))
        return modifier

    def handle_choice(self, choice):
        log.debug('handling choice: choice={}'.format(choice))
        choice.make_choice(self)

    def save_menu_enter_location(self):
        self.menu_enter_location = (self.current_level, self.current_room, self.current_scene, self.current_screen)

    def _choice_hook(self, choice_string, decision):
        """hook choices the player makes to inject choices into decision choice list (for debugging or cheats)"""
        # inject choices holder
        inject_choices = [choices.ChoiceEnableDebugMode()]
        # list of debugging choices
        debug_choices = [
            choices.ChoiceNavigate('level1', key='level1',
                                   level='level_1', room='entrance_hall', hidden=True),
            choices.ChoiceNavigate('level2', key='level2',
                                   level='level_2', room='grande_hall', hidden=True),
        ]
        if self.is_flag_value('DEBUG', True):
            # add debug choices to inject choices
            inject_choices.extend(debug_choices)
            # check for magic Teleportation
            if choice_string.startswith('tele'):
                parts = choice_string.split()
                if len(parts) > 2:
                    tele = choices.ChoiceNavigate(*parts, key='tele', hidden=True)
                    inject_choices.append(tele)
                    choice_string = 'tele'  # let the Teleportation happen
                else:
                    log.debug('teleportation requires a level and a room (and optionally a scene)')

        # add all inject choices to the decision
        for inject_choice in inject_choices:
            decision.add_choice(inject_choice)

        # return choice string
        return choice_string

    def load_levels(self):
        # level_dirs = sorted(filter(lambda name: name.startswith('level'), os.listdir(self.level_dir)))
        level_dirs = ['level_1', 'level_2']  # todo: this is just for the beginning so i don't need to do it all
        for level_name in level_dirs:
            self.load_level(level_name)

    def load_level(self, level_name):
        """
        a level will be in the level dir with the same name as the level dir, with the same class name as the level
        loads levels from python files (for now)
        """
        level_file_path = '{}.py'.format(os.path.join(self.level_dir, level_name, level_name))
        level_class = core.load_class_from_file(level_file_path, level_name)
        self.add_new_level(level_name, level_class)

    def add_new_level(self, level_name, level_class):
        level = level_class()
        level.attach_game(self)
        level.load_rooms()
        self.levels[level_name] = level

    def set_opening_screen(self):
        opening_level = self.levels['level_1']
        opening_scene = opening_level.get_first_scene()
        opening_screen = opening_scene.get_first_screen()
        self.previous_level = self.current_level = opening_level
        self.previous_scene = self.current_scene = opening_scene
        self.previous_screen = self.current_screen = self.next_screen = opening_screen

    def start_game(self):
        self.set_opening_screen()
        self.operating = True
        self.interface.start()

    def get_state(self):
        """gets the 'state' of the game, what the screen should be"""
        return self.next_screen


def start_game(*args, **kwargs):
    game = Game(*args)
    game.add_player()
    game.set_interface(kwargs.get('interface', 'terminal'))
    game.load_levels()
    game.start_game()
    return game
