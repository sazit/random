import {
  Connection,
  PublicKey,
  Keypair,
  Transaction,
  TransactionInstruction,
  sendAndConfirmTransaction,
  SystemProgram,
  LAMPORTS_PER_SOL,
} from '@solana/web3.js';
import * as borsh from 'borsh';

// Counter account data structure (matches Rust)
class CounterAccount {
  count: number = 0;
  authority: PublicKey = new PublicKey(0);

  constructor(properties: { count: number; authority: PublicKey }) {
    Object.assign(this, properties);
  }

  static schema = new Map([
    [CounterAccount, { kind: 'struct', fields: [['count', 'u64'], ['authority', [32]]] }],
  ]);
}

// Program instruction types (matches Rust enum)
enum CounterInstruction {
  Initialize = 0,
  Increment = 1,
  Decrement = 2,
}

/**
 * Simple Solana Counter Program Client
 * Demonstrates how to interact with Solana programs from JavaScript/TypeScript
 */
class CounterProgramClient {
  private connection: Connection;
  private programId: PublicKey;
  private payer: Keypair;

  constructor(connection: Connection, programId: PublicKey, payer: Keypair) {
    this.connection = connection;
    this.programId = programId;
    this.payer = payer;
  }

  /**
   * Initialize a new counter account
   */
  async initializeCounter(): Promise<PublicKey> {
    console.log('Initializing new counter...');

    // Generate a new keypair for the counter account
    const counterKeypair = Keypair.generate();
    console.log(`Counter account: ${counterKeypair.publicKey.toBase58()}`);

    // Calculate rent exemption amount
    const accountSpace = 8 + 32; // 8 bytes for count + 32 bytes for authority pubkey
    const rentExemption = await this.connection.getMinimumBalanceForRentExemption(accountSpace);

    // Create account instruction
    const createAccountIx = SystemProgram.createAccount({
      fromPubkey: this.payer.publicKey,
      newAccountPubkey: counterKeypair.publicKey,
      lamports: rentExemption,
      space: accountSpace,
      programId: this.programId,
    });

    // Create initialize instruction
    const initializeIx = new TransactionInstruction({
      keys: [
        { pubkey: this.payer.publicKey, isSigner: true, isWritable: false },
        { pubkey: counterKeypair.publicKey, isSigner: false, isWritable: true },
      ],
      programId: this.programId,
      data: Buffer.from([CounterInstruction.Initialize]),
    });

    // Send transaction
    const transaction = new Transaction().add(createAccountIx, initializeIx);
    const signature = await sendAndConfirmTransaction(
      this.connection,
      transaction,
      [this.payer, counterKeypair]
    );

    console.log(`Counter initialized! Transaction: ${signature}`);
    console.log(`View on Solana Explorer: https://explorer.solana.com/tx/${signature}?cluster=devnet`);

    return counterKeypair.publicKey;
  }

  /**
   * Increment the counter
   */
  async incrementCounter(counterAccount: PublicKey): Promise<void> {
    console.log('Incrementing counter...');

    const incrementIx = new TransactionInstruction({
      keys: [
        { pubkey: this.payer.publicKey, isSigner: true, isWritable: false },
        { pubkey: counterAccount, isSigner: false, isWritable: true },
      ],
      programId: this.programId,
      data: Buffer.from([CounterInstruction.Increment]),
    });

    const transaction = new Transaction().add(incrementIx);
    const signature = await sendAndConfirmTransaction(this.connection, transaction, [this.payer]);

    console.log(`Counter incremented! Transaction: ${signature}`);
  }

  /**
   * Decrement the counter
   */
  async decrementCounter(counterAccount: PublicKey): Promise<void> {
    console.log('Decrementing counter...');

    const decrementIx = new TransactionInstruction({
      keys: [
        { pubkey: this.payer.publicKey, isSigner: true, isWritable: false },
        { pubkey: counterAccount, isSigner: false, isWritable: true },
      ],
      programId: this.programId,
      data: Buffer.from([CounterInstruction.Decrement]),
    });

    const transaction = new Transaction().add(decrementIx);
    const signature = await sendAndConfirmTransaction(this.connection, transaction, [this.payer]);

    console.log(`Counter decremented! Transaction: ${signature}`);
  }

  /**
   * Get the current counter value
   */
  async getCounterValue(counterAccount: PublicKey): Promise<number> {
    const accountInfo = await this.connection.getAccountInfo(counterAccount);
    if (!accountInfo) {
      throw new Error('Counter account not found');
    }

    const counterData = borsh.deserialize(CounterAccount.schema, CounterAccount, accountInfo.data);
    return counterData.count;
  }

  /**
   * Display counter information
   */
  async displayCounterInfo(counterAccount: PublicKey): Promise<void> {
    try {
      const count = await this.getCounterValue(counterAccount);
      console.log(`Current counter value: ${count}`);
    } catch (error) {
      console.error('Error reading counter:', error);
    }
  }
}

/**
 * Main demo function
 */
async function main() {
  console.log('Solana Counter Program Demo\n');

  // Connect to Solana devnet
  const connection = new Connection('https://api.devnet.solana.com', 'confirmed');
  console.log('Connected to Solana devnet');

  // Load or generate payer keypair
  // In production, load from file: const payer = Keypair.fromSecretKey(...)
  const payer = Keypair.generate();
  console.log(`Payer address: ${payer.publicKey.toBase58()}`);

  // Request airdrop for testing (devnet only)
  console.log('Requesting SOL airdrop...');
  const airdropSignature = await connection.requestAirdrop(payer.publicKey, LAMPORTS_PER_SOL);
  await connection.confirmTransaction(airdropSignature);
  console.log('Airdrop received!');

  // Replace with your deployed program ID
  const programId = new PublicKey('11111111111111111111111111111111'); // Placeholder - use your actual program ID

  // Create client
  const client = new CounterProgramClient(connection, programId, payer);

  try {
    // Demo workflow
    console.log('\nStarting demo workflow...');

    // 1. Initialize counter
    const counterAccount = await client.initializeCounter();
    await client.displayCounterInfo(counterAccount);

    // 2. Increment counter multiple times
    for (let i = 0; i < 3; i++) {
      await client.incrementCounter(counterAccount);
      await client.displayCounterInfo(counterAccount);
    }

    // 3. Decrement counter
    await client.decrementCounter(counterAccount);
    await client.displayCounterInfo(counterAccount);

    console.log('\nDemo completed successfully!');
  } catch (error) {
    console.error('Demo failed:', error);
  }
}

// TypeScript configuration export
export { CounterProgramClient, CounterAccount, CounterInstruction };

// Run demo if this file is executed directly
if (require.main === module) {
  main().catch(console.error);
}
