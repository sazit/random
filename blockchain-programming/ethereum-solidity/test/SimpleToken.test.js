const { expect } = require("chai");
const { ethers } = require("hardhat");

/**
 * SimpleToken Contract Tests
 * This demonstrates proper smart contract testing practices:
 * - Unit testing individual functions
 * - Edge case testing
 * - Gas optimization verification
 * - Security vulnerability checks
 */
describe("SimpleToken Contract", function () {
  let simpleToken;
  let owner;
  let addr1;
  let addr2;
  
  const INITIAL_SUPPLY = 1000000;
  const DECIMALS = 18;
  
  // Deploy fresh contract before each test
  beforeEach(async function () {
    [owner, addr1, addr2] = await ethers.getSigners();
    
    const SimpleToken = await ethers.getContractFactory("SimpleToken");
    simpleToken = await SimpleToken.deploy(INITIAL_SUPPLY);
    await simpleToken.waitForDeployment();
  });
  
  describe("Contract Deployment", function () {
    it("Should set the correct name and symbol", async function () {
      expect(await simpleToken.name()).to.equal("LearnToken");
      expect(await simpleToken.symbol()).to.equal("LEARN");
      expect(await simpleToken.decimals()).to.equal(DECIMALS);
    });
    
    it("Should assign total supply to owner", async function () {
      const ownerBalance = await simpleToken.balanceOf(owner.address);
      const totalSupply = await simpleToken.totalSupply();
      expect(ownerBalance).to.equal(totalSupply);
    });
    
    it("Should set the correct owner", async function () {
      expect(await simpleToken.owner()).to.equal(owner.address);
    });
  });
  
  describe("Token Transfers", function () {
    it("Should transfer tokens between accounts", async function () {
      const transferAmount = ethers.parseUnits("100", DECIMALS);
      
      // Transfer from owner to addr1
      await simpleToken.transfer(addr1.address, transferAmount);
      
      const addr1Balance = await simpleToken.balanceOf(addr1.address);
      expect(addr1Balance).to.equal(transferAmount);
      
      // Check owner balance decreased
      const ownerBalance = await simpleToken.balanceOf(owner.address);
      const expectedOwnerBalance = ethers.parseUnits((INITIAL_SUPPLY - 100).toString(), DECIMALS);
      expect(ownerBalance).to.equal(expectedOwnerBalance);
    });
    
    it("Should fail if sender doesn't have enough tokens", async function () {
      const initialOwnerBalance = await simpleToken.balanceOf(owner.address);
      const transferAmount = initialOwnerBalance + 1n;
      
      await expect(
        simpleToken.transfer(addr1.address, transferAmount)
      ).to.be.revertedWith("Insufficient balance");
    });
    
    it("Should emit Transfer event", async function () {
      const transferAmount = ethers.parseUnits("50", DECIMALS);
      
      await expect(simpleToken.transfer(addr1.address, transferAmount))
        .to.emit(simpleToken, "Transfer")
        .withArgs(owner.address, addr1.address, transferAmount);
    });
  });
  
  describe("Token Approvals & TransferFrom", function () {
    it("Should approve and transfer tokens", async function () {
      const approveAmount = ethers.parseUnits("100", DECIMALS);
      const transferAmount = ethers.parseUnits("50", DECIMALS);
      
      // Owner approves addr1 to spend tokens
      await simpleToken.approve(addr1.address, approveAmount);
      
      // Check allowance
      const allowance = await simpleToken.allowance(owner.address, addr1.address);
      expect(allowance).to.equal(approveAmount);
      
      // addr1 transfers from owner to addr2
      await simpleToken.connect(addr1).transferFrom(owner.address, addr2.address, transferAmount);
      
      // Check balances
      const addr2Balance = await simpleToken.balanceOf(addr2.address);
      expect(addr2Balance).to.equal(transferAmount);
      
      // Check remaining allowance
      const remainingAllowance = await simpleToken.allowance(owner.address, addr1.address);
      expect(remainingAllowance).to.equal(approveAmount - transferAmount);
    });
    
    it("Should fail transferFrom without sufficient allowance", async function () {
      const transferAmount = ethers.parseUnits("100", DECIMALS);
      
      await expect(
        simpleToken.connect(addr1).transferFrom(owner.address, addr2.address, transferAmount)
      ).to.be.revertedWith("Insufficient allowance");
    });
  });
  
  describe("Token Minting", function () {
    it("Should allow owner to mint tokens", async function () {
      const mintAmount = ethers.parseUnits("500", DECIMALS);
      const initialSupply = await simpleToken.totalSupply();
      
      await simpleToken.mint(addr1.address, mintAmount);
      
      // Check addr1 balance
      const addr1Balance = await simpleToken.balanceOf(addr1.address);
      expect(addr1Balance).to.equal(mintAmount);
      
      // Check total supply increased
      const newTotalSupply = await simpleToken.totalSupply();
      expect(newTotalSupply).to.equal(initialSupply + mintAmount);
    });
    
    it("Should fail if non-owner tries to mint", async function () {
      const mintAmount = ethers.parseUnits("100", DECIMALS);
      
      await expect(
        simpleToken.connect(addr1).mint(addr2.address, mintAmount)
      ).to.be.revertedWith("Only owner can call this function");
    });
    
    it("Should emit Mint and Transfer events", async function () {
      const mintAmount = ethers.parseUnits("200", DECIMALS);
      
      await expect(simpleToken.mint(addr1.address, mintAmount))
        .to.emit(simpleToken, "Mint")
        .withArgs(addr1.address, mintAmount)
        .and.to.emit(simpleToken, "Transfer")
        .withArgs(ethers.ZeroAddress, addr1.address, mintAmount);
    });
  });
  
  describe("Security Tests", function () {
    it("Should not allow transfer to zero address", async function () {
      const transferAmount = ethers.parseUnits("100", DECIMALS);
      
      await expect(
        simpleToken.transfer(ethers.ZeroAddress, transferAmount)
      ).to.be.revertedWith("Cannot transfer to zero address");
    });
    
    it("Should not allow minting to zero address", async function () {
      const mintAmount = ethers.parseUnits("100", DECIMALS);
      
      await expect(
        simpleToken.mint(ethers.ZeroAddress, mintAmount)
      ).to.be.revertedWith("Cannot mint to zero address");
    });
  });
  
  describe("Gas Optimization Tests", function () {
    it("Should use reasonable gas for transfers", async function () {
      const transferAmount = ethers.parseUnits("100", DECIMALS);
      
      const tx = await simpleToken.transfer(addr1.address, transferAmount);
      const receipt = await tx.wait();
      
      // Basic transfer should use less than 60k gas
      expect(receipt.gasUsed).to.be.lessThan(60000);
    });
  });
});
