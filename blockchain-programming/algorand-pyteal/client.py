"""
Algorand Counter Client
Demonstrates how to interact with Algorand smart contracts using the Python SDK
"""

import base64
import json
from algosdk import account, mnemonic, transaction, logic
from algosdk.v2client import algod, indexer
from algosdk.future.transaction import ApplicationCreateTxn, ApplicationCallTxn, OnComplete, StateSchema
import time

class AlgorandCounterClient:
    """Client for interacting with the Algorand Counter smart contract"""
    
    def __init__(self, algod_client, private_key=None, mnemonic_phrase=None):
        """
        Initialize the client
        
        Args:
            algod_client: Algorand client instance
            private_key: Account private key (optional)
            mnemonic_phrase: Account mnemonic (optional)
        """
        self.algod_client = algod_client
        
        if private_key:
            self.private_key = private_key
            self.address = account.address_from_private_key(private_key)
        elif mnemonic_phrase:
            self.private_key = mnemonic.to_private_key(mnemonic_phrase)
            self.address = account.address_from_private_key(self.private_key)
        else:
            # Generate new account for demo
            self.private_key, self.address = account.generate_account()
            self.mnemonic_phrase = mnemonic.from_private_key(self.private_key)
            print(f"Generated new account: {self.address}")
            print(f"Mnemonic: {self.mnemonic_phrase}")
            print("Save this mnemonic safely!")
        
        self.app_id = None
    
    def get_account_info(self):
        """Get account information"""
        try:
            account_info = self.algod_client.account_info(self.address)
            balance = account_info['amount'] / 1_000_000  # Convert microAlgos to Algos
            print(f"Account balance: {balance:.6f} ALGO")
            return account_info
        except Exception as e:
            print(f"Error getting account info: {e}")
            return None
    
    def wait_for_confirmation(self, txid):
        """Wait for transaction confirmation"""
        last_round = self.algod_client.status().get('last-round')
        txinfo = self.algod_client.pending_transaction_info(txid)
        
        while not (txinfo.get('confirmed-round') and txinfo.get('confirmed-round') > 0):
            print(f"Waiting for confirmation... (Round {last_round})")
            last_round += 1
            self.algod_client.status_after_block(last_round)
            txinfo = self.algod_client.pending_transaction_info(txid)
        
        print(f"Transaction confirmed in round {txinfo.get('confirmed-round')}")
        return txinfo
    
    def create_app(self, approval_teal_code, clear_teal_code):
        """
        Create the counter application on Algorand
        
        Args:
            approval_teal_code: Compiled approval program TEAL code
            clear_teal_code: Compiled clear state program TEAL code
        """
        try:
            print("Creating Algorand Counter Application...")
            
            # Compile TEAL programs
            approval_program = self.algod_client.compile(approval_teal_code)
            clear_program = self.algod_client.compile(clear_teal_code)
            
            # Define schema
            global_schema = StateSchema(num_ints=4, num_byte_slices=0)
            local_schema = StateSchema(num_ints=0, num_byte_slices=0)
            
            # Get transaction parameters
            params = self.algod_client.suggested_params()
            
            # Create application creation transaction
            create_txn = ApplicationCreateTxn(
                sender=self.address,
                sp=params,
                on_complete=OnComplete.NoOpOC,
                approval_program=base64.b64decode(approval_program['result']),
                clear_program=base64.b64decode(clear_program['result']),
                global_schema=global_schema,
                local_schema=local_schema
            )
            
            # Sign and submit transaction
            signed_txn = create_txn.sign(self.private_key)
            txid = self.algod_client.send_transaction(signed_txn)
            
            print(f"Creation transaction ID: {txid}")
            
            # Wait for confirmation
            txinfo = self.wait_for_confirmation(txid)
            
            # Get application ID
            self.app_id = txinfo['application-index']
            print(f"Application created with ID: {self.app_id}")
            
            return self.app_id
            
        except Exception as e:
            print(f"Error creating application: {e}")
            return None
    
    def call_app(self, method, app_args=None):
        """
        Call a method on the deployed application
        
        Args:
            method: Method name to call
            app_args: Additional arguments for the method
        """
        if not self.app_id:
            print("No application deployed. Create application first.")
            return None
        
        try:
            print(f"Calling method '{method}' on app {self.app_id}")
            
            # Prepare arguments
            call_args = [method.encode('utf-8')]
            if app_args:
                call_args.extend([arg.encode('utf-8') if isinstance(arg, str) else arg for arg in app_args])
            
            # Get transaction parameters
            params = self.algod_client.suggested_params()
            
            # Create application call transaction
            call_txn = ApplicationCallTxn(
                sender=self.address,
                sp=params,
                index=self.app_id,
                on_complete=OnComplete.NoOpOC,
                app_args=call_args
            )
            
            # Sign and submit transaction
            signed_txn = call_txn.sign(self.private_key)
            txid = self.algod_client.send_transaction(signed_txn)
            
            print(f"Call transaction ID: {txid}")
            
            # Wait for confirmation
            txinfo = self.wait_for_confirmation(txid)
            
            print(f"Method '{method}' executed successfully")
            return txinfo
            
        except Exception as e:
            print(f"Error calling method '{method}': {e}")
            return None
    
    def read_global_state(self):
        """Read the global state of the application"""
        if not self.app_id:
            print("No application deployed.")
            return None
        
        try:
            app_info = self.algod_client.application_info(self.app_id)
            global_state = app_info['params']['global-state']
            
            print(f"\nGlobal State for App {self.app_id}:")
            print("-" * 40)
            
            state_data = {}
            for item in global_state:
                key = base64.b64decode(item['key']).decode('utf-8')
                
                if item['value']['type'] == 1:  # byte slice
                    value = base64.b64decode(item['value']['bytes']).decode('utf-8')
                else:  # integer
                    value = item['value']['uint']
                
                state_data[key] = value
                print(f"   {key}: {value}")
            
            print("-" * 40)
            return state_data
            
        except Exception as e:
            print(f"Error reading global state: {e}")
            return None
    
    def increment_counter(self):
        """Increment the counter"""
        return self.call_app("increment")
    
    def decrement_counter(self):
        """Decrement the counter"""
        return self.call_app("decrement")
    
    def reset_counter(self):
        """Reset the counter (only creator can call)"""
        return self.call_app("reset")


