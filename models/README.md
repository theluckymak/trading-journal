# DRL Models Directory

Place trained model files here before running `docker-compose up`:

- `ppo_daily.zip` — PPO agent (Stable Baselines3)
- `a2c_daily.zip` — A2C agent (Stable Baselines3)
- `sac_daily.zip` — SAC agent (Stable Baselines3)
- `hmm_model.pkl` — HMM regime detector (hmmlearn)

These are mounted read-only into the backend container at `/app/ai/saved_models/drl/`.
