use borsh::{BorshDeserialize, BorshSerialize};
use simple_solana_program::{CounterAccount, CounterInstruction};
use solana_program::{
    instruction::{AccountMeta, Instruction},
    pubkey::Pubkey,
    rent::Rent,
    system_instruction,
};
use solana_program_test::*;
use solana_sdk::{
    account::Account,
    signature::{Keypair, Signer},
    transaction::Transaction,
};

/**
 * Integration tests for the Simple Counter Program
 * These tests run against a local Solana runtime simulation
 */

#[tokio::test]
async fn test_initialize_counter() {
    // Setup test environment
    let program_id = Pubkey::new_unique();
    let (mut banks_client, payer, recent_blockhash) = ProgramTest::new(
        "simple_solana_program",
        program_id,
        processor!(simple_solana_program::process_instruction),
    )
    .start()
    .await;

    // Generate counter account
    let counter_keypair = Keypair::new();
    let counter_pubkey = counter_keypair.pubkey();

    // Calculate rent exemption
    let rent = Rent::default();
    let account_space = std::mem::size_of::<CounterAccount>();
    let rent_exemption = rent.minimum_balance(account_space);

    // Create account instruction
    let create_account_ix = system_instruction::create_account(
        &payer.pubkey(),
        &counter_pubkey,
        rent_exemption,
        account_space as u64,
        &program_id,
    );

    // Create initialize instruction
    let initialize_data = CounterInstruction::Initialize.try_to_vec().unwrap();
    let initialize_ix = Instruction::new_with_bytes(
        program_id,
        &initialize_data,
        vec![
            AccountMeta::new(payer.pubkey(), true),
            AccountMeta::new(counter_pubkey, false),
        ],
    );

    // Execute transaction
    let mut transaction = Transaction::new_with_payer(
        &[create_account_ix, initialize_ix],
        Some(&payer.pubkey()),
    );
    transaction.sign(&[&payer, &counter_keypair], recent_blockhash);

    assert!(banks_client.process_transaction(transaction).await.is_ok());

    // Verify counter was initialized
    let counter_account = banks_client.get_account(counter_pubkey).await.unwrap().unwrap();
    let counter_data = CounterAccount::try_from_slice(&counter_account.data).unwrap();
    
    assert_eq!(counter_data.count, 0);
    assert_eq!(counter_data.authority, payer.pubkey());
}

#[tokio::test]
async fn test_increment_counter() {
    // Setup with initialized counter
    let program_id = Pubkey::new_unique();
    let (mut banks_client, payer, recent_blockhash) = ProgramTest::new(
        "simple_solana_program",
        program_id,
        processor!(simple_solana_program::process_instruction),
    )
    .start()
    .await;

    let counter_keypair = Keypair::new();
    let counter_pubkey = counter_keypair.pubkey();

    // Initialize counter (setup)
    let rent = Rent::default();
    let account_space = std::mem::size_of::<CounterAccount>();
    let rent_exemption = rent.minimum_balance(account_space);

    let create_account_ix = system_instruction::create_account(
        &payer.pubkey(),
        &counter_pubkey,
        rent_exemption,
        account_space as u64,
        &program_id,
    );

    let initialize_data = CounterInstruction::Initialize.try_to_vec().unwrap();
    let initialize_ix = Instruction::new_with_bytes(
        program_id,
        &initialize_data,
        vec![
            AccountMeta::new(payer.pubkey(), true),
            AccountMeta::new(counter_pubkey, false),
        ],
    );

    let mut setup_transaction = Transaction::new_with_payer(
        &[create_account_ix, initialize_ix],
        Some(&payer.pubkey()),
    );
    setup_transaction.sign(&[&payer, &counter_keypair], recent_blockhash);
    banks_client.process_transaction(setup_transaction).await.unwrap();

    // Now test increment
    let increment_data = CounterInstruction::Increment.try_to_vec().unwrap();
    let increment_ix = Instruction::new_with_bytes(
        program_id,
        &increment_data,
        vec![
            AccountMeta::new(payer.pubkey(), true),
            AccountMeta::new(counter_pubkey, true),
        ],
    );

    let mut increment_transaction = Transaction::new_with_payer(
        &[increment_ix],
        Some(&payer.pubkey()),
    );
    increment_transaction.sign(&[&payer], recent_blockhash);

    assert!(banks_client.process_transaction(increment_transaction).await.is_ok());

    // Verify counter incremented
    let counter_account = banks_client.get_account(counter_pubkey).await.unwrap().unwrap();
    let counter_data = CounterAccount::try_from_slice(&counter_account.data).unwrap();
    
    assert_eq!(counter_data.count, 1);
}

