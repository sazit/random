// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title SimpleToken
 * @dev A basic ERC-20 token implementation for learning purposes
 * This contract demonstrates core blockchain concepts:
 * - State management on blockchain
 * - Event emission for transparency
 * - Access control with ownership
 * - Gas-efficient operations
 */
contract SimpleToken {
    // State variables stored on blockchain
    string public name = "LearnToken";
    string public symbol = "LEARN";
    uint8 public decimals = 18;
    uint256 public totalSupply;
    address public owner;
    
    // Mapping: address -> balance (like a distributed database)
    mapping(address => uint256) public balanceOf;
    mapping(address => mapping(address => uint256)) public allowance;
    
    // Events for blockchain transparency (logged permanently)
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Approval(address indexed owner, address indexed spender, uint256 value);
    event Mint(address indexed to, uint256 value);
    
    // Modifier for access control
    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner can call this function");
        _;
    }
    
    /**
     * @dev Constructor runs once when contract is deployed
     * @param _initialSupply Initial token supply
     */
    constructor(uint256 _initialSupply) {
        owner = msg.sender;  // msg.sender = wallet deploying the contract
        totalSupply = _initialSupply * 10**decimals;
        balanceOf[owner] = totalSupply;
        emit Transfer(address(0), owner, totalSupply);
    }
    
    /**
     * @dev Transfer tokens between addresses
     * @param _to Recipient address
     * @param _value Amount to transfer
     */
    function transfer(address _to, uint256 _value) public returns (bool success) {
        require(_to != address(0), "Cannot transfer to zero address");
        require(balanceOf[msg.sender] >= _value, "Insufficient balance");
        
        // Update balances (atomic operation)
        balanceOf[msg.sender] -= _value;
        balanceOf[_to] += _value;
        
        emit Transfer(msg.sender, _to, _value);
        return true;
    }
    
    /**
     * @dev Approve someone to spend your tokens
     * @param _spender Address to approve
     * @param _value Amount to approve
     */
    function approve(address _spender, uint256 _value) public returns (bool success) {
        allowance[msg.sender][_spender] = _value;
        emit Approval(msg.sender, _spender, _value);
        return true;
    }
    
    /**
     * @dev Transfer tokens from one address to another (requires approval)
     * @param _from Source address
     * @param _to Destination address
     * @param _value Amount to transfer
     */
    function transferFrom(address _from, address _to, uint256 _value) 
        public returns (bool success) {
        require(_to != address(0), "Cannot transfer to zero address");
        require(balanceOf[_from] >= _value, "Insufficient balance");
        require(allowance[_from][msg.sender] >= _value, "Insufficient allowance");
        
        // Update balances and allowances
        balanceOf[_from] -= _value;
        balanceOf[_to] += _value;
        allowance[_from][msg.sender] -= _value;
        
        emit Transfer(_from, _to, _value);
        return true;
    }
    
    /**
     * @dev Mint new tokens (only owner)
     * @param _to Address to mint tokens to
     * @param _value Amount to mint
     */
    function mint(address _to, uint256 _value) public onlyOwner returns (bool success) {
        require(_to != address(0), "Cannot mint to zero address");
        
        totalSupply += _value;
        balanceOf[_to] += _value;
        
        emit Mint(_to, _value);
        emit Transfer(address(0), _to, _value);
        return true;
    }
    
    /**
     * @dev Get token balance of an address
     * @param _owner Address to check
     */
    function getBalance(address _owner) public view returns (uint256) {
        return balanceOf[_owner];
    }
}
