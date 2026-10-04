from .web_search import web_search
from .fetch_url import fetch_url
from .read_file import read_file
from .write_file import write_file

TOOLS = {
    "web_search": web_search,
    "fetch_url": fetch_url,
    "read_file": read_file,
    "write_file": write_file,
}

DANGEROUS = {"write_file"}