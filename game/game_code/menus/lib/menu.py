from game_code.interactions import menu


class Menu(object):

    def __init__(self, name):
        self.name = name
        self.game = None
        super(Menu, self).__init__()

    def attach_game(self, game):
        self.game = game

    @property
    def menu_items(self):
        """should iterate the menu items"""
        raise NotImplementedError()

    def generate_menu_scene(self):
        # todo: @inbar add easy navigation to menus? (by level?)
        menu_screen = menu.Menu(
            name=self.name,
            menu_items=self.menu_items
        )
        return menu_screen
