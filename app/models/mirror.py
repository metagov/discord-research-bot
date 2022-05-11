from abc import abstractclassmethod


class Mirror:
    """Most of what we will be storing are "reflections" of resources owned by
    Discord. This class is an abstract document that will be extended by
    other classes that will be used to update their respective data.
    """

    # TODO: Investigate weird behavior when inheriting from ``ABC``.
    @abstractclassmethod
    def record(cls, object, **kwargs) -> 'Mirror':
        raise NotImplementedError
