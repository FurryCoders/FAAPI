class DisallowedPath(BaseException):
    """
    The path is not allowed by the robots.txt.
    """


class ParsingError(BaseException):
    """
    An error occurred while parsing the page.
    """


class Unauthorized(BaseException):
    """
    The user is not logged-in.
    """


class NonePage(ParsingError):
    """
    The parsed page is None.
    """


class NoTitle(ParsingError):
    """
    The parsed paged is missing a title.
    """


class DisabledAccount(ParsingError):
    """
    The resource belongs to a disabled account.
    """


class ServerError(ParsingError):
    """
    The page contains a server error notice.
    """


class NoticeMessage(ParsingError):
    """
    A notice of unknown type was found in the page.
    """
