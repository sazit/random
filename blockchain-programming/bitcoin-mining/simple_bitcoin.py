"""
Simple Bitcoin Mining Simulation
Demonstrates core blockchain concepts:
- Proof of Work (PoW) consensus
- SHA-256 hashing
- Block structure and mining
- Difficulty adjustment
- Transaction validation

This is educational code to understand Bitcoin's core mechanics
"""

import hashlib
import time
import json
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Transaction:
    """Represents a Bitcoin transaction"""
    sender: str
    receiver: str
    amount: float
    fee: float = 0.001  # Transaction fee
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()
    
    def to_dict(self) -> Dict:
        """Convert transaction to dictionary for hashing"""
        return asdict(self)
    
    def get_hash(self) -> str:
        """Calculate transaction hash"""
        tx_string = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(tx_string.encode()).hexdigest()
    
    def is_valid(self) -> bool:
        """Basic transaction validation"""
        return (
            self.sender != self.receiver and
            self.amount > 0 and
            self.fee >= 0 and
            len(self.sender) > 0 and
            len(self.receiver) > 0
        )


@dataclass
class Block:
    """Represents a Bitcoin block"""
    index: int
    timestamp: float
    transactions: List[Transaction]
    previous_hash: str
    merkle_root: str
    nonce: int = 0
    difficulty: int = 4
    
    def __post_init__(self):
        if not self.merkle_root:
            self.merkle_root = self.calculate_merkle_root()
    
    def calculate_merkle_root(self) -> str:
        """Calculate Merkle tree root of all transactions"""
        if not self.transactions:
            return "0" * 64
        
        # Simple Merkle root calculation (in production, use proper Merkle tree)
        tx_hashes = [tx.get_hash() for tx in self.transactions]
        
        while len(tx_hashes) > 1:
            if len(tx_hashes) % 2 == 1:
                tx_hashes.append(tx_hashes[-1])  # Duplicate last hash if odd number
            
            new_hashes = []
            for i in range(0, len(tx_hashes), 2):
                combined = tx_hashes[i] + tx_hashes[i + 1]
                new_hashes.append(hashlib.sha256(combined.encode()).hexdigest())
            
            tx_hashes = new_hashes
        
        return tx_hashes[0] if tx_hashes else "0" * 64
    
    def get_block_data(self) -> str:
        """Get block data for hashing (without nonce)"""
        return f"{self.index}{self.timestamp}{self.previous_hash}{self.merkle_root}{self.difficulty}"
    
    def calculate_hash(self) -> str:
        """Calculate block hash with current nonce"""
        block_string = self.get_block_data() + str(self.nonce)
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self) -> Dict:
        """
        Mine the block by finding a nonce that produces a hash with required difficulty
        Returns mining statistics
        """
        target = "0" * self.difficulty  # Target: hash must start with this many zeros
        start_time = time.time()
        attempts = 0
        
        print(f"Mining block {self.index}...")
        print(f"Target difficulty: {self.difficulty} leading zeros")
        print(f"Transactions in block: {len(self.transactions)}")
        
        while True:
            attempts += 1
            hash_result = self.calculate_hash()
            
            # Show progress every 100,000 attempts
            if attempts % 100000 == 0:
                elapsed = time.time() - start_time
                hash_rate = attempts / elapsed if elapsed > 0 else 0
                print(f"   Attempt: {attempts:,} | Hash rate: {hash_rate:,.0f} H/s | Current hash: {hash_result[:20]}...")
            
            # Check if we found a valid hash
            if hash_result.startswith(target):
                mining_time = time.time() - start_time
                hash_rate = attempts / mining_time if mining_time > 0 else 0
                
                print(f"Block mined successfully!")
                print(f"Winning hash: {hash_result}")
                print(f"Winning nonce: {self.nonce}")
                print(f"Mining time: {mining_time:.2f} seconds")
                print(f"Hash rate: {hash_rate:,.0f} H/s")
                print(f"Total attempts: {attempts:,}")
                
                return {
                    'hash': hash_result,
                    'nonce': self.nonce,
                    'attempts': attempts,
                    'mining_time': mining_time,
                    'hash_rate': hash_rate,
                    'difficulty': self.difficulty
                }
            
            self.nonce += 1
            
            # Safety check to prevent infinite loops in high difficulty
            if attempts > 10_000_000:  # 10 million attempts max for demo
                print(f"Stopping after {attempts:,} attempts (demo limit)")
                break


