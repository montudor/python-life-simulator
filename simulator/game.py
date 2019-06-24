from . import errors
import random

class Actor(object):
    events = []
    ticks = 0
    _loaded = False

    def __init__(self, game, *args, **kwargs):
        self.game = game
        self.config = game.get_config()
        self.first_name = kwargs.get("first_name", None)
        self.last_name = kwargs.get("last_name", None)
        self.primary = kwargs.get("primary", False)
        self.tier = kwargs.get("tier", None)
        self.age = kwargs.get("age", 0)

    def __str__(self):
        return "%s %s" % (self.first_name, self.last_name)

    def load_events(self):
        if self.primary:
            if self.tier is None:
                raise errors.InvalidConfig()
            self.events = []
            for event in self.config["events"]["primary"][self.tier]:
                self.events.append(Event(
                    self.game,
                    text=event.get("text", "Event occured"),
                    type=event.get("type", None),
                ))
        self._loaded = True
        return self.events

    def trigger_random_event(self):
        if not self._loaded:
            self.load_events()

        if len(self.events) == 0:
            return "Nothing happened!"

        key = random.randint(0, len(self.events)-1)
        event = self.events[key]
        del self.events[key]
        return event.get_event_text()

    def tick(self):
        if self.ticks > 0:
            self.age += 1
        update_tier = None
        for tier in self.config["events"]["meta"]["tiers"]:
            if update_tier == True:
                self.tier = tier["key"]
                self.load_events()
                break
            if tier["key"] == self.tier:
                if tier["ages"][1] < self.age:
                    update_tier = True
                    continue
                break
        self.ticks += 1
        return self.trigger_random_event()


class Person(object):
    pass


class Event(object):
    def __init__(self, game, *args, **kwargs):
        self.game = game
        self.type = kwargs.get("type", None)
        self.text = kwargs.get("text", "Something happened")
    
    def get_event_text(self, *args, **kwargs):
        return self.text.format(
            actor=self.game.current_actor
        )


class Game(object):
    config = None
    _name_pool = None
    active = False

    def __init__(self, *args, **kwargs):
        self.config_file = kwargs.get("config", "default_config.json")

    def get_config(self):
        if self.config is not None:
            return self.config
        with open(self.config_file, "r") as file:
            import json
            self.config = json.loads(file.read())
        return self.config

    def get_name_pool(self, force_gen=False):
        if self._name_pool is not None and force_gen is not True:
            return self._name_pool
        config = self.get_config()
        names = []

        first_names = []
        for key, items in config["names"]["first_names"].items():
            for name in config["names"]["first_names"][key]:
                first_names.append(name)

        for fn in first_names:
            for ln in config["names"]["last_names"]:
                names.append("%s %s" % (fn, ln))
        self._name_pool = names
        return names

    def get_starter_tier(self):
        for tier in self.config.get("events", {}).get("meta", {}).get("tiers", [None]):
            if tier is None:
                raise errors.InvalidConfig()
            if tier.get("start", None) is True:
                return tier.get("key", None)
            else:
                continue
        else:
            raise errors.InvalidConfig()

    def generate_actor(self):
        name_pool = self.get_name_pool()
        pos = random.randint(0, len(name_pool)-1)
        name = name_pool[pos]
        del name_pool[pos]
        actor_name = name.split(" ")
        actor = Actor(
            self,
            first_name=actor_name[0],
            last_name=actor_name[1],
            primary=True,
            tier=self.get_starter_tier()
        )
        return actor

    def new(self):
        self._name_pool = self.get_name_pool(force_gen=True)
        self.current_actor = self.generate_actor()
        self.active = True

    def tick(self):
        return self.current_actor.tick()
