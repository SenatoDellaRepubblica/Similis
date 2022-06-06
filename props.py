import os

app_name = 'Similis-Service'
app_version = '1.0'

# PATH pattern
current_in_path_prefix = os.environ['BGTPATH_IN']
current_in_path = r"/{0}/BGT/Testi"

# current output path
current_out_path = None

# Livello di logging
logging_level = 'DEBUG'

#################################################
#
#           CONFIG EXPERIMENT
#
#################################################

# SET METHOD Jaccard / Cosine

COSINE = 'cosine'
JACCARD = 'jaccard'
TF_IDF = 'tf-idf'
TF = 'tf'

THRESHOLD_JACC = 0.35  # 0.4
THRESHOLD_COSINE_TF_IDF = 0.35
THRESHOLD_COSINE_TF = 0.2

# MAX_DF_COSINE = 0.95
MAX_DF_COSINE = 1.00


class DistanceConfig:

    def __init__(self, method=None, threshold=None):
        self.method = method
        self.threshold = threshold

        if threshold is None:
            if self.method == TF_IDF:
                self.threshold = THRESHOLD_COSINE_TF_IDF
            elif self.method == TF:
                self.threshold = THRESHOLD_COSINE_TF
            elif self.method == JACCARD:
                self.threshold = THRESHOLD_JACC


curr_dist_cfg = DistanceConfig(None)

processCorpus = 'FULL'
# processCorpus = 'VIR'
# processCorpus = 'NOVIR'


#################################################
