// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721Enumerable.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/Counters.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Strings.sol";

/**
 * @title LearnNFT
 * @dev A comprehensive NFT contract demonstrating key blockchain concepts:
 * - ERC-721 standard implementation
 * - Metadata and token URI management
 * - Access control and ownership
 * - Minting mechanics and supply limits
 * - Royalty system for creators
 * - Gas-efficient operations
 * - Security best practices
 * 
 * Perfect for learning NFT development on Polygon/Ethereum
 */
contract LearnNFT is ERC721, ERC721URIStorage, ERC721Enumerable, Ownable, ReentrancyGuard {
    using Counters for Counters.Counter;
    using Strings for uint256;

    // State variables
    Counters.Counter private _tokenIdCounter;
    
    // Collection settings
    uint256 public constant MAX_SUPPLY = 10000;
    uint256 public constant MAX_PER_WALLET = 10;
    uint256 public mintPrice = 0.001 ether;  // Very low for Polygon
    bool public publicMintEnabled = false;
    bool public whitelistMintEnabled = true;
    
    // Metadata
    string private _baseTokenURI;
    string private _contractURI;
    
    // Whitelist for early access
    mapping(address => bool) public whitelist;
    mapping(address => uint256) public walletMintCount;
    
    // Royalty info (EIP-2981)
    address public royaltyReceiver;
    uint256 public royaltyPercentage = 750; // 7.5% in basis points (7.5% = 750/10000)
    
    // Events for transparency and indexing
    event NFTMinted(address indexed to, uint256 indexed tokenId, string tokenURI);
    event WhitelistUpdated(address indexed user, bool status);
    event MintPriceUpdated(uint256 newPrice);
    event BaseURIUpdated(string newBaseURI);
    event RoyaltyUpdated(address receiver, uint256 percentage);
    event WithdrawalCompleted(address to, uint256 amount);

    /**
     * @dev Constructor sets up the NFT collection
     * @param _name Collection name
     * @param _symbol Collection symbol  
     * @param _initialBaseURI Base URI for metadata
     */
    constructor(
        string memory _name,
        string memory _symbol,
        string memory _initialBaseURI
    ) ERC721(_name, _symbol) {
        _baseTokenURI = _initialBaseURI;
        royaltyReceiver = msg.sender;
        
        // Mint token #0 to deployer as genesis NFT
        _safeMint(msg.sender, 0);
        _setTokenURI(0, "genesis.json");
        walletMintCount[msg.sender] = 1;
        
        emit NFTMinted(msg.sender, 0, "genesis.json");
    }

    /**
     * @dev Mint NFTs to specified address (only owner)
     * @param to Address to mint NFTs to
     * @param quantity Number of NFTs to mint
     * @param tokenURIs Array of token URIs for metadata
     */
    function ownerMint(
        address to, 
        uint256 quantity, 
        string[] memory tokenURIs
    ) external onlyOwner {
        require(quantity > 0, "Quantity must be positive");
        require(quantity == tokenURIs.length, "Quantity and URI count mismatch");
        require(_tokenIdCounter.current() + quantity <= MAX_SUPPLY, "Would exceed max supply");
        require(walletMintCount[to] + quantity <= MAX_PER_WALLET, "Would exceed wallet limit");
        
        for (uint256 i = 0; i < quantity; i++) {
            _tokenIdCounter.increment();
            uint256 tokenId = _tokenIdCounter.current();
            
            _safeMint(to, tokenId);
            _setTokenURI(tokenId, tokenURIs[i]);
            
            emit NFTMinted(to, tokenId, tokenURIs[i]);
        }
        
        walletMintCount[to] += quantity;
    }

    /**
     * @dev Public mint function (when enabled)
     * @param quantity Number of NFTs to mint
     */
    function publicMint(uint256 quantity) external payable nonReentrant {
        require(publicMintEnabled, "Public mint not enabled");
        require(quantity > 0 && quantity <= 5, "Invalid quantity (1-5)");
        require(_tokenIdCounter.current() + quantity <= MAX_SUPPLY, "Would exceed max supply");
        require(walletMintCount[msg.sender] + quantity <= MAX_PER_WALLET, "Would exceed wallet limit");
        require(msg.value >= mintPrice * quantity, "Insufficient payment");
        
        for (uint256 i = 0; i < quantity; i++) {
            _tokenIdCounter.increment();
            uint256 tokenId = _tokenIdCounter.current();
            
            _safeMint(msg.sender, tokenId);
            
            // Generate default metadata URI
            string memory tokenURI = string(abi.encodePacked(tokenId.toString(), ".json"));
            _setTokenURI(tokenId, tokenURI);
            
            emit NFTMinted(msg.sender, tokenId, tokenURI);
        }
        
        walletMintCount[msg.sender] += quantity;
        
        // Refund excess payment
        if (msg.value > mintPrice * quantity) {
            payable(msg.sender).transfer(msg.value - (mintPrice * quantity));
        }
    }

    /**
     * @dev Whitelist mint function (early access)
     * @param quantity Number of NFTs to mint
     */
    function whitelistMint(uint256 quantity) external payable nonReentrant {
        require(whitelistMintEnabled, "Whitelist mint not enabled");
        require(whitelist[msg.sender], "Not on whitelist");
        require(quantity > 0 && quantity <= 3, "Invalid quantity (1-3)");
        require(_tokenIdCounter.current() + quantity <= MAX_SUPPLY, "Would exceed max supply");
        require(walletMintCount[msg.sender] + quantity <= MAX_PER_WALLET, "Would exceed wallet limit");
        
        // 50% discount for whitelist
        uint256 discountedPrice = (mintPrice * 50) / 100;
        require(msg.value >= discountedPrice * quantity, "Insufficient payment");
        
        for (uint256 i = 0; i < quantity; i++) {
            _tokenIdCounter.increment();
            uint256 tokenId = _tokenIdCounter.current();
            
            _safeMint(msg.sender, tokenId);
            
            string memory tokenURI = string(abi.encodePacked("wl_", tokenId.toString(), ".json"));
            _setTokenURI(tokenId, tokenURI);
            
            emit NFTMinted(msg.sender, tokenId, tokenURI);
        }
        
        walletMintCount[msg.sender] += quantity;
        
        // Refund excess payment
        if (msg.value > discountedPrice * quantity) {
            payable(msg.sender).transfer(msg.value - (discountedPrice * quantity));
        }
    }

    /**
     * @dev Add/remove addresses from whitelist
     * @param addresses Array of addresses to update
     * @param status True to add, false to remove
     */
    function updateWhitelist(address[] calldata addresses, bool status) external onlyOwner {
        for (uint256 i = 0; i < addresses.length; i++) {
            whitelist[addresses[i]] = status;
            emit WhitelistUpdated(addresses[i], status);
        }
    }

    /**
     * @dev Toggle public mint status
     */
    function togglePublicMint() external onlyOwner {
        publicMintEnabled = !publicMintEnabled;
    }

    /**
     * @dev Toggle whitelist mint status
     */
    function toggleWhitelistMint() external onlyOwner {
        whitelistMintEnabled = !whitelistMintEnabled;
    }

    /**
     * @dev Update mint price
     * @param newPrice New price in wei
     */
    function setMintPrice(uint256 newPrice) external onlyOwner {
        mintPrice = newPrice;
        emit MintPriceUpdated(newPrice);
    }

    /**
     * @dev Update base URI for metadata
     * @param newBaseURI New base URI
     */
    function setBaseURI(string memory newBaseURI) external onlyOwner {
        _baseTokenURI = newBaseURI;
        emit BaseURIUpdated(newBaseURI);
    }

    /**
     * @dev Update contract metadata URI
     * @param newContractURI New contract URI
     */
    function setContractURI(string memory newContractURI) external onlyOwner {
        _contractURI = newContractURI;
    }

    /**
     * @dev Update royalty information
     * @param receiver Address to receive royalties
     * @param percentage Royalty percentage in basis points (e.g., 750 = 7.5%)
     */
    function setRoyaltyInfo(address receiver, uint256 percentage) external onlyOwner {
        require(percentage <= 1000, "Royalty too high (max 10%)");
        royaltyReceiver = receiver;
        royaltyPercentage = percentage;
        emit RoyaltyUpdated(receiver, percentage);
    }

    /**
     * @dev Withdraw contract funds
     * @param to Address to send funds to
     */
    function withdraw(address payable to) external onlyOwner nonReentrant {
        require(to != address(0), "Cannot withdraw to zero address");
        uint256 balance = address(this).balance;
        require(balance > 0, "No funds to withdraw");
        
        (bool success, ) = to.call{value: balance}("");
        require(success, "Withdrawal failed");
        
        emit WithdrawalCompleted(to, balance);
    }

    // View functions
    
    /**
     * @dev Get total number of tokens minted
     */
    function totalMinted() external view returns (uint256) {
        return _tokenIdCounter.current();
    }

    /**
     * @dev Get remaining supply
     */
    function remainingSupply() external view returns (uint256) {
        return MAX_SUPPLY - _tokenIdCounter.current();
    }

    /**
     * @dev Get tokens owned by an address
     * @param owner Address to query
     */
    function tokensOfOwner(address owner) external view returns (uint256[] memory) {
        uint256 tokenCount = balanceOf(owner);
        uint256[] memory tokenIds = new uint256[](tokenCount);
        
        for (uint256 i = 0; i < tokenCount; i++) {
            tokenIds[i] = tokenOfOwnerByIndex(owner, i);
        }
        
        return tokenIds;
    }

    /**
     * @dev Check if address is whitelisted
     * @param user Address to check
     */
    function isWhitelisted(address user) external view returns (bool) {
        return whitelist[user];
    }

    /**
     * @dev Get contract metadata URI (OpenSea standard)
     */
    function contractURI() external view returns (string memory) {
        return _contractURI;
    }

    /**
     * @dev Calculate royalty amount (EIP-2981)
     * @param tokenId Token ID (not used in this implementation)
     * @param salePrice Sale price to calculate royalty on
     */
    function royaltyInfo(uint256 tokenId, uint256 salePrice) 
        external view returns (address receiver, uint256 royaltyAmount) {
        receiver = royaltyReceiver;
        royaltyAmount = (salePrice * royaltyPercentage) / 10000;
    }

    // Internal functions

    /**
     * @dev Base URI for token metadata
     */
    function _baseURI() internal view override returns (string memory) {
        return _baseTokenURI;
    }

    /**
     * @dev Hook called before any token transfer
     */
    function _beforeTokenTransfer(
        address from,
        address to,
        uint256 tokenId
    ) internal override(ERC721, ERC721Enumerable) {
        super._beforeTokenTransfer(from, to, tokenId);
    }

    /**
     * @dev Burn a token
     */
    function _burn(uint256 tokenId) internal override(ERC721, ERC721URIStorage) {
        super._burn(tokenId);
    }

    /**
     * @dev Get token URI with fallback to base URI
     */
    function tokenURI(uint256 tokenId)
        public view override(ERC721, ERC721URIStorage) returns (string memory) {
        return super.tokenURI(tokenId);
    }

    /**
     * @dev Interface support check
     */
    function supportsInterface(bytes4 interfaceId)
        public view override(ERC721, ERC721Enumerable) returns (bool) {
        return interfaceId == 0x2a55205a || // EIP-2981 royalty standard
               super.supportsInterface(interfaceId);
    }
}
