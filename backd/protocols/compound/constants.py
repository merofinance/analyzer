"""
In the price oracle contract, some addresses use an external DSValue
storage, which address is stored in a "readers" mapping
https://etherscan.io/address/0x02557a5e05defeffd4cae6d83ea3d173b272c904#code

This mapping maps the "reader" contract to the (underlying) tokens using it

To get all the values, the following shell script can be used:

```sh
DATA_PATH=/path/to/data
for market in (jq -r .[].underlyingAddress $DATA_PATH/compound/markets.json)
    echo $market
    eth-tools call-contract --abi $DATA_PATH/abis/price-oracle.json -f readers -e 7715673 0x02557a5e05defeffd4cae6d83ea3d173b272c904 --args $market:address
end
```
"""
DS_VALUES_MAPPING = {
    "0x729d19f657bd0614b4985cf1d82531c67569197b": [
        "0x89d24a6b4ccb1b6faa2625fe562bdd9a23260359",  # SAI
        "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # USDC
    ]
}
