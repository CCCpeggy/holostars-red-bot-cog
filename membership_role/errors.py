
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

class ValidFailure(TempMembershipRole):
    pass

class PassDate(TempMembershipRole):
    pass

class ModRefused(TempMembershipRole):
    pass

class ReactionTimeout(TempMembershipRole):
    pass

class ServerError(TempMembershipRole):
    pass

