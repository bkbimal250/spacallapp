class BaseRepository:
    model = None

    @classmethod
    def get_by_id(cls, id):
        return cls.model.objects.filter(id=id).first()

    @classmethod
    def filter(cls, **kwargs):
        return cls.model.objects.filter(**kwargs)

    @classmethod
    def all(cls):
        return cls.model.objects.all()
