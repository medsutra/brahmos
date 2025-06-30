from sqlalchemy import String, TypeDecorator


class EnumType(TypeDecorator):
    impl = String 
    cache_ok = True

    def __init__(self, enum_class, *arg, **kw):
        self.enum_class = enum_class
        super(EnumType, self).__init__(*arg, **kw)

    def process_bind_param(self, value, dialect):
        # Convert Python Enum member to its value (e.g., "pending") for storage
        if value is not None:
            if isinstance(value, self.enum_class):
                return value.value
            return value # If already a string, pass as is
        return None

    def process_result_value(self, value, dialect):
        # Convert stored value (e.g., "pending") back to Python Enum member
        if value is not None:
            try:
                return self.enum_class(value)
            except ValueError:
                # Handle cases where the stored value might not be a valid enum member
                return None # Or raise an error, depending on desired behavior
        return None

    def copy(self, **kw):
        return EnumType(self.enum_class, **kw)
