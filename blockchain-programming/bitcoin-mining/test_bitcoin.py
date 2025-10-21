"""
Test suite for Simple Bitcoin Mining Simulation
Demonstrates testing blockchain applications and core concepts validation
"""

import unittest
import time
from simple_bitcoin import Transaction, Block, SimpleBitcoinBlockchain


class TestTransaction(unittest.TestCase):
    """Test Transaction functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.valid_tx = Transaction("alice", "bob", 10.0, fee=0.001)
    
    def test_transaction_creation(self):
        """Test transaction creation with valid data"""
        self.assertEqual(self.valid_tx.sender, "alice")
        self.assertEqual(self.valid_tx.receiver, "bob")
        self.assertEqual(self.valid_tx.amount, 10.0)
        self.assertEqual(self.valid_tx.fee, 0.001)
        self.assertIsNotNone(self.valid_tx.timestamp)
    
    def test_transaction_hash(self):
        """Test transaction hashing is deterministic"""
        tx1 = Transaction("alice", "bob", 10.0, fee=0.001, timestamp=1234567890)
        tx2 = Transaction("alice", "bob", 10.0, fee=0.001, timestamp=1234567890)
        
        # Same transactions should have same hash
        self.assertEqual(tx1.get_hash(), tx2.get_hash())
        
        # Different transactions should have different hashes
        tx3 = Transaction("alice", "bob", 11.0, fee=0.001, timestamp=1234567890)
        self.assertNotEqual(tx1.get_hash(), tx3.get_hash())
    
    def test_transaction_validation(self):
        """Test transaction validation rules"""
        # Valid transaction
        valid_tx = Transaction("alice", "bob", 10.0, fee=0.001)
        self.assertTrue(valid_tx.is_valid())
        
        # Invalid: same sender and receiver
        invalid_tx1 = Transaction("alice", "alice", 10.0, fee=0.001)
        self.assertFalse(invalid_tx1.is_valid())
        
        # Invalid: negative amount
        invalid_tx2 = Transaction("alice", "bob", -10.0, fee=0.001)
        self.assertFalse(invalid_tx2.is_valid())
        
        # Invalid: empty sender
        invalid_tx3 = Transaction("", "bob", 10.0, fee=0.001)
        self.assertFalse(invalid_tx3.is_valid())


class TestBlock(unittest.TestCase):
    """Test Block functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.transactions = [
            Transaction("alice", "bob", 10.0, fee=0.001, timestamp=1234567890),
            Transaction("bob", "charlie", 5.0, fee=0.001, timestamp=1234567891)
        ]
        
        self.test_block = Block(
            index=1,
            timestamp=1234567892,
            transactions=self.transactions,
            previous_hash="0" * 64,
            merkle_root="",
            difficulty=2  # Low difficulty for testing
        )
    
    def test_block_creation(self):
        """Test block creation"""
        self.assertEqual(self.test_block.index, 1)
        self.assertEqual(len(self.test_block.transactions), 2)
        self.assertEqual(self.test_block.difficulty, 2)
        self.assertIsNotNone(self.test_block.merkle_root)
    
    def test_merkle_root_calculation(self):
        """Test Merkle root calculation"""
        # Empty transactions should return zero hash
        empty_block = Block(1, time.time(), [], "prev_hash", "", difficulty=1)
        self.assertEqual(empty_block.merkle_root, "0" * 64)
        
        # Same transactions should produce same Merkle root
        block1 = Block(1, 1234567890, self.transactions, "prev_hash", "", difficulty=1)
        block2 = Block(1, 1234567890, self.transactions, "prev_hash", "", difficulty=1)
        self.assertEqual(block1.merkle_root, block2.merkle_root)
    
    def test_block_hashing(self):
        """Test block hashing"""
        # Same block data should produce same hash
        hash1 = self.test_block.calculate_hash()
        hash2 = self.test_block.calculate_hash()
        self.assertEqual(hash1, hash2)
        
        # Different nonce should produce different hash
        self.test_block.nonce = 12345
        hash3 = self.test_block.calculate_hash()
        self.assertNotEqual(hash1, hash3)
    
    def test_mining_with_low_difficulty(self):
        """Test mining with low difficulty"""
        # Use very low difficulty for fast testing
        self.test_block.difficulty = 1
        
        mining_stats = self.test_block.mine_block()
        
        self.assertIsNotNone(mining_stats)
        self.assertTrue(mining_stats['hash'].startswith("0"))
        self.assertGreater(mining_stats['attempts'], 0)
        self.assertGreater(mining_stats['hash_rate'], 0)


