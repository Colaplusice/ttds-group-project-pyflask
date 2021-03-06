import re, math
from enum import Enum
from app.api.processor import PreProcessor

class QueryType(Enum):
    BOOL = 1
    TERM = 2

class SearchEngine:
    _index_collection = None
    _index = {}
    _preprocessor = None
    _default_max_results = 20

    _re_bool = re.compile("(.*?)\\b(AND NOT|AND|OR)\\b(.*)")

    def __init__(self, index, use_stopping=True, use_stemming=True):
        """ Set inverted index. """
        self._preprocessor = PreProcessor(apply_stemming=use_stemming, apply_stopping=use_stopping)
        self._index_collection = index
        self._index = self._index_collection.index
        return

    def match(self, query, limit=None):
        results = []
        if not query:
            return results
        if limit is None or not isinstance(limit, int) or limit <= 0:
            limit = self._default_max_results

        query_type, parts = self.parse_query(query)
        if query_type == QueryType.BOOL:
            results = self.match_strict(query, limit)
        else:
            results = self.match_ranked(query, limit)
        return results

    def match_ranked(self, query, limit=None):
        """ Execute a search and returns a list of tweets ranked by TFIDF score"""
        tokens = set(self._preprocessor.preprocess(query))

        tweet_lists = [self._index[token] for token in tokens if token in self._index]
        tweet_superset = self.get_union(tweet_lists)
        results = []
        for tweet in tweet_superset:
            qd = 0.0
            last_seen = 0.0
            for token in tokens:
                if not tweet in self._index[token]:
                    continue

                df = len(self._index[token])
                tf = min(1, self._index[token][tweet][1]) + (self._index[token][tweet][2] * 0.75)
                idf = math.log10(self._index_collection._tweet_count / df)
                wtd = (1 + math.log10(tf)) * idf
                qd += wtd
                last_seen = max(last_seen, self._index[token][tweet][0])

            results.append([tweet, qd, last_seen])
        
        # Sort by TF-IDF, then by date seen, both in reverse
        results.sort(key=lambda x: (x[1], x[2]), reverse=True)

        # Return list of tweet IDs, not score
        return [result[0] for result in results[:limit]]

    def match_strict(self, query, limit = None):
        """Execute a boolean search and returns a list of matched tweet IDs."""
        tweets = []
        query_type, parts = self.parse_query(query)
        if query_type == QueryType.BOOL:
            # If bool, recursively get results for left & right part
            left_set = self.match(parts[0])
            right_set = self.match(parts[2])

            # Perform boolean match
            op = parts[1]
            if op == "AND":
                tweets = self.get_intersection([left_set, right_set])
            elif op == "OR":
                tweets = self.get_union([left_set, right_set])
            elif op == "AND NOT":
                tweets = self.get_difference([left_set, right_set])
        else:
            """Matches tweets that contain all terms of a query."""
            tokens = self._preprocessor.preprocess(query)
            tweet_lists = []
            for token in tokens:
                if token in self._index:
                    tweet_lists.append(self._index[token])
            tweets = self.get_intersection(tweet_lists)

        tweets.sort()
        return tweets

    def parse_query(self, query):
        """Identifies a query's type and its constituent parts."""
        match = self._re_bool.match(query)
        if not match is None:
            return QueryType.BOOL, match.group(1, 2, 3)
        return QueryType.TERM, query

    def get_union(self, lists):
        if lists is None or len(lists) == 0:
            return []
        if len(lists) == 1:
            return list(set(lists[0]))

        union = list(set({}).union(*lists))
        union.sort()
        return union

    def get_intersection(self, lists):
        if lists is None or len(lists) == 0:
            return []
        if len(lists) == 1:
            return list(set(lists[0]))

        list_as_set = set(lists[0])
        intersect = list(list_as_set.intersection(*lists))
        intersect.sort()
        return intersect

    def get_difference(self, lists):
        if lists is None or len(lists) == 0:
            return []
        if len(lists) == 1:
            return list(set(lists[0]))

        difference = list(set(lists[0]).difference(lists[1]))
        difference.sort()
        return difference
