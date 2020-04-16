
from .record import Record


class CoreferenceGroup(Record):
    __attributes__ = ['items']

    def __init__(self, first):
        self.items = [first]

    def __iter__(self):
        return iter(self.items)

    @property
    def first(self):
        return self.items[0]

    def includes(self, item):
        return all(
            item.same_as(_)
            for _ in self.items
        )

    def add(self, item):
        self.items.append(item)


class CoreferenceGroups(Record):
    __attributes__ = ['groups']

    def __init__(self):
        self.groups = []

    def __iter__(self):
        return iter(self.groups)

    def add(self, item):
        for group in self.groups:
            if group.includes(item):
                group.add(item)
                break
        else:
            group = CoreferenceGroup(item)
            self.groups.append(group)