class SimpleBitcoinBlockchain:
    """Simple Bitcoin-like blockchain implementation"""
    
    def __init__(self):
        self.chain: List[Block] = []
        self.difficulty = 4  # Number of leading zeros required
        self.mining_reward = 50.0  # Reward for mining a block
        self.transaction_pool: List[Transaction] = []  # Mempool
        self.balances: Dict[str, float] = {
            "genesis": 1000000.0,  # Genesis account with initial supply
        }
        
        # Create genesis block
        self.create_genesis_block()
    
    def create_genesis_block(self):
        """Create the first block in the blockchain"""
        genesis_tx = Transaction(
            sender="genesis",
            receiver="miner1", 
            amount=100.0,
            timestamp=time.time()
        )
        
        genesis_block = Block(
            index=0,
            timestamp=time.time(),
            transactions=[genesis_tx],
            previous_hash="0" * 64,  # Genesis block has no previous hash
            merkle_root="",
            difficulty=self.difficulty
        )
        
        print("Creating Genesis Block...")
        mining_stats = genesis_block.mine_block()
        self.chain.append(genesis_block)
        
        # Update balances
        self.update_balances([genesis_tx])
        
        print(f"Genesis block created with hash: {mining_stats['hash']}\n")
    
    def get_latest_block(self) -> Block:
        """Get the most recent block"""
        return self.chain[-1]
    
    def add_transaction(self, transaction: Transaction) -> bool:
        """Add a transaction to the mempool"""
        if not transaction.is_valid():
            print(f"Invalid transaction: {transaction}")
            return False
        
        # Check if sender has sufficient balance
        sender_balance = self.balances.get(transaction.sender, 0)
        total_required = transaction.amount + transaction.fee
        
        if sender_balance < total_required:
            print(f"Insufficient balance. Required: {total_required}, Available: {sender_balance}")
            return False
        
        self.transaction_pool.append(transaction)
        print(f"Transaction added to mempool: {transaction.sender} -> {transaction.receiver} ({transaction.amount} BTC)")
        return True
    
    def update_balances(self, transactions: List[Transaction]):
        """Update account balances based on transactions"""
        for tx in transactions:
            # Deduct from sender
            if tx.sender in self.balances:
                self.balances[tx.sender] -= (tx.amount + tx.fee)
            
            # Add to receiver
            if tx.receiver not in self.balances:
                self.balances[tx.receiver] = 0
            self.balances[tx.receiver] += tx.amount
            
            # Transaction fees go to miner (simplified)
    
    def mine_block(self, miner_address: str) -> Optional[Block]:
        """Mine a new block with pending transactions"""
        if not self.transaction_pool:
            print("No transactions to mine")
            return None
        
        # Create coinbase transaction (mining reward)
        coinbase_tx = Transaction(
            sender="coinbase",
            receiver=miner_address,
            amount=self.mining_reward,
            fee=0.0,
            timestamp=time.time()
        )
        
        # Add transaction fees to mining reward
        total_fees = sum(tx.fee for tx in self.transaction_pool)
        if total_fees > 0:
            fee_tx = Transaction(
                sender="fees",
                receiver=miner_address,
                amount=total_fees,
                fee=0.0,
                timestamp=time.time()
            )
            transactions = [coinbase_tx, fee_tx] + self.transaction_pool
        else:
            transactions = [coinbase_tx] + self.transaction_pool
        
        # Create new block
        new_block = Block(
            index=len(self.chain),
            timestamp=time.time(),
            transactions=transactions,
            previous_hash=self.get_latest_block().calculate_hash(),
            merkle_root="",
            difficulty=self.difficulty
        )
        
        # Mine the block
        mining_stats = new_block.mine_block()
        
        if mining_stats:
            # Add to blockchain
            self.chain.append(new_block)
            
            # Update balances
            self.update_balances(transactions)
            
            # Clear transaction pool
            self.transaction_pool = []
            
            print(f"Block {new_block.index} added to blockchain\n")
            return new_block
        
        return None
    
    def adjust_difficulty(self):
        """Adjust mining difficulty based on recent block times"""
        if len(self.chain) < 10:  # Need at least 10 blocks
            return
        
        # Calculate average time for last 10 blocks
        recent_blocks = self.chain[-10:]
        time_diff = recent_blocks[-1].timestamp - recent_blocks[0].timestamp
        average_time = time_diff / 9  # 9 intervals between 10 blocks
        
        target_time = 10.0  # Target 10 seconds per block (faster than Bitcoin's 10 minutes for demo)
        
        if average_time < target_time * 0.8:  # Too fast
            self.difficulty += 1
            print(f"Difficulty increased to {self.difficulty}")
        elif average_time > target_time * 1.2:  # Too slow
            self.difficulty = max(1, self.difficulty - 1)
            print(f"Difficulty decreased to {self.difficulty}")
    
    def is_chain_valid(self) -> bool:
        """Validate the entire blockchain"""
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            # Check if current block's hash is valid
            if not current_block.calculate_hash().startswith("0" * current_block.difficulty):
                print(f"Invalid hash for block {i}")
                return False
            
            # Check if previous hash matches
            if current_block.previous_hash != previous_block.calculate_hash():
                print(f"Previous hash mismatch at block {i}")
                return False
        
        print("Blockchain is valid")
        return True
    
    def get_balance(self, address: str) -> float:
        """Get account balance"""
        return self.balances.get(address, 0.0)
    
    def print_blockchain_info(self):
        """Print blockchain statistics"""
        print("\n" + "="*60)
        print("BLOCKCHAIN STATISTICS")
        print("="*60)
        print(f"Total blocks: {len(self.chain)}")
        print(f"Current difficulty: {self.difficulty}")
        print(f"Transactions in mempool: {len(self.transaction_pool)}")
        
        print("\nACCOUNT BALANCES:")
        for address, balance in self.balances.items():
            if balance > 0:
                print(f"   {address}: {balance:.6f} BTC")
        
        print(f"\nRECENT BLOCKS:")
        for block in self.chain[-3:]:  # Show last 3 blocks
            tx_count = len(block.transactions)
            block_hash = block.calculate_hash()[:20] + "..."
            print(f"   Block {block.index}: {tx_count} txs, Hash: {block_hash}")
        print("="*60)


