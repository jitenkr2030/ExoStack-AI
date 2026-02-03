# ExoStack AI - Turning Idle Laptops into AI Powerhouses

ExoStack AI is an advanced distributed AI compute platform that transforms idle laptops into powerful AI processing nodes. It intelligently detects when laptops are unused and leverages their computational resources for AI/ML workloads while respecting user experience and battery life.

## 🌟 Key Features

### 1. AI-Ready Idle Detection
- **Smart Activity Monitoring**: Detects user inactivity across platforms (Windows, macOS, Linux)
- **System Load Analysis**: Monitors CPU, memory, and GPU usage to determine true idle state
- **Configurable Thresholds**: Customizable idle detection parameters (default: 5 minutes of low activity)
- **User-Friendly**: Automatically pauses AI work when user returns

### 2. Power-Aware Computing
- **Battery Monitoring**: Real-time battery level and power source detection
- **Adaptive Throttling**: Automatically adjusts compute intensity based on battery level
- **Power Source Optimization**: Full performance when plugged in, conservative on battery
- **Critical Battery Protection**: Stops AI work below 20% battery

### 3. Intelligent AI Task Distribution
- **Readiness Scoring**: 0-100 score based on idle state, power, and resources
- **Priority Scheduling**: Routes AI tasks to best-suited laptops
- **GPU-Aware Assignment**: Automatically detects and utilizes available GPUs
- **Load Balancing**: Distributes tasks based on current system capabilities

### 4. Laptop-Optimized Agent
- **Cross-Platform Support**: Windows, macOS, and Linux compatibility
- **Resource Monitoring**: Real-time CPU, memory, GPU, and disk usage tracking
- **Health Reporting**: Comprehensive system health and AI readiness metrics
- **Graceful Interruption**: Seamlessly handles user activity and power changes

### 5. AI Compute Dashboard
- **Real-Time Monitoring**: Live view of laptop AI readiness and task execution
- **Power Status Visualization**: Battery levels and power source information
- **Idle Time Tracking**: See which laptops are ready for AI work
- **Task Analytics**: Monitor AI task distribution and completion rates

### 6. Smart Resource Management
- **Dynamic Limits**: Adjusts concurrent tasks based on system state
- **Memory Optimization**: Prevents system slowdown with intelligent memory management
- **Thermal Awareness**: Monitors system temperature to prevent overheating
- **Network Efficiency**: Optimized data transfer for distributed AI workloads

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+
- Modern laptop with idle time available
- Optional: NVIDIA GPU for accelerated AI compute

### Installation

1. Clone the repository:

```bash
git clone https://github.com/jitenkr2030/exostack.git
cd exostack
```

2. Install Python dependencies:

```bash
pip install -r requirements.txt
```

3. Install UI dependencies:

```bash
cd exo_ui
npm install
```

### Quick Start

1. **Start the ExoStack Hub (AI Scheduler):**

```bash
python start_exostack.py hub
```

2. **Deploy an AI Agent on your laptop:**

```bash
python start_exostack.py agent --node-id my-laptop
```

3. **Access the AI Dashboard:**

```bash
cd exo_ui
npm run dev
```

4. **Submit AI Tasks:**

```bash
# Submit a text generation task
python -m exo_cli infer --model gpt2 --prompt "Hello world"

# Submit a custom AI task
curl -X POST http://localhost:8000/tasks/submit \
  -H "Content-Type: application/json" \
  -d '{"task_type": "text_generation", "model": "gpt2", "input": "Hello world"}'
```

## 📚 AI Compute Features

### How ExoStack AI Works

1. **Idle Detection**: The agent monitors your laptop for user activity and system load
2. **Readiness Assessment**: Calculates an AI readiness score (0-100) based on:
   - Current idle duration
   - Battery level and power source
   - Available CPU, memory, and GPU resources
3. **Task Assignment**: The hub assigns AI tasks to laptops with highest readiness scores
4. **Smart Execution**: Tasks run with respect to system resources and power constraints
5. **User Priority**: AI work instantly pauses when you return to your laptop

### AI Readiness Scoring

| Factor | Weight | Description |
|--------|--------|-------------|
| Idle State | 40% | Duration and stability of idle time |
| Power Source | 30% | Plugged in vs battery level |
| System Resources | 30% | Available CPU, memory, and GPU |

**Readiness Levels:**
- **80-100**: Excellent for intensive AI tasks
- **60-79**: Good for moderate AI workloads
- **40-59**: Light AI tasks only
- **0-39**: Not suitable for AI compute

### Power Management

| Battery Level | Max CPU Usage | Max Memory | Concurrent Tasks |
|---------------|---------------|------------|------------------|
| Plugged In | 90% | 90% | 5 |
| >80% | 70% | 80% | 3 |
| 50-80% | 50% | 70% | 2 |
| 20-50% | 30% | 50% | 1 |
| <20% | No AI compute |

## 🔧 Configuration

### Agent Configuration

