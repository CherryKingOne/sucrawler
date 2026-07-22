from urllib.parse import quote, urlencode, urljoin, urlparse


def build_url(base_url: str, path: str = "", params: dict[str, str] | None = None) -> str:
    url = urljoin(base_url, path)
    if params:
        separator = "&" if "?" in url else "?"
        url += separator + urlencode(params)
    return url


def encode_params(params: dict[str, str]) -> str:
    return urlencode(params)


def encode_path_component(component: str) -> str:
    return quote(component, safe="")


def is_success(status_code: int) -> bool:
    return 200 <= status_code < 300


def is_redirect(status_code: int) -> bool:
    return 300 <= status_code < 400


def is_client_error(status_code: int) -> bool:
    return 400 <= status_code < 500


def is_server_error(status_code: int) -> bool:
    return 500 <= status_code < 600


def parse_url(url: str) -> dict[str, str]:
    parsed = urlparse(url)
    return {
        "scheme": parsed.scheme,
        "netloc": parsed.netloc,
        "path": parsed.path,
        "params": parsed.params,
        "query": parsed.query,
        "fragment": parsed.fragment,
    }


def join_url(base: str, url: str) -> str:
    return urljoin(base, url)