def demo_bitcoin_mining():
    """Demonstrate Bitcoin mining simulation"""
    print("Bitcoin Mining Simulation Started")
    print("This demonstrates Proof of Work consensus and blockchain basics\n")
    
    # Create blockchain
    blockchain = SimpleBitcoinBlockchain()
    
    # Add some transactions
    print("Adding transactions to mempool...")
    blockchain.add_transaction(Transaction("miner1", "alice", 25.0, fee=0.001))
    blockchain.add_transaction(Transaction("miner1", "bob", 15.0, fee=0.002))
    blockchain.add_transaction(Transaction("alice", "charlie", 10.0, fee=0.001))
    
    # Mine first block
    print("\nMining Block 1...")
    blockchain.mine_block("miner1")
    blockchain.print_blockchain_info()
    
    # Add more transactions
    print("\nAdding more transactions...")
    blockchain.add_transaction(Transaction("bob", "alice", 5.0, fee=0.001))
    blockchain.add_transaction(Transaction("charlie", "bob", 3.0, fee=0.002))
    
    # Mine second block
    print("\nMining Block 2...")
    blockchain.mine_block("miner2")
    
    # Adjust difficulty and mine another block
    blockchain.adjust_difficulty()
    blockchain.add_transaction(Transaction("alice", "dave", 8.0, fee=0.001))
    
    print("\nMining Block 3...")
    blockchain.mine_block("miner1")
    
    # Final statistics
    blockchain.print_blockchain_info()
    
    # Validate blockchain
    print("\nValidating blockchain integrity...")
    blockchain.is_chain_valid()
    
    print("\nBitcoin mining simulation completed!")
    print("\nKey concepts demonstrated:")
    print("   - Proof of Work consensus")
    print("   - SHA-256 hashing")
    print("   - Block structure and merkle roots")
    print("   - Transaction validation")
    print("   - Difficulty adjustment")
    print("   - Mining rewards and fees")
    print("   - Blockchain validation")


if __name__ == "__main__":
    demo_bitcoin_mining()