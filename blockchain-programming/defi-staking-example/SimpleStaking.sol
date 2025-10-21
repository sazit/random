// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/security/Pausable.sol";
import "@openzeppelin/contracts/utils/math/SafeMath.sol";

/**
 * @title SimpleStaking
 * @dev A beginner-friendly DeFi staking contract demonstrating:
 * - Token staking mechanics
 * - Reward calculation and distribution
 * - Time-locked staking periods
 * - Emergency withdrawal mechanisms
 * - Yield farming basics
 * - Security best practices for DeFi
 */
contract SimpleStaking is Ownable, ReentrancyGuard, Pausable {
    using SafeMath for uint256;

    // The token being staked
    IERC20 public stakingToken;
    
    // Reward token (can be same as staking token)
    IERC20 public rewardToken;
    
    // Staking parameters
    uint256 public rewardRate = 100; // 100 tokens per second base rate
    uint256 public lockDuration = 7 days; // Minimum lock period
    uint256 public totalStaked;
    uint256 public totalRewardsDistributed;
    
    // Reward multipliers for different lock periods
    uint256 public constant WEEK_MULTIPLIER = 100;    // 1x (base)
    uint256 public constant MONTH_MULTIPLIER = 125;   // 1.25x
    uint256 public constant QUARTER_MULTIPLIER = 150; // 1.5x
    uint256 public constant YEAR_MULTIPLIER = 200;    // 2x

    struct StakeInfo {
        uint256 amount;           // Amount staked
        uint256 rewardDebt;       // Reward debt for calculations
        uint256 stakeTime;        // When stake was created
        uint256 lockPeriod;       // Lock period in seconds
        uint256 multiplier;       // Reward multiplier (100 = 1x)
        bool isActive;            // Whether stake is active
    }
    
    struct PoolInfo {
        uint256 accRewardPerShare; // Accumulated rewards per share
        uint256 lastRewardTime;    // Last time rewards were calculated
        uint256 totalStaked;       // Total amount staked in pool
    }
    
    // Mappings
    mapping(address => StakeInfo[]) public userStakes;
    mapping(address => uint256) public userTotalStaked;
    mapping(address => uint256) public userTotalRewards;
    
    // Pool information
    PoolInfo public poolInfo;
    
    // Events for transparency and frontend integration
    event Staked(
        address indexed user, 
        uint256 indexed stakeId, 
        uint256 amount, 
        uint256 lockPeriod,
        uint256 multiplier
    );
    event Unstaked(address indexed user, uint256 indexed stakeId, uint256 amount);
    event RewardsClaimed(address indexed user, uint256 amount);
    event EmergencyWithdraw(address indexed user, uint256 indexed stakeId, uint256 amount);
    event RewardRateUpdated(uint256 newRate);
    event LockDurationUpdated(uint256 newDuration);

    /**
     * @dev Constructor initializes the staking contract
     * @param _stakingToken Address of token to be staked
     * @param _rewardToken Address of reward token
     */
    constructor(
        address _stakingToken,
        address _rewardToken
    ) {
        require(_stakingToken != address(0), "Invalid staking token");
        require(_rewardToken != address(0), "Invalid reward token");
        
        stakingToken = IERC20(_stakingToken);
        rewardToken = IERC20(_rewardToken);
        
        // Initialize pool
        poolInfo.lastRewardTime = block.timestamp;
    }

    /**
     * @dev Stake tokens with specified lock period
     * @param _amount Amount to stake
     * @param _lockPeriod Lock period (1 = week, 2 = month, 3 = quarter, 4 = year)
     */
    function stake(uint256 _amount, uint8 _lockPeriod) 
        external 
        nonReentrant 
        whenNotPaused 
    {
        require(_amount > 0, "Cannot stake 0 tokens");
        require(_lockPeriod >= 1 && _lockPeriod <= 4, "Invalid lock period");
        
        // Update pool rewards before staking
        updatePool();
        
        // Transfer tokens from user
        stakingToken.transferFrom(msg.sender, address(this), _amount);
        
        // Calculate lock duration and multiplier
        (uint256 lockTime, uint256 multiplier) = getLockDetails(_lockPeriod);
        
        // Create stake record
        StakeInfo memory newStake = StakeInfo({
            amount: _amount,
            rewardDebt: _amount.mul(poolInfo.accRewardPerShare).div(1e12),
            stakeTime: block.timestamp,
            lockPeriod: lockTime,
            multiplier: multiplier,
            isActive: true
        });
        
        userStakes[msg.sender].push(newStake);
        userTotalStaked[msg.sender] = userTotalStaked[msg.sender].add(_amount);
        totalStaked = totalStaked.add(_amount);
        poolInfo.totalStaked = poolInfo.totalStaked.add(_amount);
        
        emit Staked(
            msg.sender, 
            userStakes[msg.sender].length - 1, 
            _amount, 
            lockTime,
            multiplier
        );
    }

    /**
     * @dev Unstake tokens after lock period expires
     * @param _stakeId Index of the stake to unstake
     */
    function unstake(uint256 _stakeId) external nonReentrant {
        require(_stakeId < userStakes[msg.sender].length, "Invalid stake ID");
        
        StakeInfo storage stakeInfo = userStakes[msg.sender][_stakeId];
        require(stakeInfo.isActive, "Stake already withdrawn");
        require(
            block.timestamp >= stakeInfo.stakeTime.add(stakeInfo.lockPeriod),
            "Stake still locked"
        );
        
        // Update pool rewards
        updatePool();
        
        uint256 amount = stakeInfo.amount;
        uint256 reward = calculateReward(msg.sender, _stakeId);
        
        // Mark stake as inactive
        stakeInfo.isActive = false;
        
        // Update totals
        userTotalStaked[msg.sender] = userTotalStaked[msg.sender].sub(amount);
        totalStaked = totalStaked.sub(amount);
        poolInfo.totalStaked = poolInfo.totalStaked.sub(amount);
        
        // Transfer staked tokens back
        stakingToken.transfer(msg.sender, amount);
        
        // Transfer rewards if any
        if (reward > 0) {
            rewardToken.transfer(msg.sender, reward);
            userTotalRewards[msg.sender] = userTotalRewards[msg.sender].add(reward);
            totalRewardsDistributed = totalRewardsDistributed.add(reward);
            emit RewardsClaimed(msg.sender, reward);
        }
        
        emit Unstaked(msg.sender, _stakeId, amount);
    }

    /**
     * @dev Claim rewards without unstaking
     * @param _stakeId Index of the stake to claim rewards for
     */
    function claimRewards(uint256 _stakeId) external nonReentrant {
        require(_stakeId < userStakes[msg.sender].length, "Invalid stake ID");
        
        StakeInfo storage stakeInfo = userStakes[msg.sender][_stakeId];
        require(stakeInfo.isActive, "Stake not active");
        
        // Update pool rewards
        updatePool();
        
        uint256 reward = calculateReward(msg.sender, _stakeId);
        require(reward > 0, "No rewards available");
        
        // Update reward debt
        stakeInfo.rewardDebt = stakeInfo.amount.mul(poolInfo.accRewardPerShare).div(1e12);
        
        // Transfer rewards
        rewardToken.transfer(msg.sender, reward);
        userTotalRewards[msg.sender] = userTotalRewards[msg.sender].add(reward);
        totalRewardsDistributed = totalRewardsDistributed.add(reward);
        
        emit RewardsClaimed(msg.sender, reward);
    }

    /**
     * @dev Emergency withdraw (forfeits rewards)
     * @param _stakeId Index of the stake to emergency withdraw
     */
    function emergencyWithdraw(uint256 _stakeId) external nonReentrant {
        require(_stakeId < userStakes[msg.sender].length, "Invalid stake ID");
        
        StakeInfo storage stakeInfo = userStakes[msg.sender][_stakeId];
        require(stakeInfo.isActive, "Stake already withdrawn");
        
        uint256 amount = stakeInfo.amount;
        
        // Mark stake as inactive
        stakeInfo.isActive = false;
        
        // Update totals
        userTotalStaked[msg.sender] = userTotalStaked[msg.sender].sub(amount);
        totalStaked = totalStaked.sub(amount);
        poolInfo.totalStaked = poolInfo.totalStaked.sub(amount);
        
        // Transfer staked tokens back (no rewards)
        stakingToken.transfer(msg.sender, amount);
        
        emit EmergencyWithdraw(msg.sender, _stakeId, amount);
    }

    /**
     * @dev Update pool reward calculations
     */
    function updatePool() public {
        if (block.timestamp <= poolInfo.lastRewardTime) {
            return;
        }
        
        if (poolInfo.totalStaked == 0) {
            poolInfo.lastRewardTime = block.timestamp;
            return;
        }
        
        uint256 timeElapsed = block.timestamp.sub(poolInfo.lastRewardTime);
        uint256 reward = timeElapsed.mul(rewardRate);
        
        poolInfo.accRewardPerShare = poolInfo.accRewardPerShare.add(
            reward.mul(1e12).div(poolInfo.totalStaked)
        );
        poolInfo.lastRewardTime = block.timestamp;
    }

    /**
     * @dev Calculate pending rewards for a specific stake
     * @param _user User address
     * @param _stakeId Stake index
     */
    function calculateReward(address _user, uint256 _stakeId) 
        public 
        view 
        returns (uint256) 
    {
        if (_stakeId >= userStakes[_user].length) {
            return 0;
        }
        
        StakeInfo memory stakeInfo = userStakes[_user][_stakeId];
        if (!stakeInfo.isActive) {
            return 0;
        }
        
        uint256 accRewardPerShare = poolInfo.accRewardPerShare;
        
        // Calculate pending pool rewards
        if (block.timestamp > poolInfo.lastRewardTime && poolInfo.totalStaked > 0) {
            uint256 timeElapsed = block.timestamp.sub(poolInfo.lastRewardTime);
            uint256 reward = timeElapsed.mul(rewardRate);
            accRewardPerShare = accRewardPerShare.add(
                reward.mul(1e12).div(poolInfo.totalStaked)
            );
        }
        
        uint256 baseReward = stakeInfo.amount.mul(accRewardPerShare).div(1e12).sub(stakeInfo.rewardDebt);
        
        // Apply multiplier
        return baseReward.mul(stakeInfo.multiplier).div(100);
    }

    /**
     * @dev Get lock duration and multiplier for lock period type
     * @param _lockPeriod Lock period type (1-4)
     */
    function getLockDetails(uint8 _lockPeriod) 
        public 
        pure 
        returns (uint256 lockTime, uint256 multiplier) 
    {
        if (_lockPeriod == 1) {        // 1 week
            return (7 days, WEEK_MULTIPLIER);
        } else if (_lockPeriod == 2) { // 1 month
            return (30 days, MONTH_MULTIPLIER);
        } else if (_lockPeriod == 3) { // 3 months
            return (90 days, QUARTER_MULTIPLIER);
        } else if (_lockPeriod == 4) { // 1 year
            return (365 days, YEAR_MULTIPLIER);
        }
        
        revert("Invalid lock period");
    }

    // View functions for frontend integration

    /**
     * @dev Get user's total staking information
     */
    function getUserInfo(address _user) 
        external 
        view 
        returns (
            uint256 totalStaked_,
            uint256 totalRewards_,
            uint256 activeStakes,
            uint256 totalPendingRewards
        ) 
    {
        totalStaked_ = userTotalStaked[_user];
        totalRewards_ = userTotalRewards[_user];
        
        uint256 stakesLength = userStakes[_user].length;
        for (uint256 i = 0; i < stakesLength; i++) {
            if (userStakes[_user][i].isActive) {
                activeStakes++;
                totalPendingRewards = totalPendingRewards.add(calculateReward(_user, i));
            }
        }
    }

    /**
     * @dev Get specific stake information
     */
    function getStakeInfo(address _user, uint256 _stakeId)
        external
        view
        returns (
            uint256 amount,
            uint256 stakeTime,
            uint256 lockPeriod,
            uint256 multiplier,
            uint256 pendingRewards,
            bool canUnstake,
            bool isActive
        )
    {
        require(_stakeId < userStakes[_user].length, "Invalid stake ID");
        
        StakeInfo memory stakeInfo = userStakes[_user][_stakeId];
        
        amount = stakeInfo.amount;
        stakeTime = stakeInfo.stakeTime;
        lockPeriod = stakeInfo.lockPeriod;
        multiplier = stakeInfo.multiplier;
        pendingRewards = calculateReward(_user, _stakeId);
        canUnstake = block.timestamp >= stakeInfo.stakeTime.add(stakeInfo.lockPeriod);
        isActive = stakeInfo.isActive;
    }

    /**
     * @dev Get pool statistics
     */
    function getPoolInfo() 
        external 
        view 
        returns (
            uint256 totalStaked_,
            uint256 rewardRate_,
            uint256 totalRewardsDistributed_,
            uint256 rewardTokenBalance
        ) 
    {
        totalStaked_ = totalStaked;
        rewardRate_ = rewardRate;
        totalRewardsDistributed_ = totalRewardsDistributed;
        rewardTokenBalance = rewardToken.balanceOf(address(this));
    }

    // Owner functions

    /**
     * @dev Update reward rate (owner only)
     */
    function setRewardRate(uint256 _rewardRate) external onlyOwner {
        updatePool();
        rewardRate = _rewardRate;
        emit RewardRateUpdated(_rewardRate);
    }

    /**
     * @dev Update minimum lock duration (owner only)
     */
    function setLockDuration(uint256 _lockDuration) external onlyOwner {
        lockDuration = _lockDuration;
        emit LockDurationUpdated(_lockDuration);
    }

    /**
     * @dev Emergency pause contract (owner only)
     */
    function pause() external onlyOwner {
        _pause();
    }

    /**
     * @dev Unpause contract (owner only)
     */
    function unpause() external onlyOwner {
        _unpause();
    }

    /**
     * @dev Emergency withdrawal of reward tokens (owner only)
     */
    function emergencyWithdrawRewards(uint256 _amount) external onlyOwner {
        require(_amount <= rewardToken.balanceOf(address(this)), "Insufficient balance");
        rewardToken.transfer(owner(), _amount);
    }

    /**
     * @dev Add reward tokens to the pool (anyone can add)
     */
    function addRewards(uint256 _amount) external {
        require(_amount > 0, "Cannot add 0 rewards");
        rewardToken.transferFrom(msg.sender, address(this), _amount);
    }
}
