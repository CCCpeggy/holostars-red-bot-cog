from typing import Any

class AlreadyExisted(Exception):
    pass

class AlreadyExisted(Exception):
    pass

class AuditException(Exception):
    pass

class NoSPWNID(AuditException):
    pass

class NoDiscordID(AuditException):
    pass

class WrongSPWNID(AuditException):
    pass

class RepeatSPWNID(AuditException):
    pass

class ModRefused(AuditException):
    pass

class ReactionTimeout(AuditException):
    pass

class ServerError(AuditException):
    pass

