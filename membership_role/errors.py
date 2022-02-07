
class TempMembershipRole(Exception):
    pass

class WrongDateFormat(TempMembershipRole):
    pass

class WrongChannelName(TempMembershipRole):
    pass

class NoDate(TempMembershipRole):
    pass

class NoChannelName(TempMembershipRole):
    pass

class FutureDate(TempMembershipRole):
    pass

class CommentFailure(TempMembershipRole):
    pass

class PassDate(TempMembershipRole):
    pass

class ModRefused(TempMembershipRole):
    pass

class ReactionTimeout(TempMembershipRole):
    pass

class ServerError(TempMembershipRole):
    pass

class APIError(TempMembershipRole):
    def __init__(self, status_code: int, raw_data) -> None:
        self.status_code = status_code
        self.raw_data = raw_data
        super().__init__(f"{status_code=} {raw_data=}")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self!s})"

