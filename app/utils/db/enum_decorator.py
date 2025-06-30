from sqlalchemy import String, TypeDecorator


class EnumType(TypeDecorator):
    impl = String
    cache_ok = True

    def __init__(self, enum_class, *arg, **kw):
        self.enum_class = enum_class
        super(EnumType, self).__init__(*arg, **kw)

    def process_bind_param(self, value, dialect):
        if value is not None:
            if isinstance(value, self.enum_class):
                return value.value
            return value
        return None

    def process_result_value(self, value, dialect):
        if value is not None:
            try:
                return self.enum_class(value)
            except ValueError:
                return None
        return None

    def copy(self, **kw):
        return EnumType(self.enum_class, **kw)
