import math

class Paginator:
    def __init__(self, array: list | tuple, page: int = 1, quantity_page: int = 1):
        self.array = array
        self.quantity_page = quantity_page
        self.page = page
        self.len = len(self.array)
        self.pages = math.ceil(self.len / self.quantity_page)
        
    def __get_slice(self):
        start = (self.page - 1) * self.quantity_page
        stop = start + self.quantity_page
        return self.array[start:stop]
    
    def get_page(self):
        page_items = self.__get_slice()
        return page_items
    
    def has_naxt(self):
        if self.page < self.pages:
            return self.page + 1
        return False
    
    def has_previous(self):
        if self.page > 1:
            return self.page - 1
        return False
    
class List_of_Carts:
    def __init__(self, array: list | tuple):
        self.array = array
        self.len = len(self.array)
        
    def __get_carts_to_self(self):
        return self.array
    
    def get_carts(self):
        carts_items = self.__get_carts_to_self()
        return carts_items