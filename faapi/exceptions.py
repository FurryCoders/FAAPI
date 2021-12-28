class DisallowedPath(Exception):
    """
    The path is not allowed by the robots.txt.
    """
    pass


class ParsingError(Exception):
    """
    An error occurred while parsing the page.
    """
    pass


class Unauthorized(Exception):
    """
    The user is not logged-in.
    """
    pass


class NonePage(ParsingError):
    """
    The parsed page is None.
    """
    pass


class NoTitle(ParsingError):
    """
    The parsed paged is missing a title.
    """
    pass


class DisabledAccount(ParsingError):
    """
    The resource belongs to a disabled account.
    """
    pass


class ServerError(ParsingError):
    """
    The page contains a server error notice.
    """
    pass


class NoticeMessage(ParsingError):
    """
    A notice of unknown type was found in the page.
    """
    pass
