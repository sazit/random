const hre = require("hardhat");
const { ethers } = require("hardhat");

// Replace with your deployed contract address
const CONTRACT_ADDRESS = "0x742d35Cc69b8e8e7e4f9A1C2b2Dd42fb8f2b87c"; // UPDATE THIS!

async function main() {
  console.log("NFT Minting Script");
  console.log("Network:", hre.network.name);
  
  // Get signer
  const [signer] = await ethers.getSigners();
  console.log("Minting with account:", signer.address);
  
  // Connect to deployed contract
  const LearnNFT = await ethers.getContractFactory("LearnNFT");
  const contract = LearnNFT.attach(CONTRACT_ADDRESS);
  
  // Check contract connection
  try {
    const name = await contract.name();
    console.log("Contract name:", name);
  } catch (error) {
    console.error("Failed to connect to contract. Check CONTRACT_ADDRESS!");
    process.exit(1);
  }
  
  // Get contract info
  const totalMinted = await contract.totalMinted();
  const maxSupply = await contract.MAX_SUPPLY();
  const mintPrice = await contract.mintPrice();
  const isPublicMintEnabled = await contract.publicMintEnabled();
  const isWhitelistMintEnabled = await contract.whitelistMintEnabled();
  const isWhitelisted = await contract.isWhitelisted(signer.address);
  const walletMintCount = await contract.walletMintCount(signer.address);
  
  console.log("\nContract Status:");
  console.log("   Total Minted:", totalMinted.toString(), "/", maxSupply.toString());
  console.log("   Mint Price:", ethers.formatEther(mintPrice), "ETH/MATIC");
  console.log("   Public Mint:", isPublicMintEnabled ? "Enabled" : "Disabled");
  console.log("   Whitelist Mint:", isWhitelistMintEnabled ? "Enabled" : "Disabled");
  console.log("   Your Whitelist Status:", isWhitelisted ? "Whitelisted" : "Not whitelisted");
  console.log("   Your NFTs Minted:", walletMintCount.toString());
  
  // Check balance
  const balance = await ethers.provider.getBalance(signer.address);
  console.log("   Your Balance:", ethers.formatEther(balance), "ETH/MATIC");
  
  // Determine minting strategy
  let mintFunction;
  let mintQuantity = 2; // Number of NFTs to mint
  let mintCost;
  
  if (isWhitelistMintEnabled && isWhitelisted) {
    console.log("\nUsing whitelist mint (50% discount!)");
    mintFunction = "whitelistMint";
    mintCost = (mintPrice * BigInt(mintQuantity) * BigInt(50)) / BigInt(100); // 50% discount
    mintQuantity = Math.min(mintQuantity, 3); // Max 3 for whitelist
  } else if (isPublicMintEnabled) {
    console.log("\nUsing public mint");
    mintFunction = "publicMint";
    mintCost = mintPrice * BigInt(mintQuantity);
    mintQuantity = Math.min(mintQuantity, 5); // Max 5 for public
  } else {
    console.log("No minting options available. Enable public mint or add to whitelist.");
    process.exit(1);
  }
  
  console.log("   Quantity:", mintQuantity);
  console.log("   Total Cost:", ethers.formatEther(mintCost), "ETH/MATIC");
  
  // Check if user has enough balance
  if (balance < mintCost) {
    console.log("Insufficient balance for minting!");
    console.log("   Required:", ethers.formatEther(mintCost), "ETH/MATIC");
    console.log("   Available:", ethers.formatEther(balance), "ETH/MATIC");
    
    if (hre.network.name === "mumbai") {
      console.log("Get free MATIC: https://faucet.polygon.technology/");
    }
    process.exit(1);
  }
  
  // Mint NFTs
  console.log("\nMinting NFTs...");
  
  try {
    const tx = await contract[mintFunction](mintQuantity, { value: mintCost });
    console.log("Transaction submitted:", tx.hash);
    
    console.log("Waiting for confirmation...");
    const receipt = await tx.wait();
    
    console.log("Minting successful!");
    console.log("Transaction confirmed in block:", receipt.blockNumber);
    console.log("Gas used:", receipt.gasUsed.toString());
    
    // Parse minting events
    const mintEvents = receipt.logs.filter(log => {
      try {
        const parsed = contract.interface.parseLog(log);
        return parsed.name === "NFTMinted";
      } catch {
        return false;
      }
    });
    
    console.log("\nMinted NFTs:");
    mintEvents.forEach((log, index) => {
      const parsed = contract.interface.parseLog(log);
      console.log(`   NFT #${parsed.args.tokenId}: ${parsed.args.tokenURI}`);
    });
    
    // Network-specific links
    if (hre.network.name === "mumbai") {
      console.log(`\nView transaction: https://mumbai.polygonscan.com/tx/${tx.hash}`);
      console.log(`View on OpenSea: https://testnets.opensea.io/assets/mumbai/${CONTRACT_ADDRESS}`);
    } else if (hre.network.name === "polygon") {
      console.log(`\nView transaction: https://polygonscan.com/tx/${tx.hash}`);
      console.log(`View on OpenSea: https://opensea.io/assets/matic/${CONTRACT_ADDRESS}`);
    }
    
    // Updated stats
    const newTotalMinted = await contract.totalMinted();
    const newWalletCount = await contract.walletMintCount(signer.address);
    const userBalance = await contract.balanceOf(signer.address);
    
    console.log("\nUpdated Stats:");
    console.log("   Total Minted:", newTotalMinted.toString(), "/", maxSupply.toString());
    console.log("   Your NFTs Minted:", newWalletCount.toString());
    console.log("   Your NFT Balance:", userBalance.toString());
    
    // Get token IDs owned by user
    console.log("\nYour NFT Collection:");
    const tokenIds = await contract.tokensOfOwner(signer.address);
    tokenIds.forEach((tokenId, index) => {
      console.log(`   Token #${tokenId.toString()}`);
    });
    
  } catch (error) {
    console.error("Minting failed:", error.message);
    
    // Common error handling
    if (error.message.includes("Would exceed max supply")) {
      console.log("The collection is sold out!");
    } else if (error.message.includes("Would exceed wallet limit")) {
      console.log("You've reached the maximum NFTs per wallet.");
    } else if (error.message.includes("Insufficient payment")) {
      console.log("You didn't send enough ETH/MATIC for the mint price.");
    } else if (error.message.includes("Not on whitelist")) {
      console.log("You need to be whitelisted for this mint phase.");
    }
    
    process.exit(1);
  }
}

