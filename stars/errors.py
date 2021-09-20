from typing import Any


class StreamsError(Exception):
    pass


class StreamNotFound(StreamsError):
    pass


class APIError(StreamsError):
    def __init__(self, status_code: int, raw_data: Any) -> None:
        self.status_code = status_code
        self.raw_data = raw_data
        super().__init__(f"{status_code=} {raw_data=}")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self!s})"



class InvalidYoutubeCredentials(StreamsError):
    pass


class YoutubeQuotaExceeded(StreamsError):
    pass


class OfflineStream(StreamsError):
    pass

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

class PassDate(TempMembershipRole):
    pass

class ModRefused(TempMembershipRole):
    pass

class ReactionTimeout(TempMembershipRole):
    pass

class ServerError(TempMembershipRole):
    pass

class StarsServer(Exception):
    pass

class NotFound(StarsServer):
    pass
