---
name: SakThai-hf-deep-rl-course
author: SakThai
license: MIT
description: "Train RL agents with Stable Baselines3 and Hugging Face."
version: 1.0.0
tags: [ReinforcementLearning, RL, DeepRL, StableBaselines, HuggingFace]
---
# Deep Reinforcement Learning with Hugging Face

Based on the [HF Deep RL Course](https://huggingface.co/learn/deep-rl-course). Covers Q-learning, policy gradients, PPO, A2C, multi-agent RL, and training agents in game environments.

## When to Use

- User wants to "train a reinforcement learning agent"
- User asks about PPO, DQN, A2C, or policy gradients
- User wants to use Stable Baselines3 or CleanRL
- User needs RL environments (Atari, Unity ML-Agents, PyBullet)

## Prerequisites & Setup

```bash
pip install stable-baselines3 gymnasium torch tensorboard
pip install gymnasium[atari] autorom  # Atari envs
auto-rom
pip install pybullet  # robotics
pip install mlagents  # Unity
pip install optuna    # hyperparameter tuning
```

## Quick Reference

| Algorithm | Library | Action Space | Best For |
|-----------|---------|-------------|----------|
| DQN | SB3 | Discrete | Atari, card games |
| PPO | SB3 | Both | General-purpose, stable |
| A2C | SB3 | Both | Synchronous actor-critic |
| SAC | SB3 | Continuous | Robotic control, sample efficient |
| TD3 | SB3 | Continuous | Continuous, avoids overestimation |
| DDPG | SB3 | Continuous | Older; SAC preferred |
| CleanRL | cleanrl | Both | Readable reference implementations |

## Environment Setup

### Gymnasium Environments
```python
import gymnasium as gym
env = gym.make("CartPole-v1")             # Discrete, simple
env = gym.make("LunarLander-v2")           # Discrete, medium
env = gym.make("BipedalWalker-v3")         # Continuous, hard
env = gym.make("ALE/Breakout-v5", render_mode="rgb_array")  # Atari
```

### Custom Environment (SB3-compatible)
```python
import gymnasium as gym
from gymnasium import spaces
import numpy as np

class CustomEnv(gym.Env):
    def __init__(self):
        super().__init__()
        self.observation_space = spaces.Box(low=-np.inf, high=np.inf, shape=(4,), dtype=np.float32)
        self.action_space = spaces.Discrete(2)
        self.state = None

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.state = np.zeros(4, dtype=np.float32)
        return self.state, {}

    def step(self, action):
        reward = 0.0
        self.state += np.random.randn(4) * 0.1
        return self.state, reward, False, False, {}
```

### Vectorized Environments
```python
from stable_baselines3.common.env_util import make_vec_env
vec_env = make_vec_env("CartPole-v1", n_envs=4)
```

## Training Loop Examples

### PPO (Minimal)
```python
from stable_baselines3 import PPO
env = make("CartPole-v1")
model = PPO("MlpPolicy", env, verbose=1).learn(100_000)
model.save("ppo_cartpole")
```

### PPO (Production-style with callbacks)
```python
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.callbacks import EvalCallback, CheckpointCallback

env = make_vec_env("LunarLander-v2", n_envs=4)
model = PPO("MlpPolicy", env, learning_rate=3e-4, n_steps=2048, batch_size=64,
            n_epochs=10, gamma=0.99, gae_lambda=0.95, clip_range=0.2,
            verbose=1, tensorboard_log="./logs/")
eval_callback = EvalCallback(make_vec_env("LunarLander-v2", n_envs=1),
                             best_model_save_path="./logs/best/", eval_freq=10000)
model.learn(total_timesteps=1_000_000, callback=eval_callback)
model.save("ppo_lunar_final")
```

### DQN on Atari
```python
from stable_baselines3 import DQN
from stable_baselines3.common.env_util import make_atari_env
from stable_baselines3.common.vec_env import VecFrameStack
env = VecFrameStack(make_atari_env("ALE/Breakout-v5", n_envs=4), n_stack=4)
model = DQN("CnnPolicy", env, learning_rate=1e-4, buffer_size=100000,
            learning_starts=50000, verbose=1).learn(10_000_000)
model.save("dqn_breakout")
```

### SAC for Continuous Control
```python
from stable_baselines3 import SAC
env = make_vec_env("BipedalWalker-v3", n_envs=4)
model = SAC("MlpPolicy", env, learning_rate=3e-4, buffer_size=1_000_000,
            batch_size=256, ent_coef="auto", verbose=1).learn(3_000_000)
model.save("sac_bipedal_walker")
```

## Evaluation

```python
model = PPO.load("ppo_cartpole")
env = gym.make("CartPole-v1")
rewards = []
for ep in range(10):
    obs, _ = env.reset()
    total = 0
    done = False
    while not done:
        action, _ = model.predict(obs, deterministic=True)
        obs, reward, terminated, truncated, _ = env.step(action)
        total += reward
        done = terminated or truncated
    rewards.append(total)
print(f"Mean: {np.mean(rewards):.1f} ± {np.std(rewards):.1f}")
```

## Hyperparameter Tuning with Optuna

```python
import optuna
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env

def objective(trial):
    env = make_vec_env("LunarLander-v2", n_envs=4)
    model = PPO("MlpPolicy", env,
                learning_rate=trial.suggest_float("lr", 1e-5, 1e-3, log=True),
                n_steps=trial.suggest_int("n_steps", 256, 4096),
                batch_size=trial.suggest_int("batch_size", 32, 256),
                gamma=trial.suggest_float("gamma", 0.9, 0.9999), verbose=0)
    model.learn(50_000)
    # evaluate model...
    return mean_reward

study = optuna.create_study(direction="maximize")
study.optimize(objective, n_trials=50)
```

## Pitfalls

- RL is sample-hungry — expect millions of timesteps for complex environments.
- Hyperparameter tuning is critical — use Optuna or SB3's built-in search.
- Environment wrappers (frame stack, grayscale, resize) are essential for Atari.
- Multi-agent environments need specialized libs (PettingZoo, RLlib).
- Training stability varies by seed — always test across 3-5 random seeds.
- Use `deterministic=True` during eval for consistent results.

## Verification

```python
from stable_baselines3 import PPO, make
model = PPO("MlpPolicy", make("CartPole-v1"), verbose=0).learn(5000)
obs, _ = make("CartPole-v1").reset(); print(model.predict(obs, deterministic=True)[0])
```
