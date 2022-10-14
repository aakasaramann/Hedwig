from urllib.request import urlopen
import bs4
import Levenshtein as lev
from functools import wraps
import time


def time_took(f):
    """
    wrapper to print the time took
    :param f:
    :return:
    """
    @wraps(f)
    def func(*args, **kwargs):
        st = time.time()
        res = f(*args, **kwargs)
        print("time took to run {} is {}".format(f.__name__, (time.time() - st)))
        return res

    return func


def match_score(entry, title, author):
    """
    :param entry: book schema object
    :return: give a score by checking if the title and author matches properly
    :param title:
    :param author:
    """
    # typical s_ looks like ['The Scorch Trials (The Maze Runner, #2)', 'by', 'James Dashner (Goodreads Author)', '3.90 avg rating — 507,459 ratings', '—', 'published', '2010', '—', '142 editions', 'Want to Read', 'saving…', 'Want to Read', 'Currently Reading', 'Read', 'Error rating book. Refresh and try again.', 'Rate this book', 'Clear rating', '1 of 5 stars2 of 5 stars3 of 5 stars4 of 5 stars5 of 5 stars', 'Get a copy']
    s_ = [x.strip("\n ") for x in entry.text.strip("\n ").split("\n") if x.strip("\n ")]
    # s_[0] is title , s_[2] is author
    if len(s_) < 3:
        s_.extend([""] * (3 - len(s_)))
    return 0.75 * lev.ratio(title.lower(), s_[0].lower()) + 0.25 * lev.ratio(author.lower(), s_[2].lower())


@time_took
def get_greads_links(books, top_result=True):
    """
    :param books: list of lists Ex: [["The trial", "Franz Kafka"], ["The white tiger", "Aravind Adiga"]]
    :return:
    """
    for book in books:
        source = urlopen("https://www.goodreads.com/search?q={}".format("+".join(book[0].split())))
        soup = bs4.BeautifulSoup(source, 'html.parser')
        tables_ = soup.findAll("table", {"class": "tableList"})
        if len(tables_) != 1:
            raise AssertionError
        if top_result:
            match, i = None, 0
            while (match is None) and i < len(tables_[0].contents):
                entry = tables_[0].contents[i]
                if "schema.org/Book" in ((hasattr(entry, "attrs") and entry.attrs.get("itemtype", "")) or ""):
                    match = entry
                i += 1
        else:
            scores = []
            contents = []
            for entry in tables_[0].contents:
                if "schema.org/Book" in ((hasattr(entry, "attrs") and entry.attrs.get("itemtype", "")) or ""):
                    scores.append(match_score(entry, book[0], book[1]))
                    contents.append(entry)
            match = contents[scores.index(max(scores))]
        title_link_ = []
        for x in match.contents:
            if hasattr(x, "findAll"):
                title_link_.extend(x.findAll("a", {"class": "bookTitle"}))
        book.append("https://www.goodreads.com" + (title_link_[0].attrs["href"].split("?")[0]))
    return books


if __name__ == "__main__":
    get_greads_links([["The trial", "Franz Kafka"]])
