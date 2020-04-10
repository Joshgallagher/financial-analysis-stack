const express = require('express')
const redis = require('redis')
const moment = require('moment')

const app = express()
const port = 3000

const client = redis.createClient(6379, 'redis');
const { promisify } = require('util');
const getAsync = promisify(client.get).bind(client);
const keysAsync = promisify(client.keys).bind(client);
const hgetallAsync = promisify(client.hgetall).bind(client);

app.set('view engine', 'ejs');

app.get('/', async (req, res) => {
    const keys = await keysAsync('stocks:name:*')
    const stocks = keys.map(stock => stock.split(':')[2]);

    res.render('stocks', { stocks })
})

app.get('/:symbol', async (req, res) => {
    const { params: { symbol } } = req

    let model = await hgetallAsync(`stocks:query:${symbol}`)
    const orderedModel = Object.entries(model)
        .sort()
        .reduce((p, c) => {
            p[c[0]] = c[1];

            return p;
        }, {});

    let dates = []
    let value = []
    for (let [key, point] of Object.entries(orderedModel)) {
        dates.push(key)
        value.push(point)
    }

    const coeffecient = await getAsync(`stocks:model:${symbol}:coefficient`)
    const intercept = await getAsync(`stocks:model:${symbol}:intercept`)

    const regressionPoints = [
        [dates[0], (Math.floor(Date.parse(dates[0]) / 8.64e7) + 718821) * parseFloat(coeffecient) + parseFloat(intercept)],
        [dates.slice(-1)[0], (Math.floor(Date.parse(dates.slice(-1)[0]) / 8.64e7) + 718821) * parseFloat(coeffecient) + parseFloat(intercept)]
    ]

    res.render('stock', { symbol, dates, value, rp: regressionPoints })
})

app.listen(port, () => console.log(`Example app listening at http://localhost:${port}`))
