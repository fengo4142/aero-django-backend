"""
Exception Classes
"""


class FormatError(Exception):
    """ Raised when the basic schema is invalid. """

    def __init__(self, message):
        """
        If 'message' is a string, we simply create the instance.
        If 'message' is a list, we split it to individual messages
        """
        if isinstance(message, list):
            self.error_list = []
            for message in message:
                if not isinstance(message, FormatError):
                    message = FormatError(message)
                self.error_list.extend(message.error_list)
        else:
            self.message = message
            self.error_list = [self]

    def __iter__(self):
        for error in self.error_list:
            message = error.message
            yield message

    def __str__(self):
        return repr(list(self))

    def __repr__(self):
        return "{0}".format(self.message)


class FieldError(Exception):
    """ Raised when a field is invalid. """

    def __init__(self, message):
        """
        If 'message' is a string, we simply create the instance.
        If 'message' is a list, we split it to individual messages
        """
        if isinstance(message, list):
            self.error_list = []
            for message in message:
                if not isinstance(message, FieldError):
                    message = FieldError(message)
                self.error_list.extend(message.error_list)
        else:
            self.message = message
            self.error_list = [self]

    def __iter__(self):
        for error in self.error_list:
            message = error.message
            yield message

    def __str__(self):
        return repr(list(self))

    def __repr__(self):
        return "{0}".format(self.message)


class ConditionError(Exception):
    """ Raised when a condition is invalid. """

    def __init__(self, message):
        """
        If 'message' is a string, we simply create the instance.
        If 'message' is a list, we split it to individual messages
        """
        if isinstance(message, list):
            self.error_list = []
            for message in message:
                if not isinstance(message, ConditionError):
                    message = ConditionError(message)
                self.error_list.extend(message.error_list)
        else:
            self.message = message
            self.error_list = [self]

    def __iter__(self):
        for error in self.error_list:
            message = error.message
            yield message

    def __str__(self):
        return repr(list(self))

    def __repr__(self):
        return "{0}".format(self.message)


class ValidationError(Exception):
    """ Raised when a validator is invalid. """

    def __init__(self, message):
        """
        If 'message' is a string, we simply create the instance.
        If 'message' is a list, we split it to individual messages
        """
        if isinstance(message, list):
            self.error_list = []
            for message in message:
                if not isinstance(message, ValidationError):
                    message = ValidationError(message)
                self.error_list.extend(message.error_list)
        else:
            self.message = message
            self.error_list = [self]

    def __iter__(self):
        for error in self.error_list:
            message = error.message
            yield message

    def __str__(self):
        return repr(list(self))

    def __repr__(self):
        return "{0}".format(self.message)
