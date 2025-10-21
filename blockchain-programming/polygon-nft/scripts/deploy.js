const hre = require("hardhat");
const { ethers } = require("hardhat");

async function main() {
  console.log("Deploying LearnNFT to", hre.network.name);
  
  // Get deployer account
  const [deployer] = await ethers.getSigners();
  console.log("Deploying with account:", deployer.address);
  
  // Check balance
  const balance = await ethers.provider.getBalance(deployer.address);
  console.log("Account balance:", ethers.formatEther(balance), "ETH/MATIC");
  
  if (balance < ethers.parseEther("0.01")) {
    console.log("Low balance! You might need more funds for deployment.");
    if (hre.network.name === "mumbai") {
      console.log("Get free MATIC: https://faucet.polygon.technology/");
    }
  }
  
  // Contract parameters
  const contractName = "LearnNFT Collection";
  const contractSymbol = "LEARN";
  const baseURI = "https://api.learnnft.dev/metadata/"; // Replace with your metadata API
  
  console.log("\nContract Configuration:");
  console.log("   Name:", contractName);
  console.log("   Symbol:", contractSymbol);
  console.log("   Base URI:", baseURI);
  
  // Deploy contract
  console.log("\nDeploying contract...");
  
  const LearnNFT = await ethers.getContractFactory("LearnNFT");
  const learnNFT = await LearnNFT.deploy(contractName, contractSymbol, baseURI);
  
  // Wait for deployment
  await learnNFT.waitForDeployment();
  const contractAddress = await learnNFT.getAddress();
  
  console.log("LearnNFT deployed to:", contractAddress);
  
  // Get deployment transaction
  const deployTxHash = learnNFT.deploymentTransaction().hash;
  console.log("Deployment transaction:", deployTxHash);
  
  // Verify contract details
  const name = await learnNFT.name();
  const symbol = await learnNFT.symbol();
  const maxSupply = await learnNFT.MAX_SUPPLY();
  const mintPrice = await learnNFT.mintPrice();
  const totalMinted = await learnNFT.totalMinted();
  
  console.log("\nContract Details:");
  console.log("   Name:", name);
  console.log("   Symbol:", symbol);
  console.log("   Max Supply:", maxSupply.toString());
  console.log("   Mint Price:", ethers.formatEther(mintPrice), "ETH/MATIC");
  console.log("   Total Minted:", totalMinted.toString());
  console.log("   Owner:", await learnNFT.owner());
  
  // Network-specific information
  if (hre.network.name === "mumbai") {
    console.log("\nMumbai Testnet Links:");
    console.log(`   Contract: https://mumbai.polygonscan.com/address/${contractAddress}`);
    console.log(`   Transaction: https://mumbai.polygonscan.com/tx/${deployTxHash}`);
    console.log(`   OpenSea: https://testnets.opensea.io/assets/mumbai/${contractAddress}`);
  } else if (hre.network.name === "polygon") {
    console.log("\nPolygon Mainnet Links:");
    console.log(`   Contract: https://polygonscan.com/address/${contractAddress}`);
    console.log(`   Transaction: https://polygonscan.com/tx/${deployTxHash}`);
    console.log(`   OpenSea: https://opensea.io/assets/matic/${contractAddress}`);
  }
  
  // Save deployment info
  const deploymentInfo = {
    network: hre.network.name,
    contractAddress: contractAddress,
    contractName: contractName,
    contractSymbol: contractSymbol,
    baseURI: baseURI,
    deployerAddress: deployer.address,
    deploymentTransaction: deployTxHash,
    timestamp: new Date().toISOString(),
    maxSupply: maxSupply.toString(),
    mintPrice: ethers.formatEther(mintPrice)
  };
  
  console.log("\nDeployment Info (save this!):");
  console.log(JSON.stringify(deploymentInfo, null, 2));
  
  // Wait for block confirmations before verification
  if (hre.network.name !== "localhost") {
    console.log("\nWaiting for block confirmations...");
    await learnNFT.deploymentTransaction().wait(6);
    
    // Auto-verify on supported networks
    if (process.env.POLYGONSCAN_API_KEY) {
      console.log("\nVerifying contract on PolygonScan...");
      try {
        await hre.run("verify:verify", {
          address: contractAddress,
          constructorArguments: [contractName, contractSymbol, baseURI],
        });
        console.log("Contract verified successfully!");
      } catch (error) {
        console.log("Verification failed:", error.message);
        console.log("You can verify manually with:");
        console.log(`   npx hardhat verify --network ${hre.network.name} ${contractAddress} "${contractName}" "${contractSymbol}" "${baseURI}"`);
      }
    }
  }
  
  // Next steps
  console.log("\nNext Steps:");
  console.log("   1. Add your contract address to mint scripts");
  console.log("   2. Upload metadata to IPFS or your server");
  console.log("   3. Update base URI with your metadata endpoint");
  console.log("   4. Add addresses to whitelist");
  console.log("   5. Enable public minting when ready");
  
  if (hre.network.name === "localhost") {
    console.log("\nFor local testing:");
    console.log("   - Run: npm run test");
    console.log("   - Use scripts/mint.js to test minting");
  }
  
  // Sample interaction
  console.log("\nTesting basic functionality...");
  const isWhitelisted = await learnNFT.isWhitelisted(deployer.address);
  const balance = await learnNFT.balanceOf(deployer.address);
  console.log(`   Deployer whitelisted: ${isWhitelisted}`);
  console.log(`   Deployer NFT balance: ${balance.toString()}`);
  
  console.log("\nDeployment completed successfully!");
}

// Error handling
main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("Deployment failed:", error);
    process.exit(1);
  });
