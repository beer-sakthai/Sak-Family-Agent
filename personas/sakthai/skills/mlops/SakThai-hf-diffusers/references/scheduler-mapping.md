# Quick Reference: A1111 / k-diffusion → Diffusers Scheduler Mapping

Use this table when porting prompts or workflows from AUTOMATIC1111 / ComfyUI to 🤗 Diffusers.

| A1111 / k-diffusion | Diffusers Class | Init kwargs if different |
|---------------------|-----------------|---------------------------|
| DPM++ 2M | `DPMSolverMultistepScheduler` | |
| DPM++ 2M Karras | `DPMSolverMultistepScheduler` | `use_karras_sigmas=True` |
| DPM++ 2M SDE | `DPMSolverMultistepScheduler` | `algorithm_type="sde-dpmsolver++"` |
| DPM++ 2M SDE Karras | `DPMSolverMultistepScheduler` | `use_karras_sigmas=True`, `algorithm_type="sde-dpmsolver++"` |
| DPM++ SDE | `DPMSolverSinglestepScheduler` | |
| DPM++ SDE Karras | `DPMSolverSinglestepScheduler` | `use_karras_sigmas=True` |
| DPM2 | `KDPM2DiscreteScheduler` | |
| DPM2 Karras | `KDPM2DiscreteScheduler` | `use_karras_sigmas=True` |
| DPM2 a | `KDPM2AncestralDiscreteScheduler` | |
| DPM2 a Karras | `KDPM2AncestralDiscreteScheduler` | `use_karras_sigmas=True` |
| Euler | `EulerDiscreteScheduler` | |
| Euler a | `EulerAncestralDiscreteScheduler` | |
| Heun | `HeunDiscreteScheduler` | |
| LMS | `LMSDiscreteScheduler` | |
| LMS Karras | `LMSDiscreteScheduler` | `use_karras_sigmas=True` |
| DDIM | `DDIMScheduler` | |
| UniPC | `UniPCMultistepScheduler` | |

## Noise schedule aliases

| A1111 `schedule` value | Diffusers init kwargs |
|------------------------|------------------------|
| `simple` or `sgm_uniform` | `timestep_spacing="trailing"` |
| `exponential` | `timestep_spacing="linspace"`, `use_exponential_sigmas=True` |
| `beta` | `timestep_spacing="linspace"`, `use_beta_sigmas=True` |
| `Karras` | `use_karras_sigmas=True` |

## Pitfalls
- Discrete schedulers expect integer `timestep`; continuous schedulers expect float `sigmas`.
- Some A1111 names (e.g. `DPM++ 2S a`) have no exact match in Diffusers; use `DPMSolverSinglestepScheduler` as closest equivalent.
- `DPM adaptive` and `DPM fast` from k-diffusion are not implemented in Diffusers.