#[tokio::test]
async fn test_decrement_counter() {
    // Similar setup as increment test
    let program_id = Pubkey::new_unique();
    let (mut banks_client, payer, recent_blockhash) = ProgramTest::new(
        "simple_solana_program",
        program_id,
        processor!(simple_solana_program::process_instruction),
    )
    .start()
    .await;

    let counter_keypair = Keypair::new();
    let counter_pubkey = counter_keypair.pubkey();

    // Initialize and increment to have count = 1
    let rent = Rent::default();
    let account_space = std::mem::size_of::<CounterAccount>();
    let rent_exemption = rent.minimum_balance(account_space);

    let create_account_ix = system_instruction::create_account(
        &payer.pubkey(),
        &counter_pubkey,
        rent_exemption,
        account_space as u64,
        &program_id,
    );

    let initialize_data = CounterInstruction::Initialize.try_to_vec().unwrap();
    let initialize_ix = Instruction::new_with_bytes(
        program_id,
        &initialize_data,
        vec![
            AccountMeta::new(payer.pubkey(), true),
            AccountMeta::new(counter_pubkey, false),
        ],
    );

    let increment_data = CounterInstruction::Increment.try_to_vec().unwrap();
    let increment_ix = Instruction::new_with_bytes(
        program_id,
        &increment_data,
        vec![
            AccountMeta::new(payer.pubkey(), true),
            AccountMeta::new(counter_pubkey, true),
        ],
    );

    let mut setup_transaction = Transaction::new_with_payer(
        &[create_account_ix, initialize_ix, increment_ix],
        Some(&payer.pubkey()),
    );
    setup_transaction.sign(&[&payer, &counter_keypair], recent_blockhash);
    banks_client.process_transaction(setup_transaction).await.unwrap();

    // Now test decrement
    let decrement_data = CounterInstruction::Decrement.try_to_vec().unwrap();
    let decrement_ix = Instruction::new_with_bytes(
        program_id,
        &decrement_data,
        vec![
            AccountMeta::new(payer.pubkey(), true),
            AccountMeta::new(counter_pubkey, true),
        ],
    );

    let mut decrement_transaction = Transaction::new_with_payer(
        &[decrement_ix],
        Some(&payer.pubkey()),
    );
    decrement_transaction.sign(&[&payer], recent_blockhash);

    assert!(banks_client.process_transaction(decrement_transaction).await.is_ok());

    // Verify counter decremented back to 0
    let counter_account = banks_client.get_account(counter_pubkey).await.unwrap().unwrap();
    let counter_data = CounterAccount::try_from_slice(&counter_account.data).unwrap();
    
    assert_eq!(counter_data.count, 0);
}

#[tokio::test]
async fn test_unauthorized_access() {
    // Test that only the authority can modify the counter
    let program_id = Pubkey::new_unique();
    let (mut banks_client, payer, recent_blockhash) = ProgramTest::new(
        "simple_solana_program",
        program_id,
        processor!(simple_solana_program::process_instruction),
    )
    .start()
    .await;

    let counter_keypair = Keypair::new();
    let counter_pubkey = counter_keypair.pubkey();
    let unauthorized_user = Keypair::new();

    // Initialize counter with payer as authority
    let rent = Rent::default();
    let account_space = std::mem::size_of::<CounterAccount>();
    let rent_exemption = rent.minimum_balance(account_space);

    let create_account_ix = system_instruction::create_account(
        &payer.pubkey(),
        &counter_pubkey,
        rent_exemption,
        account_space as u64,
        &program_id,
    );

    let initialize_data = CounterInstruction::Initialize.try_to_vec().unwrap();
    let initialize_ix = Instruction::new_with_bytes(
        program_id,
        &initialize_data,
        vec![
            AccountMeta::new(payer.pubkey(), true),
            AccountMeta::new(counter_pubkey, false),
        ],
    );

    let mut setup_transaction = Transaction::new_with_payer(
        &[create_account_ix, initialize_ix],
        Some(&payer.pubkey()),
    );
    setup_transaction.sign(&[&payer, &counter_keypair], recent_blockhash);
    banks_client.process_transaction(setup_transaction).await.unwrap();

    // Try to increment with unauthorized user (should fail)
    let increment_data = CounterInstruction::Increment.try_to_vec().unwrap();
    let increment_ix = Instruction::new_with_bytes(
        program_id,
        &increment_data,
        vec![
            AccountMeta::new(unauthorized_user.pubkey(), true),
            AccountMeta::new(counter_pubkey, true),
        ],
    );

    let mut unauthorized_transaction = Transaction::new_with_payer(
        &[increment_ix],
        Some(&unauthorized_user.pubkey()),
    );
    unauthorized_transaction.sign(&[&unauthorized_user], recent_blockhash);

    // This should fail due to authority mismatch
    assert!(banks_client.process_transaction(unauthorized_transaction).await.is_err());
}
