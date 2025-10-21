use borsh::{BorshDeserialize, BorshSerialize};
use solana_program::{
    account_info::{next_account_info, AccountInfo},
    entrypoint,
    entrypoint::ProgramResult,
    msg,
    program_error::ProgramError,
    pubkey::Pubkey,
    rent::Rent,
    sysvar::Sysvar,
};

/// Define the type of state stored in accounts
/// This is like a database schema in traditional apps
#[derive(BorshSerialize, BorshDeserialize, Debug)]
pub struct CounterAccount {
    /// The current count value
    pub count: u64,
    /// The authority that can modify this counter
    pub authority: Pubkey,
}

/// Define program instructions
/// This is like API endpoints in traditional apps
#[derive(BorshSerialize, BorshDeserialize, Debug)]
pub enum CounterInstruction {
    /// Initialize a new counter account
    /// Accounts expected:
    /// 0. `[signer]` The account that will pay for the account creation
    /// 1. `[writable]` The counter account to create
    Initialize,
    
    /// Increment the counter
    /// Accounts expected:
    /// 0. `[signer]` The authority account
    /// 1. `[writable]` The counter account to increment
    Increment,
    
    /// Decrement the counter  
    /// Accounts expected:
    /// 0. `[signer]` The authority account
    /// 1. `[writable]` The counter account to decrement
    Decrement,
}

// Declare and export the program's entrypoint
entrypoint!(process_instruction);

/// Program entrypoint's implementation
/// This is the main function that processes all instructions
pub fn process_instruction(
    program_id: &Pubkey,
    accounts: &[AccountInfo],
    instruction_data: &[u8],
) -> ProgramResult {
    msg!("Simple Counter Program: Processing instruction");
    
    // Deserialize the instruction data
    let instruction = CounterInstruction::try_from_slice(instruction_data)
        .map_err(|_| ProgramError::InvalidInstructionData)?;
    
    match instruction {
        CounterInstruction::Initialize => {
            msg!("Instruction: Initialize");
            initialize_counter(program_id, accounts)
        }
        CounterInstruction::Increment => {
            msg!("Instruction: Increment");
            increment_counter(accounts)
        }
        CounterInstruction::Decrement => {
            msg!("Instruction: Decrement");
            decrement_counter(accounts)
        }
    }
}

/// Initialize a new counter account
fn initialize_counter(program_id: &Pubkey, accounts: &[AccountInfo]) -> ProgramResult {
    let account_iter = &mut accounts.iter();
    
    // Get accounts
    let authority = next_account_info(account_iter)?;
    let counter_account = next_account_info(account_iter)?;
    
    // Verify authority is signer
    if !authority.is_signer {
        msg!("Error: Authority must be a signer");
        return Err(ProgramError::MissingRequiredSignature);
    }
    
    // Verify counter account is owned by our program
    if counter_account.owner != program_id {
        msg!("Error: Counter account not owned by program");
        return Err(ProgramError::IncorrectProgramId);
    }
    
    // Check if account is already initialized
    if !counter_account.data_is_empty() {
        msg!("Error: Counter account already initialized");
        return Err(ProgramError::AccountAlreadyInitialized);
    }
    
    // Verify account has enough space
    let account_len = std::mem::size_of::<CounterAccount>();
    if counter_account.data_len() < account_len {
        msg!("Error: Counter account too small");
        return Err(ProgramError::AccountDataTooSmall);
    }
    
    // Verify account is rent exempt
    let rent = Rent::get()?;
    if !rent.is_exempt(counter_account.lamports(), account_len) {
        msg!("Error: Counter account not rent exempt");
        return Err(ProgramError::AccountNotRentExempt);
    }
    
    // Initialize the counter account
    let counter_data = CounterAccount {
        count: 0,
        authority: *authority.key,
    };
    
    // Serialize and store data
    counter_data.serialize(&mut *counter_account.data.borrow_mut())?;
    
    msg!("Counter initialized successfully with count: {}", counter_data.count);
    Ok(())
}

/// Increment the counter
fn increment_counter(accounts: &[AccountInfo]) -> ProgramResult {
    let account_iter = &mut accounts.iter();
    
    // Get accounts
    let authority = next_account_info(account_iter)?;
    let counter_account = next_account_info(account_iter)?;
    
    // Verify authority is signer
    if !authority.is_signer {
        msg!("Error: Authority must be a signer");
        return Err(ProgramError::MissingRequiredSignature);
    }
    
    // Deserialize counter account data
    let mut counter_data = CounterAccount::try_from_slice(&counter_account.data.borrow())?;
    
    // Verify authority matches
    if counter_data.authority != *authority.key {
        msg!("Error: Authority mismatch");
        return Err(ProgramError::InvalidAccountData);
    }
    
    // Increment counter (with overflow protection)
    counter_data.count = counter_data.count
        .checked_add(1)
        .ok_or(ProgramError::ArithmeticOverflow)?;
    
    // Serialize and store updated data
    counter_data.serialize(&mut *counter_account.data.borrow_mut())?;
    
    msg!("Counter incremented to: {}", counter_data.count);
    Ok(())
}

/// Decrement the counter
fn decrement_counter(accounts: &[AccountInfo]) -> ProgramResult {
    let account_iter = &mut accounts.iter();
    
    // Get accounts
    let authority = next_account_info(account_iter)?;
    let counter_account = next_account_info(account_iter)?;
    
    // Verify authority is signer
    if !authority.is_signer {
        msg!("Error: Authority must be a signer");
        return Err(ProgramError::MissingRequiredSignature);
    }
    
    // Deserialize counter account data
    let mut counter_data = CounterAccount::try_from_slice(&counter_account.data.borrow())?;
    
    // Verify authority matches
    if counter_data.authority != *authority.key {
        msg!("Error: Authority mismatch");
        return Err(ProgramError::InvalidAccountData);
    }
    
    // Decrement counter (with underflow protection)
    counter_data.count = counter_data.count
        .checked_sub(1)
        .ok_or(ProgramError::ArithmeticOverflow)?;
    
    // Serialize and store updated data
    counter_data.serialize(&mut *counter_account.data.borrow_mut())?;
    
    msg!("Counter decremented to: {}", counter_data.count);
    Ok(())
}

// Error handling utilities
impl From<std::io::Error> for ProgramError {
    fn from(_: std::io::Error) -> Self {
        ProgramError::InvalidAccountData
    }
}
