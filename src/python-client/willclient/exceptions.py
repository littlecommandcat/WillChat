class WillClientException(Exception):
    pass

class UnexpectedBody(WillClientException):
    pass

class UnexpectedStatus(WillClientException):
    pass

class FailedConnection(WillClientException):
    pass

class UnknownGroup(WillClientException):
    pass

class UnknownMessage(WillClientException):
    pass

class UnknownMember(WillClientException):
    pass