class TestSimpleBitcoinBlockchain(unittest.TestCase):
    """Test SimpleBitcoinBlockchain functionality"""
    
    def setUp(self):
        """Set up test blockchain"""
        self.blockchain = SimpleBitcoinBlockchain()
        # Use low difficulty for faster testing
        self.blockchain.difficulty = 1
    
    def test_genesis_block_creation(self):
        """Test genesis block is created properly"""
        self.assertEqual(len(self.blockchain.chain), 1)
        genesis = self.blockchain.chain[0]
        self.assertEqual(genesis.index, 0)
        self.assertEqual(genesis.previous_hash, "0" * 64)
        self.assertTrue(len(genesis.transactions) > 0)
    
    def test_balance_management(self):
        """Test account balance tracking"""
        initial_balance = self.blockchain.get_balance("miner1")
        self.assertGreater(initial_balance, 0)
        
        # Add transaction
        tx = Transaction("miner1", "alice", 10.0, fee=0.001)
        success = self.blockchain.add_transaction(tx)
        self.assertTrue(success)
        
        # Balance should remain same until block is mined
        self.assertEqual(self.blockchain.get_balance("miner1"), initial_balance)
    
    def test_transaction_validation(self):
        """Test transaction validation in blockchain context"""
        # Valid transaction with sufficient balance
        valid_tx = Transaction("miner1", "alice", 10.0, fee=0.001)
        self.assertTrue(self.blockchain.add_transaction(valid_tx))
        
        # Invalid transaction with insufficient balance
        invalid_tx = Transaction("miner1", "alice", 999999.0, fee=0.001)
        self.assertFalse(self.blockchain.add_transaction(invalid_tx))
        
        # Invalid transaction structure
        malformed_tx = Transaction("", "alice", 10.0, fee=0.001)
        self.assertFalse(self.blockchain.add_transaction(malformed_tx))
    
    def test_mining_process(self):
        """Test block mining process"""
        # Add transactions to mine
        self.blockchain.add_transaction(Transaction("miner1", "alice", 10.0, fee=0.001))
        self.blockchain.add_transaction(Transaction("miner1", "bob", 5.0, fee=0.002))
        
        initial_chain_length = len(self.blockchain.chain)
        initial_mempool_size = len(self.blockchain.transaction_pool)
        
        # Mine block
        new_block = self.blockchain.mine_block("miner2")
        
        # Verify mining results
        self.assertIsNotNone(new_block)
        self.assertEqual(len(self.blockchain.chain), initial_chain_length + 1)
        self.assertEqual(len(self.blockchain.transaction_pool), 0)  # Mempool should be cleared
        
        # Verify miner received reward
        miner_balance = self.blockchain.get_balance("miner2")
        self.assertGreater(miner_balance, self.blockchain.mining_reward)  # Reward + fees
    
    def test_blockchain_validation(self):
        """Test blockchain integrity validation"""
        # Initially valid
        self.assertTrue(self.blockchain.is_chain_valid())
        
        # Mine a few blocks
        for i in range(2):
            self.blockchain.add_transaction(Transaction("miner1", f"user{i}", 5.0, fee=0.001))
            self.blockchain.mine_block(f"miner{i}")
        
        # Should still be valid
        self.assertTrue(self.blockchain.is_chain_valid())
    
    def test_difficulty_adjustment(self):
        """Test difficulty adjustment mechanism"""
        initial_difficulty = self.blockchain.difficulty
        
        # Need at least 10 blocks for adjustment
        for i in range(12):
            self.blockchain.add_transaction(Transaction("genesis", f"user{i}", 1.0, fee=0.001))
            self.blockchain.mine_block(f"miner{i % 3}")
        
        # Difficulty should have been adjusted
        self.blockchain.adjust_difficulty()
        
        # Difficulty should be positive
        self.assertGreater(self.blockchain.difficulty, 0)
    
    def test_double_spending_prevention(self):
        """Test that double spending is prevented"""
        # Get initial balance
        initial_balance = self.blockchain.get_balance("miner1")
        
        # Try to spend more than available
        large_amount = initial_balance + 100
        double_spend_tx = Transaction("miner1", "alice", large_amount, fee=0.001)
        
        # Should be rejected
        self.assertFalse(self.blockchain.add_transaction(double_spend_tx))
        
        # Balance should remain unchanged
        self.assertEqual(self.blockchain.get_balance("miner1"), initial_balance)


class TestCryptographicOperations(unittest.TestCase):
    """Test cryptographic operations and security properties"""
    
    def test_hash_determinism(self):
        """Test that hashes are deterministic"""
        tx = Transaction("alice", "bob", 10.0, fee=0.001, timestamp=1234567890)
        
        hash1 = tx.get_hash()
        hash2 = tx.get_hash()
        
        self.assertEqual(hash1, hash2)
        self.assertEqual(len(hash1), 64)  # SHA-256 produces 64-character hex string
    
    def test_hash_avalanche_effect(self):
        """Test that small changes produce very different hashes"""
        tx1 = Transaction("alice", "bob", 10.0, fee=0.001, timestamp=1234567890)
        tx2 = Transaction("alice", "bob", 10.1, fee=0.001, timestamp=1234567890)  # Tiny change
        
        hash1 = tx1.get_hash()
        hash2 = tx2.get_hash()
        
        self.assertNotEqual(hash1, hash2)
        
        # Count different characters (should be roughly 50% for good hash function)
        different_chars = sum(c1 != c2 for c1, c2 in zip(hash1, hash2))
        self.assertGreater(different_chars, 20)  # At least 20/64 characters different
    
    def test_mining_proof_of_work(self):
        """Test that mining actually requires work"""
        block = Block(
            index=1,
            timestamp=time.time(),
            transactions=[Transaction("alice", "bob", 10.0)],
            previous_hash="test_hash",
            merkle_root="",
            difficulty=2
        )
        
        start_time = time.time()
        mining_stats = block.mine_block()
        mining_duration = time.time() - start_time
        
        # Mining should take some time and attempts
        self.assertIsNotNone(mining_stats)
        self.assertGreater(mining_stats['attempts'], 1)
        self.assertTrue(mining_stats['hash'].startswith("00"))  # Difficulty 2
        
        # Verify the proof of work
        final_hash = block.calculate_hash()
        self.assertEqual(final_hash, mining_stats['hash'])


if __name__ == "__main__":
    print("Running Bitcoin Mining Simulation Tests")
    print("=" * 50)
    
    # Run all tests
    unittest.main(verbosity=2)