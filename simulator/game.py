from . import errors
import random

class Person(object):
    GENDER_MALE = 1
    GENDER_FEMALE = 2
    GENDER_RANDOM = 3
    GENDER_OTHER = 4

    def __init__(self, *args, **kwargs):
        self.first_name = kwargs.get("first_name", None)
        self.last_name = kwargs.get("last_name", None)
        self.set_gender(kwargs.get("gender", self.GENDER_RANDOM))

    def set_gender(self, gender):
        if gender in [self.GENDER_MALE, self.GENDER_FEMALE, self.GENDER_OTHER]:
            self.gender = gender
        elif gender == self.GENDER_RANDOM:
            self.gender = random.choice([self.GENDER_MALE, self.GENDER_FEMALE])
        else:
            self.gender = self.GENDER_OTHER

    def get_gender_text(self):
        if self.gender == self.GENDER_MALE:
            return "male"
        elif self.gender == self.GENDER_FEMALE:
            return "female"
        else:
            return "other"

    def __str__(self):
        return self.name

    @property
    def name(self):
        return "%s %s" % (self.first_name, self.last_name)


class Actor(Person):
    events = []
    people = {
        "family": {
            "mother": None,
            "father": None
        },
        "friends": {
            "best_friend": None
        },
        "relationship": {
            "person": None,
            "type": None
        }
    }
    ticks = 0
    _loaded = False

    def __init__(self, game, *args, **kwargs):
        self.game = game
        self.config = game.get_config()
        self.first_name = kwargs.get("first_name", None)
        self.last_name = kwargs.get("last_name", None)
        self.gender = kwargs.get("gender", None)
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


class Event(object):
    def __init__(self, game, *args, **kwargs):
        self.game = game
        self.type = kwargs.get("type", None)
        self.text = kwargs.get("text", "Something happened")
    
    def get_event_text(self, *args, **kwargs):
        return self.text.format(
            actor=self.game.current_actor,
            gender=self.game.current_actor.get_gender_text().capitalize()
        )


class Game(object):
    config = None
    _people_pool = None
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

    def get_people(self, force_gen=False):
        if self._people_pool is not None and force_gen is not True:
            return self._people_pool
        config = self.get_config()
        people = []

        first_names = []
        for key, items in config["names"]["first_names"].items():
            for name in config["names"]["first_names"][key]:
                genders = []
                duplicate = False
                if key == "male":
                    genders = [Person.GENDER_MALE]
                elif key == "female":
                    genders = [Person.GENDER_FEMALE]
                elif key == "gender_neutral":
                    genders = [Person.GENDER_MALE, Person.GENDER_FEMALE, Person.GENDER_OTHER]
                else:
                    gender = Person.GENDER_OTHER
                for gender in genders:
                    first_names.append(
                        {
                            "first_name": name,
                            "gender": gender
                        }
                    )

        for person in first_names:
            for ln in config["names"]["last_names"]:
                new = Person(
                    first_name=person["first_name"],
                    last_name=ln,
                    gender=person["gender"]
                )
                people.append(new)
        self._people_pool = people
        return people

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
        pool = self.get_people()
        pos = random.randint(0, len(pool)-1)
        person = pool[pos]
        del pool[pos]
        actor = Actor(
            self,
            first_name=person.first_name,
            last_name=person.last_name,
            gender=person.gender,
            primary=True,
            tier=self.get_starter_tier()
        )
        return actor

    def new(self):
        self.get_people(force_gen=True)
        self.current_actor = self.generate_actor()
        self.active = True

    def tick(self):
        return self.current_actor.tick()
