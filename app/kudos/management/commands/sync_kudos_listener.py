'''
    Copyright (C) 2018 Gitcoin Core

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Affero General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
    GNU Affero General Public License for more details.

    You should have received a copy of the GNU Affero General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.

'''

import logging
import time

from django.core.management.base import BaseCommand

from dashboard.utils import (
    get_bounty, get_web3, getBountyContract, getStandardBountiesContractAddresss, web3_process_bounty,
)
from kudos.utils import (getKudosContractAddress, getKudosContract, get_kudos_from_web3,
                         update_kudos_db, get_gen0_id_from_web3, get_kudos_map, KudosContract
                         )

logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("web3").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


def process_bounty(bounty_id, network):
    bounty = get_bounty(bounty_id, network)
    return web3_process_bounty(bounty)


class Command(BaseCommand):
    help = 'listens for kudos changes '

    def add_arguments(self, parser):
        parser.add_argument('--network', default='localhost', type=str)
        parser.add_argument('--account', help='public account address to use for transaction', type=str)
        parser.add_argument('--private_key', help='private key for signing transactions', type=str)

    def handle(self, *args, **options):
        # config
        block = 'latest'

        # setup
        network = options['network']
        account = options['account']
        private_key = options['private_key']

        kudos_contract = KudosContract(network=network, account=account, private_key=private_key)
        w3 = get_web3(network)
        # contract_address = getKudosContractAddress(network)
        # logger.info(f'Contract address: {contract_address}')

        # kudos_contract = getKudosContract(network)
        last_block_hash = None

        while True:
            # wait for a new block
            # logger.info(f'block: {block}')
            block = w3.eth.getBlock('latest')
            block_hash = block['hash']
            block_number = block['number']

            # logger.info(f'last_block_hash: {last_block_hash}')
            # logger.info(f'block_hash: {block_hash}')
            if last_block_hash == block_hash:
                time.sleep(1)
                continue

            logger.info('got new block %s' % w3.toHex(block_hash))
            logger.info(f'block id: {block_number}')

            # get txs
            transactions = block['transactions']
            for tx in transactions:
                tx = w3.eth.getTransaction(tx)
                if not tx or tx['to'] != kudos_contract.address:
                    continue

                logger.info('found a kudos tx')
                # logger.info(dir(tx))
                # logger.info(tx.keys())
                data = tx['input']
                method_id = data[:10]
                logger.info(f'method_id:  {method_id}')

                # Check if its a Clone or cloneAndTransfer function call
                if method_id == '0xdaa6eb1d' or method_id == '0x8a94e433':
                    kudos_contract.sync_db()
                    # # Get the kudos_id of the newly cloned Kudos
                    # kudos_id = kudos_contract.functions.totalSupply().call()
                    # # Update the database with the newly cloned Kudos
                    # update_kudos_db(kudos_id, network)
                    # # Find the name of the Kudos that was cloned
                    # kudos = get_kudos_from_web3(kudos_id, network)
                    # kudos_map = get_kudos_map(kudos)
                    # # Find the ID of the Gen0 Kudos that was cloned
                    # gen0_id = get_gen0_id_from_web3(kudos_map['name'], network)
                    # # Update the Gen0 Kudos in the database
                    # update_kudos_db(gen0_id, network)

            last_block_hash = block_hash
