from os import getenv
from datetime import date
import logging

from redis import Redis
from pyhive import hive
from pyspark import SparkContext
from pyspark.sql import SparkSession
from pyspark.sql.types import *
from pyspark.sql.functions import udf
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.regression import LinearRegression

LOG_FORMAT = 'app:%s'

REDIS_DELIMITER = ':'
K_STOCKS        = 'stocks'
K_STOCK_NAME    = 'name'
K_STOCK_QUERY   = 'query'

r          = None
connection = None
sc         = None
spark      = None

def make_key(*words):
    return REDIS_DELIMITER.join(words)

def get_name(symbol):
    key = make_key(K_STOCKS, K_STOCK_NAME, symbol)
    if not r.exists(key):
        cursor = connection.cursor()
        cursor.execute('SELECT name FROM symbol_descriptions WHERE symbol="%s"' % symbol)

        name = cursor.fetchone()[0]  # first index of a 1-element tuple

        r.set(key, name)
    else:
        logging.info("Found cache of %s name at %s" % (symbol, key))
        name = r.get(key).decode('utf-8')

    return name

@udf(IntegerType())
def date_string_to_ordinal(date_str):
    date_ = date.fromisoformat(date_str)
    ordinal = date_.toordinal()

    return ordinal

def make_lr_model(symbol):
    query_key = make_key(K_STOCKS, K_STOCK_QUERY, symbol)
    if not r.exists(query_key):
        cursor = connection.cursor()
        cursor.execute('SELECT date_, close FROM stocks WHERE symbol="%s"' % symbol)

        stock_history = cursor.fetchall()

        stock_history_rstore = dict(stock_history)
        r.hmset(query_key, stock_history_rstore)
    else:
        logging.info("Found cache of query at %s" % query_key)
        hscan = r.hscan_iter(query_key)
        def unpack(hscan):
            for date_bstr, float_bstr in hscan:
                yield date_bstr.decode('utf-8'), float(float_bstr)
        stock_history = unpack(hscan)

    logging.info("Transforming data for modeling")
    initial_schema = StructType([
        StructField('date', StringType()),
        StructField('close', FloatType())
    ])
    df = spark.createDataFrame(stock_history, schema=initial_schema)

    df = df.withColumn('date_ordinal', date_string_to_ordinal(df.date))

    va = VectorAssembler(inputCols=['date_ordinal'], outputCol='features')
    df = va.transform(df)

    logging.info("Creating model")
    lr = LinearRegression(featuresCol='features', labelCol='close')
    lr_model = lr.fit(df)

    return lr_model

def predict_close(lr_model, date_ordinal):
    ordinal_schema = StructType([ StructField('date_ordinal', IntegerType()) ])
    df = spark.createDataFrame([[ date_ordinal ]], schema=ordinal_schema)

    va = VectorAssembler(inputCols=['date_ordinal'], outputCol='features')
    df = va.transform(df)

    predictions = lr_model.transform(df)
    close = predictions.head().prediction

    return close

def format_currency(price):
    digits = format(abs(price), ',.2f')
    if price >= 0:
        return '$' + digits
    else:
        return '-$' + digits

def main():
    logging.basicConfig(format=LOG_FORMAT % '%(message)s', level=logging.INFO)

    symbol = getenv('APP_SYMBOL')
    date_ = date.fromisoformat(getenv('APP_DATE'))

    global r, connection, sc, spark
    logging.info("Connecting to Redis")
    r = Redis(host='redis', db=0)
    logging.info("Connecting to Hive")
    connection = hive.Connection(host='hive-server')
    logging.info("Connecting to Spark")
    sc = SparkContext.getOrCreate()
    spark = SparkSession(sc)

    name = get_name(symbol)
    logging.info("Finding stock history of %s (%s)" % (name, symbol))

    lr_model = make_lr_model(symbol)
    lr_summary = lr_model.summary
    logging.info("Successfully built linear regression model\n",
          "\t" + "Coefficient:\t%f" % lr_model.coefficients[0] + "\n",
          "\t" + "Intercept:  \t%f" % lr_model.intercept + "\n",
          "\t" + "RMSE:       \t%f" % lr_summary.rootMeanSquaredError + "\n",
          "\t" + "r2:         \t%f" % lr_summary.r2)

    date_f = date_.strftime('%b %d %Y')
    logging.info("Inputting %s into generated model" % date_f)
    close = predict_close(lr_model, date_.toordinal())
    close_f = format_currency(close)
    logging.info("Estimated price of %s at %s:\t%s"
          % (symbol, date_f, close_f))

if __name__ == "__main__":
    main()
