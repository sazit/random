const hre = require("hardhat");
const { ethers } = require("hardhat");

async function main() {
  console.log("Deploying SimpleToken contract...");
  
  // Get the contract factory
  const SimpleToken = await ethers.getContractFactory("SimpleToken");
  
  // Deploy with initial supply of 1,000,000 tokens
  const initialSupply = 1000000;
  console.log(`Initial supply: ${initialSupply.toLocaleString()} tokens`);
  
  const simpleToken = await SimpleToken.deploy(initialSupply);
  
  // Wait for deployment to complete
  await simpleToken.waitForDeployment();
  
  const contractAddress = await simpleToken.getAddress();
  console.log(`SimpleToken deployed to: ${contractAddress}`);
  
  // Display deployment info
  const [deployer] = await ethers.getSigners();
  console.log(`Deployed by: ${deployer.address}`);
  
  // Get deployer balance after deployment
  const balance = await ethers.provider.getBalance(deployer.address);
  console.log(`Deployer ETH balance: ${ethers.formatEther(balance)} ETH`);
  
  // Verify contract details
  const name = await simpleToken.name();
  const symbol = await simpleToken.symbol();
  const totalSupply = await simpleToken.totalSupply();
  const decimals = await simpleToken.decimals();
  
  console.log("\nContract Details:");
  console.log(`   Name: ${name}`);
  console.log(`   Symbol: ${symbol}`);
  console.log(`   Decimals: ${decimals}`);
  console.log(`   Total Supply: ${ethers.formatUnits(totalSupply, decimals)} ${symbol}`);
  
  // Save deployment info
  const deploymentInfo = {
    contractAddress: contractAddress,
    deployerAddress: deployer.address,
    network: hre.network.name,
    timestamp: new Date().toISOString(),
    contractName: "SimpleToken",
    initialSupply: initialSupply
  };
  
  console.log("\nSave this info for interacting with your contract:");
  console.log(JSON.stringify(deploymentInfo, null, 2));
  
  // Example interaction
  console.log("\nTesting basic functionality...");
  const deployerTokenBalance = await simpleToken.balanceOf(deployer.address);
  console.log(`   Deployer token balance: ${ethers.formatUnits(deployerTokenBalance, decimals)} ${symbol}`);
  
  if (hre.network.name === "localhost") {
    console.log("\nNext steps:");
    console.log("   1. Interact with your contract using the address above");
    console.log("   2. Try transferring tokens to another address");
    console.log("   3. Test minting new tokens");
    console.log("   4. Run the test suite: npm run test");
  }
}

// Error handling
main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("Deployment failed:", error);
    process.exit(1);
  });
