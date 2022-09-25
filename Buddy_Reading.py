from get_books import *
from get_greads_links import *


class BuddyReadFormatter:

    Kwargs = dict(
        bread_host="Buddy Read Host",
        avatar_url="https://www.clipartmax.com/png/full/437-4375457_owls-reading-read-with-a-buddy.png",
        title="Not found",
        description="Not found",
        url="",
        author_name="Not Found",
        author_url="",
        author_icon_url="",
        requester="",
        start_date="Not given",
        end_date="Not given",
        genres="Not found",
        num_pages="Not found",
        rating="Not found",
        thumbnail="",
    )

    #embed template
    Template = """{{
  "username": "{bread_host}",
  "avatar_url": "{avatar_url}",
  "content": "<@&895615518902476810> *react with :white_check_mark: if you're interested.*",
  "embeds": [
    {{
      "title": "{title}",
      "color": 0,
      "description": "{description}",
      "timestamp": "",
      "url": "{url}",
      "author": {{
        "name": "{author_name}",
        "url": "{author_url}",
        "icon_url": "{author_icon_url}"
      }},
      "image": {{}},
      "thumbnail": {{
      "url" : "{thumbnail}"
      }},
      "footer": {{
        "text": "Requested by: {requester}"
      }},
      "fields": [
        {{
          "name": "Start Date",
          "value": "{start_date}",
          "inline": True
        }},
        {{
          "name": "End Date",
          "value": "{end_date}",
          "inline": True
        }},
        {{
          "name": "Genres",
          "value": "{genres}"
        }},
        {{
          "name": "Pages :page_facing_up:",
          "value": "{num_pages} pages",
          "inline": True
        }},
        {{
          "name": "Rating :star:",
          "value": "{rating}",
          "inline": True
        }}
      ]
    }}
  ],
  "components": []
}}
"""

    def __call__(self, **kwargs):
        for key in self.Kwargs.keys():
            kwargs[key] = kwargs.get(key, "") or self.Kwargs.get(key, "")
        return self.Template.format(**kwargs)


class BuddyRead(object):
    def __init__(self, buddy_read_req, requester="Anonymous", **kwargs):
        self.buddy_read_req = buddy_read_req
        self.requester = requester
        self.kwargs = kwargs

    def get_value_from_key(self, vars_):
        x, i = -1, 0
        while (x == -1) and (i < len(vars_)):
            x = self.buddy_read_req.lower().find(vars_[i])
            i += 1
        if x > -1:
            eol = self.buddy_read_req[x:].find("\n")
            if eol == -1:
                return self.buddy_read_req[x:].split(":", 1)[-1].strip()
            else:
                return self.buddy_read_req[x:x + eol].split(":", 1)[-1].strip()
        return ""

    def get_author_input(self):
        vars_ = ["author name", "authorname", "author"]
        return self.get_value_from_key(vars_)

    def get_author(self):
        return self.gread_details["author"]

    def get_title_input(self):
        vars_ = ["book name", "bookname", "book title", "booktitle", "title", "book"]
        return self.get_value_from_key(vars_)

    def get_title(self):
        return self.gread_details["book_title"]

    def get_desc(self):
        vars_ = ["synopsis", "description", "details"]
        desc = self.get_value_from_key(vars_)
        if not desc:
            return self.gread_details["description"]
        return desc

    def get_start_date(self):
        vars_ = ["start date", "startdate", "start"]
        return self.get_value_from_key(vars_)

    def get_end_date(self):
        vars_ = ["end date", "ebddate", "end"]
        return self.get_value_from_key(vars_)

    def get_greads_link(self):
        vars_ = ["goodreads url", "goodreadsurl", "goodreadslink", "goodreadslink", "GR url", "GRurl", "goodreads"]
        link = self.get_value_from_key(vars_)
        if not link:
            link = get_greads_links([[self.get_title_input(), self.get_author_input()]])[-1][-1]
        self.get_gread_details(link)
        return link

    def get_gread_details(self, link):
        self.gread_details = scrape_book(link)

    def get_genres(self):
        vars_ = ["genres", "genre", "tags", "shelves"]
        genres = self.get_value_from_key(vars_)
        if not genres:
            num_genres = min(len(self.gread_details["genres"]), 5)
            return ", ".join(self.gread_details["genres"][:num_genres])
        return genres

    def get_num_pages(self):
        return self.gread_details["num_pages"]

    def get_rating(self):
        return self.gread_details["average_rating"]

    def get_requester(self):
        vars_ = ["requester", "requested by", "requestedby", "requested"]
        req = self.get_value_from_key(vars_)
        if not req:
            req = self.requester
        return req

    def get_author_url(self):
        return self.gread_details["author_url"]

    def get_book_thumbnail(self):
        return self.gread_details["book_thumbnail"]

    def get_author_thumbnail(self):
        return self.gread_details["author_thumbnail"]

    @time_took
    def __call__(self):
        self.kwargs.update(
            url=self.get_greads_link(),
            title=self.get_title(),
            description=self.get_desc(),
            author_name=self.get_author(),
            start_date=self.get_start_date(),
            end_date=self.get_end_date(),
            genres=self.get_genres(),
            num_pages=self.get_num_pages(),
            rating=self.get_rating(),
            requester=self.get_requester(),
            author_url=self.get_author_url(),
            author_icon_url=self.get_author_thumbnail(),
            thumbnail=self.get_book_thumbnail(),
        )
        return BuddyReadFormatter()(**self.kwargs)


if __name__ == "__main__":
    br1 = """Book name: A Little History of Economics
Start Date: Dec 12, 2021
End Date: Jan 10,2021"""
    br1 = """Book name: Chaso Kathalu
"""
    br2 = br1 + r"\n Author Name: Niall Kishtainy \n Goodreads url : https://www.goodreads.com/book/show/32622193-a-little-history-of-economics \n Genres: Economics, History, Non-fiction \n Synopsis: What causes poverty? Are economic crises inevitable under capitalism? Is government intervention in an economy a helpful approach or a disastrous idea? The answers to such basic economic questions matter to everyone, yet the unfamiliar jargon and math of economics can seem daunting. This clear, accessible, and even humorous book is ideal for young readers new to economics and for all readers who seek a better understanding of the full sweep of economic history and ideas."
    # print(BuddyRead(br2, "Bippity Boppity")())
    print(BuddyRead(br1, "Bobbity Boppity")())