// Owner-only functions (uncomment if you're the contract owner)
async function ownerMint() {
  console.log("Owner Mint Function");
  
  const [owner] = await ethers.getSigners();
  const LearnNFT = await ethers.getContractFactory("LearnNFT");
  const contract = LearnNFT.attach(CONTRACT_ADDRESS);
  
  // Mint directly to specific addresses
  const recipients = [
    "0x742d35Cc69b8e8e7e4f9A1C2b2Dd42fb8f2b87c", // Replace with actual addresses
    "0x123...", // Team member 1
    "0x456...", // Team member 2
  ];
  
  const tokenURIs = [
    "special_1.json",
    "special_2.json", 
    "special_3.json"
  ];
  
  for (let i = 0; i < recipients.length; i++) {
    try {
      const tx = await contract.ownerMint(recipients[i], 1, [tokenURIs[i]]);
      await tx.wait();
      console.log(`Minted special NFT to ${recipients[i]}`);
    } catch (error) {
      console.error(`Failed to mint to ${recipients[i]}:`, error.message);
    }
  }
}

// Whitelist management (owner only)
async function manageWhitelist() {
  console.log("Whitelist Management");
  
  const LearnNFT = await ethers.getContractFactory("LearnNFT");
  const contract = LearnNFT.attach(CONTRACT_ADDRESS);
  
  // Add addresses to whitelist
  const whitelistAddresses = [
    "0x742d35Cc69b8e8e7e4f9A1C2b2Dd42fb8f2b87c", // Replace with actual addresses
    "0x123...",
    "0x456...",
  ];
  
  try {
    const tx = await contract.updateWhitelist(whitelistAddresses, true);
    await tx.wait();
    console.log("Added addresses to whitelist");
  } catch (error) {
    console.error("Failed to update whitelist:", error.message);
  }
}

// Main execution
if (require.main === module) {
  // Change this to run different functions
  main()
    .then(() => process.exit(0))
    .catch((error) => {
      console.error(error);
      process.exit(1);
    });
}