def setup_algorand_client():
    """Setup Algorand client for TestNet"""
    # Algorand TestNet configuration
    algod_address = "https://testnet-api.algonode.cloud"
    algod_token = ""  # Public TestNet node
    
    try:
        client = algod.AlgodClient(algod_token, algod_address)
        status = client.status()
        print(f"Connected to Algorand TestNet")
        print(f"   Last round: {status['last-round']}")
        print(f"   Network: {status.get('network', 'TestNet')}")
        return client
    except Exception as e:
        print(f"Failed to connect to Algorand: {e}")
        return None


def demo_counter_app():
    """Demonstrate the counter application"""
    print("Algorand Counter Demo")
    print("=" * 50)
    
    # Setup client
    algod_client = setup_algorand_client()
    if not algod_client:
        return
    
    # Create counter client
    counter_client = AlgorandCounterClient(algod_client)
    
    # Check account balance
    account_info = counter_client.get_account_info()
    if not account_info or account_info['amount'] < 1_000_000:  # Less than 1 ALGO
        print("\nYour account needs ALGO for transactions!")
        print("Get free TestNet ALGO: https://testnet.algoexplorer.io/dispenser")
        print(f"   Send to: {counter_client.address}")
        return
    
    # Load TEAL code (you need to run simple_counter.py first)
    try:
        with open('counter_approval.teal', 'r') as f:
            approval_teal = f.read()
        with open('counter_clear.teal', 'r') as f:
            clear_teal = f.read()
    except FileNotFoundError:
        print("TEAL files not found. Run 'python simple_counter.py' first.")
        return
    
    # Create application
    app_id = counter_client.create_app(approval_teal, clear_teal)
    if not app_id:
        return
    
    # Read initial state
    print("\nInitial State:")
    counter_client.read_global_state()
    
    # Demonstrate counter operations
    print("\nTesting Counter Operations:")
    
    # Increment counter 3 times
    for i in range(3):
        print(f"\nIncrement #{i+1}")
        counter_client.increment_counter()
        time.sleep(1)  # Brief pause
    
    # Read state after increments
    print("\nState after increments:")
    state = counter_client.read_global_state()
    
    # Decrement counter once
    print(f"\nDecrement counter")
    counter_client.decrement_counter()
    
    # Read final state
    print("\nFinal State:")
    final_state = counter_client.read_global_state()
    
    # Display summary
    print(f"\nDemo Summary:")
    print(f"   Counter value: {final_state.get('counter', 'N/A')}")
    print(f"   Total increments: {final_state.get('total_increments', 'N/A')}")
    print(f"   Total decrements: {final_state.get('total_decrements', 'N/A')}")
    print(f"   Application ID: {app_id}")
    
    print(f"\nView on AlgoExplorer:")
    print(f"   App: https://testnet.algoexplorer.io/application/{app_id}")
    print(f"   Account: https://testnet.algoexplorer.io/address/{counter_client.address}")


def fund_account_helper():
    """Helper function to display funding instructions"""
    print("Account Funding Helper")
    print("=" * 30)
    
    # Generate a test account
    private_key, address = account.generate_account()
    mnemonic_phrase = mnemonic.from_private_key(private_key)
    
    print(f"Test Account: {address}")
    print(f"Mnemonic: {mnemonic_phrase}")
    print("\nSteps to fund your account:")
    print("1. Visit: https://testnet.algoexplorer.io/dispenser")
    print(f"2. Enter address: {address}")
    print("3. Click 'Dispense' to get free TestNet ALGO")
    print("4. Wait for confirmation")
    print("5. Run the demo with your funded account")
    
    print("\nIMPORTANT:")
    print("   - Save the mnemonic phrase safely")
    print("   - This is TestNet ALGO (no real value)")
    print("   - Never share private keys for MainNet accounts")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "fund":
        fund_account_helper()
    else:
        demo_counter_app()