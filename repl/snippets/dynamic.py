class AttrDict(dict):
    def __init__(self, *args, **kwargs):
        super(AttrDict, self).__init__(*args, **kwargs)
        self.__dict__ = self


def basemodel_getattr(self, name):
    try:
        contents = object.__getattribute__(self, "contents")
        if name in contents:
            return contents[name]
        else:
            raise AttributeError
    except AttributeError:
        pass
    try:
        collections = object.__getattribute__(self, "collections")
        if name in collections:
            return collections[name]
        else:
            raise AttributeError
    except AttributeError:
        pass
    return object.__getattribute__(self, name)


setattr(BaseModel, "__getattr__", basemodel_getattr)


def basemodel_getitem(self, key) -> Any:
    try:
        return self.contents[key]
    except Exception:
        pass
    try:
        return self.collections[key]
    except Exception:
        pass
    raise KeyError


setattr(BaseModel, "__getitem__", basemodel_getitem)
