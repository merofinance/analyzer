import numpy as np
import pandas as pd
import gzip
import json
import math
from datetime import datetime, timezone
from collections import Counter
from itertools import groupby
from importlib import reload
from pandas.io.json import json_normalize
import multiprocessing
import glob
import pickle
import requests
import time

ctokens = requests.get('https://api.compound.finance/api/v2/ctoken').json()

ctokens_db = pd.json_normalize(ctokens['cToken'])