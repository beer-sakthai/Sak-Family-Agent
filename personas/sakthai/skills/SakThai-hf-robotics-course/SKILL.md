---
name: SakThai-hf-robotics-course
description: "Robot learning with LeRobot \u2014 imitation, RL, VLA models, and real-world robotics\
  \ using Hugging Face ecosystem."
---

# Robotics with LeRobot

Based on the [HF Robotics Course](https://huggingface.co/learn/robotics-course) and [LeRobot](https://github.com/huggingface/lerobot). Covers classical robotics, imitation learning, reinforcement learning, VLA (Vision-Language-Action) models, and world models for robotics using LeRobot and the HF Hub ecosystem.

## When to Use

- User wants to "build a robot" or "train a robotic arm"
- User asks about LeRobot, imitation learning, or sim-to-real
- User needs robotics datasets from the HF Hub
- User wants to implement RL or VLA models for robotics
- User asks about Pi0, GR00T, ACT, Diffusion policies for robotics
- User is following the HF Robotics Course (units 0–2 released; 5–7 coming soon)

## Prerequisites

```bash
pip install lerobot torch
# For simulation:
pip install gymnasium
# For MuJoCo (if using MuJoCo environments):
pip install mujoco
```

Robot datasets from [HF Hub @ lerobot](https://huggingface.co/lerobot).

## Quick Reference

| Concept | Tool | Description |
|---------|------|-------------|
| LeRobot | `pip install lerobot` | Robotics dataset & training library (Apache 2.0, PyTorch) |
| Datasets | `LeRobotDataset` | Pre-collected robot demonstrations on HF Hub (Parquet + MP4 format) |
| Imitation Learning | `lerobot-train` | Behavioral cloning via ACT, Diffusion, VQ-BeT, Multi-task DiT |
| RL for Robotics | `lerobot-train` | Reinforcement learning via HIL-SERL, TDMPC |
| VLA Models | `lerobot-train` | Pi0, Pi0Fast, Pi0.5, GR00T N1.7, SmolVLA, XVLA, EO-1, MolmoAct2 |
| World Models | `lerobot` | VLA-JEPA, LingBot-VA, FastWAM |
| Reward Models | `lerobot` | SARM, TOPReward, Robometer |
| Evaluation | `lerobot-eval` | Benchmarks: LIBERO, MetaWorld (more coming) |
| Web UI | LeLab | Browser-based teleop, calibration, dataset recording |
| Robot Control | `Robot` class | Unified hardware-agnostic Python interface |
| Hardware | Various | SO-100, LeKiwi, Koch, HopeJR, OMX, EarthRover, Reachy2, Unitree G1, reBot B601 |

## VLA Model Comparison

| Model | Size | Type | Training Data | Robot Support | Notes |
|-------|------|------|---------------|---------------|-------|
| **Pi0** | 3.3B | VLA (Flow Match) | Open X-Embodiment | SO-100, Aloha, etc. | SOTA generalist; fine-tuned variants available |
| **Pi0Fast** | 3.3B | VLA (Fast) | Distilled from Pi0 | Same as Pi0 | 2x faster inference, slight quality drop |
| **Pi0.5** | 0.5B | VLA (Small) | Distilled | Embedded devices | Runs on edge hardware |
| **GR00T N1.7** | 1.7B | VLA | Proprietary + open | Various NVIDIA | From NVIDIA, good for simulation |
| **SmolVLA** | 0.3B | VLA | Synthetic + real | SO-100, Koch | Lightweight, good for prototyping |
| **ACT** | ~80M | Imitation (transformer) | Task-specific | SO-100, Aloha | Classic imitation learning baseline |
| **Diffusion Policy** | ~50M | Imitation (diffusion) | Task-specific | Various | Robust multi-modal action prediction |
| **VQ-BeT** | ~40M | Imitation (VQ) | Task-specific | Various | Discrete action tokens |
| **XVLA** | 1.2B | VLA (cross-attn) | Open X-Embodiment | SO-100 | Cross-architecture VLA |
| **EO-1** | 1.5B | VLA (embodied) | Proprietary | Various | Embodied observation focus |
| **MolmoAct2** | 1.0B | VLA | MOLMO dataset | SO-100 | Open-source vision-language-action |

## Course Syllabus (HF Robotics Course)

| Unit | Topic | Status |
|------|-------|--------|
| 0 | Welcome to Robotics | ✅ Published |
| 1 | Introduction to Robot Learning | ✅ Published |
| 2 | Classical Robotics (kinematics, IK, FK, limitations) | ✅ Published |
| 5 | Reinforcement Learning | Coming Soon |
| 6 | Imitation Learning | Coming Soon |
| 7 | Foundation Models | Coming Soon |

## Complete LeRobot Setup

### 1. Installation
```bash
# Create a clean environment
python -m venv lerobot-env
source lerobot-env/bin/activate

# Install LeRobot
pip install --upgrade pip
pip install lerobot

# Verify installation
lerobot-info
```

### 2. Verify with a dataset
```python
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset

dataset = LeRobotDataset("lerobot/pusht", split="train")
print(f"Dataset: {dataset}")
print(f"Number of episodes: {len(dataset)}")
print(f"Features: {list(dataset.features.keys())}")
```

### 3. Explore dataset structure
```python
episode = dataset[0]
print("Observation keys:", episode.get('observation', {}).keys())
print("Action shape:", episode['action'].shape)
print("State shape:", episode['observation']['state'].shape if 'state' in episode['observation'] else 'N/A')
```

## Imitation Learning Examples

### 1. Train ACT (Action Chunking Transformer)
```bash
# CLI mode
lerobot-train \
  --policy.type=act \
  --dataset.repo_id=lerobot/aloha_mobile_cabinet \
  --training.num_epochs=100 \
  --training.batch_size=8 \
  --training.learning_rate=1e-5 \
  --output_dir=./outputs/act_aloha
```

### 2. Train Diffusion Policy
```bash
lerobot-train \
  --policy.type=diffusion \
  --dataset.repo_id=lerobot/pusht \
  --training.num_epochs=50 \
  --training.batch_size=64 \
  --output_dir=./outputs/diffusion_pusht
```

### 3. Python API for Training
```python
from lerobot.common.policies.diffusion import DiffusionPolicy
from lerobot.scripts.train import train
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset

# Load dataset
dataset = LeRobotDataset("lerobot/pusht", split="train")

# Configure policy
policy = DiffusionPolicy(
    obs_mode="rgb",
    action_dim=dataset.features["action"].shape[0],
    horizon=16,
    n_action_steps=8,
)

# Train
train(
    policy=policy,
    dataset=dataset,
    output_dir="./trained_policy",
    num_epochs=50,
    batch_size=64,
)

# Load trained policy
policy = DiffusionPolicy.from_pretrained("./trained_policy")

# Inference on an observation
obs = dataset[0]["observation"]
action = policy.select_action(obs)
```

### 4. Training with Custom Dataset
```python
# Record your own dataset with LeLab or from existing data
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset
from pathlib import Path

# Create dataset from local files
# Expected format: episodes/ with video + parquet
dataset = LeRobotDataset.create(
    repo_id="my-user/my-robot-dataset",
    fps=30,
    robot_type="so100",
)
dataset.add_episode(
    video_paths={"observation.image": "episode_0.mp4"},
    states=states_array,  # (T, state_dim)
    actions=actions_array,  # (T, action_dim)
)
dataset.save()
```

### 5. Evaluate a policy
```bash
# LIBERO benchmark
lerobot-eval \
  --policy.path=lerobot/pi0_libero_finetuned \
  --env.type=libero \
  --env.task=libero_object \
  --eval.n_episodes=10

# Custom environment
lerobot-eval \
  --policy.path=./trained_policy \
  --env.type=custom \
  --eval.n_episodes=20
```

### 6. Deploy on Real Robot
```python
from lerobot.common.policies.diffusion import DiffusionPolicy
from lerobot.robots.so100 import SO100Robot

# Load trained policy
policy = DiffusionPolicy.from_pretrained("./trained_policy")

# Connect to robot
robot = SO100Robot()
robot.connect()

# Control loop
for _ in range(100):
    obs = robot.get_observation()
    action = policy.select_action(obs)
    robot.send_action(action)

robot.disconnect()
```

## Dataset Format (v3)

LeRobotDataset v3 uses:
- **Parquet** files for structured data (state, action, rewards, etc.)
- **MP4** videos for vision observations (synchronized, re-encoded)
- Episode-level storage on HF Hub

```python
# Dataset structure
dataset = LeRobotDataset("lerobot/pusht", split="train")
# ├── episodes/
# │   ├── episode_0/
# │   │   ├── observation.image.mp4
# │   │   └── episode.parquet
# │   ├── episode_1/
# │   └── ...
# ├── meta/
# │   ├── info.json
# │   └── stats.json
# └── features.json
```

Dataset manipulation tools:
```python
# Delete episodes
dataset.delete_episodes([0, 1, 2])

# Split dataset
train, val = dataset.split(0.8)

# Add/remove features
dataset.add_feature("reward", ...)
dataset.remove_feature("extra_state")

# Merge datasets
from lerobot.common.datasets.utils import merge_datasets
merged = merge_datasets([dataset1, dataset2])
```

## Supported Hardware

SO100, LeKiwi, Koch v1/v2, HopeJR, OMX, EarthRover, Reachy2, Gamepads, Keyboards, Phones, OpenARM, Unitree G1, reBot B601.

The library is extensible — implement the `Robot` interface to support custom hardware.

### Adding Custom Robot Support
```python
from lerobot.robots.robot import Robot

class MyCustomRobot(Robot):
    def connect(self):
        # Initialize hardware connection
        pass
    
    def get_observation(self):
        # Return observation dict
        return {"state": ..., "image": ...}
    
    def send_action(self, action):
        # Send action to robot
        pass
    
    def disconnect(self):
        # Clean shutdown
        pass
```

## LeLab (Browser-based UI)

LeLab is a web interface for LeRobot — teleoperate, calibrate, record datasets, replay, and train SO-100 arms from the browser without CLI.
- GitHub: [huggingface/leLab](https://github.com/huggingface/leLab)
- Access via HF Space

## Key Architectural Points

1. **LeRobotDataset format** (v3): Parquet (state/action) + MP4 (vision). Stored on HF Hub. Tools: delete episodes, split, add/remove features, merge datasets.
2. **Hardware-agnostic**: `Robot` class decouples control logic from hardware specifics.
3. **SoTA policies**: Pure PyTorch implementations of ACT, Diffusion, VQ-BeT, Pi0, GR00T, etc.
4. **EnvHub**: Distribution mechanism for sim environments and benchmarks via HF Hub.
5. **ICLR 2026**: LeRobot paper accepted at ICLR 2026 ([arXiv:2602.22818](https://arxiv.org/abs/2602.22818)).

## Troubleshooting

| Problem | Likely Cause | Solution |
|---------|-------------|----------|
| `lerobot-info` fails | Python version < 3.10 | Use Python 3.10+ |
| `CUDA out of memory` during training | Policy too large / batch too high | Reduce batch_size, use smaller policy |
| `Dataset download fails` | HF auth not set | `huggingface-cli login` |
| `Simulation not found` | MuJoCo not installed | `pip install mujoco` |
| `MP4 decoding error` | Corrupted dataset | Re-download or check disk space |
| `Robot not connecting` | Wrong port/permissions | Check USB connection, udev rules |
| `VLA inference OOM` | Model too large | Use Pi0Fast or SmolVLA for limited GPU |
| `LeLab not loading` | CORS/config issue | Check Space config or run locally |

## Pitfalls

- Real robot hardware requires safety precautions — start in simulation.
- Imitation learning quality depends on demonstration quality.
- LeRobot is actively developed — check [docs](https://huggingface.co/docs/lerobot/index) for API changes.
- Sim-to-real transfer is non-trivial; domain randomization helps.
- GPU/RAM requirements vary per policy — see [Compute Hardware Guide](https://huggingface.co/docs/lerobot/hardware_guide).
- Low-cost arms (SO-100) cost ~€100s vs. traditional arms costing €10k+.
- Each policy type has specific `--policy.type=` values; check README for exact names.
- Pre-trained VLA models (Pi0, GR00T) require substantial GPU memory for inference.
- Python 3.10+ required; verify with `lerobot-info`.
- Recording good demonstrations takes practice — consider using LeLab's teleop features.

## Verification

```python
from lerobot.common.datasets.lerobot_dataset import LeRobotDataset
ds = LeRobotDataset("lerobot/pusht", split="train")
print(f"Dataset has {len(ds)} episodes")
```

```bash
lerobot-info  # Verify install + available hardware/backends
```

## Resources

- [HF Robotics Course](https://huggingface.co/learn/robotics-course)
- [LeRobot Documentation](https://huggingface.co/docs/lerobot/index)
- [LeRobot GitHub](https://github.com/huggingface/lerobot)
- [HF Hub @ lerobot](https://huggingface.co/lerobot) (datasets & models)
- [LeLab Web UI](https://github.com/huggingface/leLab)
- [Robot Learning Tutorial Space](https://huggingface.co/spaces/lerobot/robot-learning-tutorial)
- [Discord](https://discord.gg/q8Dzzpym3f)
- Paper: @misc{cadene2024lerobot, ...} — [arXiv](https://arxiv.org/abs/2602.22818) (ICLR 2026)
- [Compute Hardware Guide](https://huggingface.co/docs/lerobot/hardware_guide)
