class DisallowedPath(Exception):
    pass


class CrawlDelayError(Exception):
    pass


class ParsingError(Exception):
    pass


class NonePage(ParsingError):
    pass


class NoTitle(ParsingError):
    pass


class DisabledAccount(ParsingError):
    pass


class ServerError(ParsingError):
    pass


class NoticeMessage(ParsingError):
    pass
