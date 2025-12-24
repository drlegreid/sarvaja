# Sim.ai K3s Deployment on Proxmox

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Proxmox VE Cluster                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 K3s Cluster (LXC/VM)                 │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐   │   │
│  │  │ Agents  │ │ LiteLLM │ │ Ollama  │ │ChromaDB │   │   │
│  │  │  Pod    │ │   Pod   │ │   Pod   │ │   Pod   │   │   │
│  │  │  :7777  │ │  :4000  │ │ :11434  │ │  :8001  │   │   │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘   │   │
│  │                                                     │   │
│  │  ┌─────────────────────────────────────────────┐   │   │
│  │  │              Persistent Volumes              │   │
│  │  │  chromadb-pv  │  ollama-pv  │  litellm-pv   │   │   │
│  │  └─────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

## Deployment Options

### Option A: K3s in Single LXC (Recommended for PoC)
- Single privileged LXC container running K3s
- Easiest setup, good for testing
- All pods share container resources

### Option B: K3s Multi-Node (Production)
- Master node + Worker nodes as separate LXCs/VMs
- Better isolation and scalability
- Requires more Proxmox resources

## Quick Start (Option A)

### 1. Create LXC Container

```bash
# On Proxmox host
pct create 200 local:vztmpl/ubuntu-22.04-standard_22.04-1_amd64.tar.zst \
  --hostname sim-ai-k3s \
  --memory 8192 \
  --cores 4 \
  --rootfs local-lvm:50 \
  --net0 name=eth0,bridge=vmbr0,ip=dhcp \
  --features nesting=1,keyctl=1 \
  --unprivileged 0

# Start container
pct start 200
```

### 2. Install K3s

```bash
# Enter container
pct enter 200

# Install K3s (single node)
curl -sfL https://get.k3s.io | sh -

# Verify
kubectl get nodes
```

### 3. Deploy Sim.ai Stack

```bash
# Clone repo
git clone https://github.com/drlegreid/platform-gai.git
cd platform-gai/deploy/k3s

# Apply manifests
kubectl apply -f namespace.yaml
kubectl apply -f secrets.yaml      # Create from .env first
kubectl apply -f chromadb.yaml
kubectl apply -f ollama.yaml
kubectl apply -f litellm.yaml
kubectl apply -f agents.yaml

# Verify pods
kubectl get pods -n sim-ai
```

### 4. Access Services

```bash
# Port forward for local access
kubectl port-forward -n sim-ai svc/agents 7777:7777 &
kubectl port-forward -n sim-ai svc/litellm 4000:4000 &

# Or use NodePort/LoadBalancer for external access
```

## Files in This Directory

| File | Purpose |
|------|---------|
| `namespace.yaml` | sim-ai namespace |
| `secrets.yaml` | API keys (from .env) |
| `chromadb.yaml` | ChromaDB StatefulSet |
| `ollama.yaml` | Ollama Deployment + PVC |
| `litellm.yaml` | LiteLLM Deployment |
| `agents.yaml` | Agents Deployment |
| `ingress.yaml` | Optional Traefik ingress |

## Migration from Docker Compose

The K3s manifests mirror the Docker Compose structure:

| Docker Compose | K3s Manifest |
|----------------|--------------|
| `services.chromadb` | `chromadb.yaml` |
| `services.ollama` | `ollama.yaml` |
| `services.litellm` | `litellm.yaml` |
| `services.agents` | `agents.yaml` |
| `volumes.*` | PersistentVolumeClaims |
| `.env` | `secrets.yaml` |

## Resource Requirements

| Component | CPU | Memory | Storage |
|-----------|-----|--------|---------|
| K3s Control Plane | 0.5 | 512Mi | 1Gi |
| ChromaDB | 0.5 | 1Gi | 10Gi |
| Ollama | 2 | 4Gi | 20Gi |
| LiteLLM | 0.5 | 512Mi | 1Gi |
| Agents | 0.5 | 512Mi | 1Gi |
| **Total** | **4** | **6.5Gi** | **33Gi** |

## Next Steps

1. [ ] Create secrets from .env
2. [ ] Apply manifests
3. [ ] Pull Ollama models
4. [ ] Test health endpoints
5. [ ] Configure ingress for external access
