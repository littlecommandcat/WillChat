import aiohttp

class _CacheBase:
    def __init__(self):
        self.token: str = ""
        self.data: dict = {}
        self.session: aiohttp.ClientSession | None=None

    def has_token(self) -> bool:
        return bool(self.token)

    def has_data(self) -> bool:
        return bool(self.data)

    def has_session(self) -> bool:
        return True if self.session and isinstance(self.session, aiohttp.ClientSession) and not self.session.closed else False

    def init_session(self) -> None:
        if not self.session or (isinstance(self.session, aiohttp.ClientSession) and self.session.closed):
            self.session = aiohttp.ClientSession()
            
        
_cache_base = _CacheBase()