```yaml
# config/agent.yaml
agent:
  node_id: "my-laptop"
  hub_address: "http://localhost:8000"
  
idle_detection:
  cpu_threshold: 10.0      # CPU % below this is considered idle
  memory_threshold: 70.0   # Memory % below this is considered idle
  idle_duration: 300       # Seconds of low activity to be idle
  
power_management:
  battery_threshold: 20.0  # Stop AI work below this battery level
  enable_throttling: true  # Reduce AI work on battery
  
ai_compute:
  max_concurrent_tasks: 5  # Maximum concurrent AI tasks
  gpu_priority: true       # Prefer GPU when available
```

### Hub Configuration

```yaml
# config/hub.yaml
hub:
  port: 8000
  metrics_port: 9000
  
scheduling:
  algorithm: "ai_readiness"  # Prioritize AI-ready laptops
  readiness_threshold: 60    # Minimum score for AI tasks
  cache_ttl: 30             # AI readiness cache duration
```

## 📊 Monitoring

### AI Dashboard Metrics

- **AI Ready Nodes**: Laptops currently ready for AI work
- **Readiness Scores**: Real-time AI readiness for each laptop
- **Power Status**: Battery levels and power sources
- **Idle Duration**: How long laptops have been idle
- **Task Distribution**: AI task execution across laptops
- **Resource Usage**: CPU, memory, and GPU utilization

### API Endpoints

#### AI Compute Management

```bash
# Get AI readiness for all nodes
GET /nodes/ai-readiness

# Get detailed node health with AI metrics
GET /nodes/{node_id}/health/detailed

# Submit AI task with laptop optimization
POST /tasks/submit
{
  "task_type": "text_generation",
  "model": "gpt2",
  "input": "Hello world",
  "priority": "normal",
  "laptop_optimized": true
}

# Get AI task status
GET /tasks/{task_id}/status
```

#### Node Management

```bash
# Register laptop node with AI capabilities
POST /nodes/register
{
  "id": "my-laptop",
  "capabilities": ["inference", "text-generation", "idle-detection"],
  "laptop_optimized": true,
  "gpu_available": true
}

# Node heartbeat with AI readiness
POST /nodes/{node_id}/heartbeat
{
  "ready_for_ai": true,
  "readiness_score": 85,
  "idle_state": {...},
  "power_state": {...}
}
```

## 🛠 Development

### Running Tests

```bash
# Run all tests
pytest tests/

# Run AI-specific tests
pytest tests/test_ai_compute.py

# Run laptop agent tests
pytest tests/test_laptop_agent.py
```

### Building for Production

```bash
# Build UI
cd exo_ui
npm run build

# Build Docker images
docker-compose build

# Deploy with Kubernetes
kubectl apply -f k8s/
```

## 🔌 AI Model Support

### Supported Models

- **Text Generation**: GPT-2, GPT-Neo, BLOOM
- **Image Generation**: Stable Diffusion, DALL-E Mini
- **Code Generation**: CodeParrot, StarCoder
- **Embedding Models**: Sentence Transformers, OpenAI Embeddings

### Model Optimization

- **Quantization**: Reduced memory usage for laptop deployment
- **Pruning**: Faster inference on consumer hardware
- **Batch Processing**: Efficient handling of multiple requests
- **Model Sharding**: Distribute large models across multiple laptops

## 🌍 Use Cases

### For Individuals

- **Personal AI Assistant**: Run your own AI models locally
- **Learning & Development**: Experiment with AI without cloud costs
- **Privacy-Preserving AI**: Keep sensitive data on your device
- **Background Processing**: Utilize idle time for AI computations

### For Organizations

- **Distributed AI Workforce**: Leverage employee laptops for AI compute
- **Cost-Effective ML**: Reduce cloud computing expenses
- **Edge AI**: Process data locally for faster responses
- **Sustainable Computing**: Use existing hardware instead of new servers

## 🔒 Security & Privacy

- **Local Processing**: AI work stays on your laptop
- **Encrypted Communication**: Secure data transfer between nodes
- **User Control**: Complete control over when and how AI work runs
- **Data Privacy**: No data sent to external servers without explicit consent

## 🤝 Contributing

We welcome contributions! See our [Contributing Guide](CONTRIBUTING.md) for details.

### Areas for Contribution

- **Platform Support**: Add support for more operating systems
- **AI Models**: Integrate new AI models and frameworks
- **UI Improvements**: Enhance the dashboard experience
- **Performance**: Optimize resource usage and task scheduling
- **Documentation**: Improve guides and API documentation

## 📈 Roadmap

### v2.0 Features
- [ ] Mobile device support (Android/iOS)
- [ ] Advanced model optimization
- [ ] Multi-GPU laptop support
- [ ] Federated learning capabilities
- [ ] Web-based agent deployment

### v1.5 Features
- [ ] Real-time collaboration
- [ ] Advanced scheduling algorithms
- [ ] Custom AI model marketplace
- [ ] Enterprise management features

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Thanks to the open-source AI community
- Contributors who helped build the laptop optimization features
- Early adopters who provided valuable feedback
- The distributed systems community for inspiration

## 📞 Support

- **GitHub Issues**: For bug reports and feature requests
- **Discord Community**: [Join our Discord](https://discord.gg/exostack)
- **Documentation**: [Full Documentation](https://docs.exostack.ai)
- **Email**: support@exostack.ai

---

**ExoStack AI: Transforming idle time into intelligent computation** 🚀