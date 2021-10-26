from typing import Any

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

