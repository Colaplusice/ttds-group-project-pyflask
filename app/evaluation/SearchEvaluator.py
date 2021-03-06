from app.api.Search import SearchEngine
from app.evaluation.EvalResult import EvalResult
import math

class SearchEvaluator():
    
    def __init__(self, index, use_stemming=True, use_stopping=True):
        self.search = SearchEngine(index, use_stemming=use_stemming, use_stopping=use_stopping)

    def evaluate_query(self, query, ideal_results):
        actual_results = self.search.match(query)       

        eval_result = EvalResult()
        if len(actual_results) == 0 or len(ideal_results) == 0:
            return eval_result
        
        eval_result.Precision = self.calculate_precision(actual_results, ideal_results)
        eval_result.Recall = self.calculate_recall(actual_results, ideal_results)
        eval_result.RPrecision = self.calculate_rprecision(actual_results, ideal_results)
        eval_result.AveragePrecision = self.calculate_avgprecision(actual_results, ideal_results)

        actual_tuples = [(tweet, 1) for tweet in actual_results]
        ideal_tuples = [(tweet, 1) for tweet in ideal_results]
        eval_result.nDCGat10 = self.calculate_normalized_discounted_cumulative_gain(actual_tuples, ideal_tuples, 10)
        eval_result.nDCGat20 = self.calculate_normalized_discounted_cumulative_gain(actual_tuples, ideal_tuples, 20)
        eval_result.nDCGat30 = self.calculate_normalized_discounted_cumulative_gain(actual_tuples, ideal_tuples, 30)
        return eval_result

    def calculate_precision(self, results, ideal):
        true_pos = self.get_intersection([results, ideal])
        return len(true_pos) / len(results)

    def calculate_recall(self, results, ideal):
        true_pos = self.get_intersection([results, ideal])
        return len(true_pos) / len(ideal)

    def calculate_rprecision(self, results, ideal):
        return self.calculate_precision(ideal, results[0:len(ideal)])

    def calculate_avgprecision(self, results, ideal):
        precision_sum = 0.0
        tweet_count = 0
        for idx, tweet in enumerate(results):
            if tweet in ideal:
                tweet_count += 1
                precision_sum += (tweet_count / (idx+1.0))
        return precision_sum / len(ideal)

    def calculate_discounted_cumulative_gain(self, relevance_ranks):
        dcg_index = []
        dcg_sum = 0.0

        if (len(relevance_ranks)) == 1:
            return [relevance_ranks[0]]
        
        for i, relevance in enumerate(relevance_ranks):
            idx = i
            if (idx == 0):
                dcg_sum += 1
                dcg_index.append(dcg_sum)
                continue

            if (relevance != 0):
                dcg_sum += relevance / math.log2(idx+1)
            
            dcg_index.append(dcg_sum)
        
        return dcg_index

    def calculate_normalized_discounted_cumulative_gain(self, results, ideal, count):
        relevance_ranks = [1 if result in ideal else 0 for result in results]
        ideal_ranks = [1] * len(ideal)

        dcg_idx = self.calculate_discounted_cumulative_gain(relevance_ranks)
        idcg_idx = self.calculate_discounted_cumulative_gain(ideal_ranks)

        dcg = (dcg_idx[count-1] if count < len(dcg_idx) else dcg_idx[-1])
        idcg = (idcg_idx[count-1] if count < len(idcg_idx) else idcg_idx[-1])

        ''' ndcg = dcg/idcg '''
        if idcg == 0:
            return 0.0

        return dcg / idcg

    def get_intersection(self, lists):
        if lists is None or len(lists) == 0:
            return []
        if len(lists) == 1:
            return list(set(lists[0]))

        list_as_set = set(lists[0])
        intersect = list(list_as_set.intersection(*lists))
        intersect.sort()
        return intersect