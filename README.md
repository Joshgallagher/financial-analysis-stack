# Financial Analysis Stack
This project aims to demonstrate how various distributed data and parallel processing services could be used for financial analysis.

An example application is provided, which uses the daily close prices of a stock to generate a linear regression model. This model is then used to predict the price of a stock at a given future date.

TODO example images of cli and web app in action `![]()`

## Setup
### Install Docker & Docker Compose
*Docker* is used to easily deploy containers ([learn more](https://docs.docker.com/get-started/#docker-concepts)). Cross-platform installation instructions are available at [docs.docker.com/get-docker](https://docs.docker.com/get-docker/).

*Docker Compose* is used to define and run multiple containers together, managing our stack of services and applications. You will likely have it already installed if you installed *Docker* on Windows or Mac (check with `docker-compose --version`). Installation instructions are available at [docs.docker.com/compose/install](https://docs.docker.com/compose/install/). 

We recommend Linux users add themselves to the `docker` group so as to avoid entering `sudo` for every desired command. Instructions are available at [docs.docker.com/engine/install/linux-postinstall](https://docs.docker.com/engine/install/linux-postinstall/#manage-docker-as-a-non-root-user).

### Install Python 3
*Python* is a programming language we use to build part of our stack. Cross-platform installation instructions are available at [realpython.com/installing-python/](https://realpython.com/installing-python/).

Note we use version 3 of Python. Make sure you have Python 3 by checking the version of your installation like so:
```bash
$ python --version
Python 3.X.X
```

### Clone repository using Git
*Git* is used for version control ([learn more](https://www.atlassian.com/git/tutorials/what-is-version-control)). Cross-platform installation instructions are available at [git-scm.com/downloads](https://git-scm.com/downloads).

To clone this repository in a bash shell (e.g. Git Bash), use the following command:
```bash
git clone github.com/Joshgallagher/financial-analysis-stack.git && cd financial-analysis-stack
```

See instructions for cloning repositories at [help.github.com](https://help.github.com/en/github/creating-cloning-and-archiving-repositories/cloning-a-repository).

### Start services
Simply run the following command to get the stack up and running:
```bash
docker-compose up
```

This will tail all the services logs in your shell. If you want to avoid this,  add the option `-d`. To ensure the stack is running when using the `-d` option, use `docker-compose ps` where you should see all services as status as `Up` (except for the `app`, which runs periodically as jobs).

The images for each service will automatically download on the first run.

## Use instructions
We provide an `app` service that creates a linear regression model for a stock's full history, and estimates a price for the stock at a user-provided date. The mechanisms for this container is provided in the `app/` folder.

### Command-Line Application
To run an app job, i.e. estimate a price at a given date, you can the `estimate_stock_price.py` script we provided, located in the repositories root folder.
```bash
usage: estimate_stock_price.py [-h] symbol date

positional arguments:
  symbol      Stock listing to model for
  date        Predict stock's price at <yyyy-mm-dd>

optional arguments:
  -h, --help  show this help message and exit
```

For example, if you wanted to find an estimation for the value of `GOOGL` (Google) on April 4th, 2020, you can run the following in your shell environment:
```bash
./estimate_stock_price.py GOOGL 2021-04-10
```

The output should looking something like this:
```
Running docker-compose up -d --no-deps app
Recreating spark_app_1 ... done
Running docker-compose logs -f --no-color app
Connecting to Redis
Connecting to Hive
Connecting to Spark
SELECT name FROM symbol_descriptions WHERE symbol="GOOGL"
Finding stock history of Alphabet Cl A (GOOGL)
SELECT date_, close FROM stocks WHERE symbol="GOOGL"
Transforming data for modeling
Creating model
Inputting Apr 10 2021 into generated model
Estimated price of GOOGL at Apr 10 2021:	$1,088.60
```

If the input is valid, an estimated price should be returned. For example, we can see that our arguments gave us a price of `$1,088.60`.

### Web Application
We include a web application in our stack which allows you to see charts of all the stocks that have been run through our stock prediction application. A list of all symbols that have been queried can be found on the homepage, which link to a page plotting the respective stocks history.

The web application can be accessed by going to `localhost:3000` in your browser.

## Data source
Our project automatically loads data on start-up, which has to be supplied by the developer beforehand. 

A folder called "data" is located in the repository. Two files are included, `stock_histories.csv.gz` and `symbol_descriptions.txt`, which correspond to the `stocks` and `symbol_descriptions` tables respectively in our *Hive* database.
```
.
└── data
    ├── stock_histories.csv.gz
    └── symbol_descriptions.txt
```

We preprocessed the raw data before loading it with *Hive*. See [/hive/hive_setup.sql](/hive/hive_setup.sql) to see how we need the data formatted so that it can load.

We use market data collected using [Redtide](https://github.com/qks1lver/redtide) by [@qks1lver](https://github.com/qks1lver). You can view and download a nearly-up-to-date version at [kaggle.com/qks1lver/amex-nyse-nasdaq-stock-histories](https://www.kaggle.com/qks1lver/amex-nyse-nasdaq-stock-histories).

We concatenated the `AMEX.txt`, `NASDAQ.txt` and `NYSE.txt` files to make `symbol_descriptions.txt`, removing repeats of the first row.

For the stock histories, we first merged all the `full_history/<symbol>.csv` files together, with the `<symbol>` in the filename used as a new column value. This was achieved with a Python script, available at [/scripts/merge_stock_histories.py](/scripts/merge_stock_histories.py) to make `stock_histories.csv`. Having one file dramatically reduced the time it took `Hive` to load our data. *Note that was only the case due to how we stored our data.*

We then compressed the generated file using `gzip` to make `stock_histories.csv.gz`. We load from a compressed file because we want to distribute the sample dataset in a smaller file.
