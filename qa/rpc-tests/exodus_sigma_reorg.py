#!/usr/bin/env python3
from test_framework.test_framework import ExodusTestFramework
from test_framework.util import assert_equal

class ExodusSigmaReorgTest(ExodusTestFramework):
    def run_test(self):
        super().run_test()

        sigma_start_block = 500
        self.nodes[0].generate(sigma_start_block - self.nodes[0].getblockcount())

        # generate mints to spend
        for _ in range(0, 10):
            self.nodes[0].mint(1)

        self.nodes[0].generate(10)
        self.sync_all()

        # create sigma with denominations (1, 2)
        balance = '1000000'
        self.nodes[0].exodus_sendissuancefixed(
            self.addrs[0], 1, 1, 0, '', '', 'Sigma', '', '', balance, 1
        )

        self.nodes[0].generate(1)
        sigma_property = 3

        self.nodes[0].exodus_sendcreatedenomination(self.addrs[0], sigma_property, '1')
        self.nodes[0].generate(10)

        # reorg to reverse mint and spend
        self.nodes[0].exodus_sendmint(self.addrs[0], sigma_property, {0: 2})
        self.nodes[0].generate(1)

        mint_txid = self.nodes[0].exodus_sendmint(self.addrs[0], sigma_property, {0: 1})
        mint_tx = self.nodes[0].getrawtransaction(mint_txid)

        self.nodes[0].exodus_sendspend(self.addrs[0], sigma_property, 0)

        forked_block = self.nodes[0].generate(1)

        assert_equal(2, len(self.nodes[0].exodus_listmints()))
        assert_equal(0, len(self.nodes[0].exodus_listpendingmints()))

        # reorg
        self.nodes[0].invalidateblock(forked_block[0])

        # exodus state still doesn't detect reorg until new block come.
        assert_equal(2, len(self.nodes[0].exodus_listmints()))
        assert_equal(0, len(self.nodes[0].exodus_listpendingmints()))

        # forked
        self.nodes[0].clearmempool()
        self.nodes[0].generate(1)

        assert_equal(2, len(self.nodes[0].exodus_listmints())) # a spend is reverse to confirmed
        assert_equal(1, len(self.nodes[0].exodus_listpendingmints())) # a mint is reverse to unconfirmed

        # re-broadcast mint and spend
        self.nodes[0].clearmempool()
        self.nodes[0].sendrawtransaction(mint_tx)
        self.nodes[0].exodus_sendspend(self.addrs[0], sigma_property, 0)

        self.nodes[0].generate(1)

        assert_equal(2, len(self.nodes[0].exodus_listmints()))
        assert_equal(0, len(self.nodes[0].exodus_listpendingmints()))

        # spend all and check balance
        self.nodes[0].exodus_sendspend(self.addrs[0], sigma_property, 0)
        self.nodes[0].exodus_sendspend(self.addrs[0], sigma_property, 0)

        self.nodes[0].generate(1)

        assert_equal(balance, self.nodes[0].exodus_getbalance(self.addrs[0], sigma_property)['balance'])

if __name__ == '__main__':
    ExodusSigmaReorgTest().main()