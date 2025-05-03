class ComponentError(Exception):
    """Base class for all component-related exceptions"""

    def __init__(self, message="Component error occurred"):
        self.message = message
        super().__init__(self.message)


class InvalidInputError(ComponentError):
    """Raised when user input is invalid"""

    def __init__(self, message="Invalid input provided"):
        self.message = message
        super().__init__(self.message)


class DuplicateComponentError(ComponentError):
    """Raised when a component with the same part number already exists"""

    def __init__(self, message="Component already exists"):
        self.message = message
        super().__init__(self.message)


class InvalidQuantityError(ComponentError):
    """Raised when an invalid quantity is provided"""

    def __init__(self, message="Invalid quantity specified"):
        self.message = message
        super().__init__(self.message)


class ComponentNotFoundError(ComponentError):
    """Raised when a requested component cannot be found"""

    def __init__(self, message="Component not found"):
        self.message = message
        super().__init__(self.message)


class StockError(ComponentError):
    """Raised when there's insufficient stock for an operation"""

    def __init__(self, message="Insufficient stock available"):
        self.message = message
        super().__init__(self.message)


class DatabaseError(ComponentError):
    """Raised for database-related errors"""

    def __init__(self, message="Database operation failed"):
        self.message = message
        super().__init__(self.message)
