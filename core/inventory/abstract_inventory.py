from abc import ABC, abstractmethod

class AbstractInventory(ABC):
    def __init__(self, bag_type="普通背包"):
        self.bag_type = bag_type

    @abstractmethod
    def add(self, item):
        pass

    @abstractmethod
    def remove(self, item_name, count=1):
        pass

    @abstractmethod
    def use(self, item_name, user):
        pass

    @abstractmethod
    def list_items(self):
        pass

    def get_bag_type(self):
        return self.bag_type
