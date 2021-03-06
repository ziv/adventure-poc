import logging
from game_code import core

log = logging.getLogger('interactions.events')


class Result(object):

    def __init__(self, text):
        self.text = text
        super(Result, self).__init__()


class Event(object):
    """
    an event is how the game makes stuff happen, an event will add items to player inventory, or journal entries
    an event can toggle room or game variables
    an event could have conditions
    """
    def __init__(self, **kwargs):
        self.already_triggered = False
        self.can_trigger_multiple_times = kwargs.pop('can_trigger_multiple_times', False)
        self.conditions = kwargs.pop('conditions', [])
        super(Event, self).__init__()

    def do_event(self, game):
        if self.conditions and game.check_conditions(self.conditions) == -1:
            pass  # do nothing, conditions not met
            result = None
        elif self.already_triggered and not self.can_trigger_multiple_times:
            pass  # do nothing, already triggered
            result = None
        else:
            result = self._do_event(game)
        self.already_triggered = True
        return result

    def _do_event(self, game):
        raise NotImplementedError()


class AddItem(Event):
    """add an item to the inventory"""

    def __init__(self, item, **kwargs):
        self.item = item
        super(AddItem, self).__init__(**kwargs)

    def _do_event(self, game):
        game.player.inventory.add_item(self.item)
        return Result('Added an item to your Inventory: {}'.format(self.item.name))


class RemoveItem(Event):
    """remove an item from the inventory"""

    def __init__(self, item, **kwargs):
        self.item = item
        super(RemoveItem, self).__init__(**kwargs)

    def _do_event(self, game):
        game.player.inventory.remove_item(self.item)
        return Result('Removed an item from your Inventory: {}'.format(self.item.name))


class UnlockJournal(Event):
    """unlock a journal entry"""

    def __init__(self, entry, **kwargs):
        self.entry = entry
        super(UnlockJournal, self).__init__(**kwargs)

    def _do_event(self, game):
        game.player.journal.add_entry(self.entry)
        return Result('New entry in your Journal: {} '.format(self.entry.name))


class SetRoomScreen(Event):
    """sets the room to a specific screen"""

    def __init__(self, screen_key, level=None, room=None, **kwargs):
        self.screen_key = screen_key
        self.level = level
        self.room = room
        super(SetRoomScreen, self).__init__(**kwargs)

    def _do_event(self, game):
        if self.level:
            if not self.room:
                raise core.exceptions.GameConfigurationException(
                    'can not set room flag on specific level without specifying room')
            level = game.levels.get(self.level)
        else:
            level = game.current_level
        if self.room:
            room = level.rooms.get(self.room)
        else:
            room = game.current_room
        room.set_screen(self.screen_key)


class SetRoomFlag(Event):
    """sets a room flag"""

    def __init__(self, room_flag, set_to, level=None, room=None, **kwargs):
        self.room_flag = room_flag
        self.set_to = set_to
        self.level = level
        self.room = room
        super(SetRoomFlag, self).__init__(**kwargs)

    def _do_event(self, game):
        if self.level:
            if not self.room:
                raise core.exceptions.GameConfigurationException(
                    'can not set room flag on specific level without specifying room')
            level = game.levels.get(self.level)
        else:
            level = game.current_level
        if self.room:
            room = level.rooms.get(self.room)
        else:
            room = game.current_room
        room.set_flag(self.room_flag, self.set_to)


class SetRoomFlagTrue(SetRoomFlag):
    """set a room flag to True"""

    def __init__(self, room_flag, **kwargs):
        super(SetRoomFlagTrue, self).__init__(room_flag, set_to=True, **kwargs)


class SetRoomFlagFalse(SetRoomFlag):
    """set a room flag to False"""

    def __init__(self, room_flag, **kwargs):
        super(SetRoomFlagFalse, self).__init__(room_flag, set_to=False, **kwargs)
        
        
class SetGameFlag(Event):
    """sets a game flag"""

    def __init__(self, game_flag, set_to, **kwargs):
        self.game_flag = game_flag
        self.set_to = set_to
        super(SetGameFlag, self).__init__(**kwargs)

    def _do_event(self, game):
        game.set_flag(self.game_flag, self.set_to)


class SetGameFlagTrue(SetGameFlag):
    """set a game flag to True"""

    def __init__(self, game_flag, **kwargs):
        super(SetGameFlagTrue, self).__init__(game_flag, set_to=True, **kwargs)


class SetGameFlagFalse(SetGameFlag):
    """set a game flag to False"""

    def __init__(self, game_flag, **kwargs):
        super(SetGameFlagFalse, self).__init__(game_flag, set_to=False, **kwargs)
