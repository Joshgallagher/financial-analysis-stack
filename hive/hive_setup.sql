DROP TABLE IF EXISTS stocks;
DROP TABLE IF EXISTS symbol_descriptions;

CREATE EXTERNAL TABLE stocks (
  symbol VARCHAR(5),
  date_ DATE,
  volume INT,
  open FLOAT,
  close FLOAT,
  high FLOAT,
  low FLOAT,
  adjclose FLOAT
)
    ROW FORMAT DELIMITED
    FIELDS TERMINATED BY ','
    STORED AS TEXTFILE;

LOAD DATA LOCAL INPATH '/data/stock_histories.csv.gz'
    OVERWRITE INTO TABLE stocks;

CREATE TABLE symbol_descriptions (
  symbol VARCHAR(5),
  name STRING
)
    ROW FORMAT DELIMITED
    FIELDS TERMINATED BY '\t'
    STORED AS TEXTFILE
    TBLPROPERTIES ("skip.header.line.count"="1");

LOAD DATA LOCAL INPATH '/data/symbol_descriptions.txt'
    OVERWRITE INTO TABLE symbol_descriptions;
