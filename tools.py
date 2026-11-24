"""Each event has four fields and an optional free-text note."""
from collections import Counter

from security import Rejected, read_sample


def events(file):
    for line in read_sample(file).splitlines():
        fields = line.split(maxsplit=4)
        if len(fields) < 4 or fields[1] not in ("FAIL", "SUCCESS"):
            raise Rejected("Invalid event format.")
        yield fields


def count_failures(file):
    counts = Counter((row[2], row[3]) for row in events(file) if row[1] == "FAIL")
    return [{"account": account, "source": source, "count": count}
            for (account, source), count in counts.most_common()]


def search_entries(file, query):
    return [line for line in read_sample(file).splitlines()
            if query.casefold() in line.casefold()]


def log_stats(file):
    rows = list(events(file))
    failures = sum(row[1] == "FAIL" for row in rows)
    return {"events": len(rows), "failures": failures, "successes": len(rows) - failures,
            "accounts": len({row[2] for row in rows}), "sources": len({row[3] for row in rows})}


def read_file(file):
    return read_sample(file)


REGISTRY = {
    "read_file": (read_file, {"file"}),
    "count_failures": (count_failures, {"file"}),
    "search_entries": (search_entries, {"file", "query"}),
    "log_stats": (log_stats, {"file"}),
}


def execute(name, args):
    if not isinstance(name, str) or name not in REGISTRY:
        raise Rejected("Unknown tool.")
    function, keys = REGISTRY[name]
    if not isinstance(args, dict) or args.keys() != keys:
        raise Rejected("Incorrect argument names.")
    if any(not isinstance(v, str) or not v.strip() or len(v) > 100 for v in args.values()):
        raise Rejected("Arguments must be nonempty strings of at most 100 characters.")
    return function(**args)
