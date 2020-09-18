TOOL_NAME = "backd"
LOG_FORMAT = "%(asctime)-15s - %(levelname)s - %(message)s"

CTOKEN_DECIMALS = 8
COMPOUND_FACTORS_DECIMALS = 18
CDAI_ADDRESS = "0x5d3a536e4d6dbd6114cc1ead35777bab948e3643"
CETH_ADDRESS = "0x4ddc2d193948926d02f9b1fe9e1daa0718270ed5"
NULL_ADDRESS = "0x0000000000000000000000000000000000000000"
ETH_ADDRESS = "0x0000000000000000000000000000000000000000"
DSR_DECIMALS = 27

COMPOUND_MARKETS = [
    {
        "address": "0x4ddc2d193948926d02f9b1fe9e1daa0718270ed5",
        "decimals": 18,
        "symbol": "cETH",
        "underlying_address": "0x0000000000000000000000000000000000000000",
        "underlying_symbol": "ETH",
    },
    {
        "address": "0x6c8c6b02e7b2be14d4fa6022dfd6d75921d90e4e",
        "decimals": 18,
        "symbol": "cBAT",
        "underlying_address": "0x0d8775f648430679a709e98d2b0cb6250d2887ef",
        "underlying_symbol": "BAT",
    },
    {
        "address": "0x5d3a536e4d6dbd6114cc1ead35777bab948e3643",
        "decimals": 18,
        "symbol": "cDAI",
        "underlying_address": "0x6b175474e89094c44da98b954eedeac495271d0f",
        "underlying_symbol": "DAI",
    },
    {
        "address": "0xf5dce57282a584d2746faf1593d3121fcac444dc",
        "decimals": 18,
        "symbol": "cSAI",
        "underlying_address": "0x89d24a6b4ccb1b6faa2625fe562bdd9a23260359",
        "underlying_symbol": "SAI",
    },
    {
        "address": "0x158079ee67fce2f58472a96584a73c7ab9ac95c1",
        "decimals": 18,
        "symbol": "cREP",
        "underlying_symbol": "REP",
        "underlying_address": "0x1985365e9f78359a9b6ad760e32412f4a445e862",
    },
    {
        "address": "0x39aa39c021dfbae8fac545936693ac917d5e7563",
        "decimals": 6,
        "symbol": "cUSDC",
        "underlying_address": "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",
        "underlying_symbol": "USDC",
    },
    {
        "address": "0xf650c3d88d12db855b8bf7d11be6c55a4e07dcc9",
        "decimals": 6,
        "symbol": "cUSDT",
        "underlying_address": "0xdac17f958d2ee523a2206206994597c13d831ec7",
        "underlying_symbol": "USDT",
    },
    {
        "address": "0xc11b1268c1a384e55c48c2391d8d480264a3a7f4",
        "decimals": 8,
        "symbol": "cWBTC",
        "underlying_address": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
        "underlying_symbol": "BTC",
    },
    {
        "address": "0xb3319f5d18bc0d84dd1b4825dcde5d5f7266d407",
        "decimals": 18,
        "symbol": "cZRX",
        "underlying_address": "0xe41d2489571d322189246dafa5ebde1f4699f498",
        "underlying_symbol": "ZRX",
    },
]
