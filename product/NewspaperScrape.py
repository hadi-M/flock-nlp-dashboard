from newspaper import Article
import newspaper
from newspaper import news_pool
from newspaper import Config

import pandas as pd
import spacy
from collections import Counter

from pdb import set_trace as st

import os

output_dir = "output_newspaper"
csv_links = "./links/links.csv"
default_user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36"
nlp = spacy.load("en_core_web_sm")


class ProgressCounter():
    def __init__(self):
        self.counter = 0

    def inc(self):
        self.counter += 1


progress_bar_value = ProgressCounter()


class NewspaperScrape():
    def __init__(self, output_dir, dataframe, num_rows=None, user_agent=default_user_agent) -> None:
        self.output_dir = output_dir

        temp_df = dataframe
        if num_rows:
            self.df = temp_df.iloc[:num_rows]
        else:
            self.df = temp_df

        self.user_agent = user_agent
        self.config = Config()
        self.config.browser_user_agent = user_agent

        self.download_logs_dict = {
            "link": [],
            "download_state": [],
            "download_exception_msg": []
        }

        self.number_of_downloaded = 0

        self.preprocess_df()

    def preprocess_df(self) -> pd.DataFrame:
        """
        Preprocessing the Dataframe includes, dropping the null links,
        removing space from around the links and keeping the links
        than only start with http or https
        """

        self.df = self.df.dropna()
        self.df.iloc[:, 0] = self.df.iloc[:, 0].str.strip()
        self.df = self.df[self.df.iloc[:, 0].str.startswith("http")]

    def download_single_url(self, url, args):

        article = Article(url, config=self.config)
        article.download()

        self.download_logs_dict["link"].append(url)
        self.download_logs_dict["download_state"].append(article.download_state)
        self.download_logs_dict["download_exception_msg"].append(article.download_exception_msg)

        try:
            article.parse()
        except Exception as e:
            pass
        print(f"Done with {url}")
        # article.nlp()
        # print(article.keywords)
        # st()
        if args:
            args.inc()

        return article.text

    def download_all(self, progress_bar_value):
        """
        This will download all of the articles
        and put them in a new column called
        "article_content"
        """

        self.df["text"] = self.df["Relevant Article"].apply(self.download_single_url, args=(progress_bar_value,))

    def get_text_lemmas(self, text):
        lemmas = []
        doc = nlp(text)
        for token in doc:
            if (
                (token.is_stop is False) and
                (token.is_punct is False)
            ) and (token.pos_ != 'PRON') and (not token.is_space):
                lemmas.append(token.lemma_)

        return lemmas

    def get_all_lemmas(self):
        self.df["lemmas"] = self.df["text"].apply(self.get_text_lemmas)

    def analyze(self):

        word_counts = Counter()
        appears_in = Counter()

        total_docs = len(self.df["lemmas"])

        for doc in self.df["lemmas"]:
            word_counts.update(doc)
            appears_in.update(set(doc))

        temp = zip(word_counts.keys(), word_counts.values())

        wc = pd.DataFrame(temp, columns = ['word', 'count'])

        wc['rank'] = wc['count'].rank(method='first', ascending=False)
        total = wc['count'].sum()

        wc['pct_total'] = wc['count'].apply(lambda x: x / total)

        wc = wc.sort_values(by='rank')
        wc['cul_pct_total'] = wc['pct_total'].cumsum()

        t2 = zip(appears_in.keys(), appears_in.values())
        ac = pd.DataFrame(t2, columns=['word', 'appears_in'])
        wc = ac.merge(wc, on='word')

        wc['appears_in_pct'] = wc['appears_in'].apply(lambda x: x / total_docs)

        self.analyzed_df = wc.sort_values(by='rank')


if __name__ == "__main__":
    df = pd.read_csv("links/links.csv")
    news_scraper = NewspaperScrape(
        output_dir=None,
        dataframe=df,
        num_rows=8
    )
    news_scraper.download_all(progress_bar_value)
    news_scraper.get_all_lemmas()
    news_scraper.analyze()
    print(progress_bar_value.counter)

# df = df.iloc[:50]

# config = Config()
# config.browser_user_agent = user_agent

# def link_to_article(url):
#     # url = row["Relevant Article"]
#     article = Article(url, config=config)
#     article.download()
#     # st()
#     download_logs["link"].append(url)
#     download_logs["download_state"].append(article.download_state)
#     download_logs["download_exception_msg"].append(article.download_exception_msg)
#     try:
#         article.parse()
#     except Exception as e:
#         # st()
#         pass
#     print(f"Done with {url}")
#     # article.nlp()
#     # print(article.keywords)
#     return article.text



# df.to_csv("output_all.csv")
# pd.DataFrame(download_logs).to_csv("download_logs.csv")

# papers = [newspaper.build(url) for url in start_urls]
# news_pool.set(papers, threads_per_source=2) # (3*2) = 6 threads total
# news_pool.join()

# for index, parsed_article in enumerate(papers):
#     url = start_urls[index]
#     filename = url.replace("/", "_") + ".txt"
#     path = os.path.join(output_dir, filename)
#     st()
#     with open(path, "w") as f:
#         f.write(parsed_article.text)
#     print(f"Done with {index}: {url}")