from typing import *

class MException(Exception):
    def get_message(self) -> str:
        return self.__class__.__name__

class APIError(Exception):
    def __init__(self, status_code: int, raw_data: Any) -> None:
        self.status_code = status_code
        self.raw_data = raw_data
        super().__init__(f"{status_code=} {raw_data=}")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self!s})"
    
    def get_message(self) -> str:
        return "Something went wrong whilst trying to" +\
                " contact the stream service's API.\n" +\
                "Raw response data:\n%r" + str(self)

class InvalidYoutubeCredentials(APIError):
    def __repr__(self) -> str:
        return f"InvalidYoutubeCredentials"
    def get_message(self) -> str:
        return "The YouTube API key is either invalid or has not been set."

class YoutubeQuotaExceeded(APIError):
    def __repr__(self) -> str:
        return f"YoutubeQuotaExceeded"
    def get_message(self) -> str:
        return "YouTube quota has been exceeded."

class NotInitYet(Exception):
    def __repr__(self) -> str:
        return f"NotInitYet"
    def get_message(self) -> str:
        return "Your class need to initial."
