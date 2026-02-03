import asyncio
import logging
import time
import requests
from datetime import datetime
from fastapi import FastAPI
from .health_monitor import health_monitor
from .executor import inference_engine
from shared.config.env import AGENT_ID, HUB_URL, AGENT_HOST, AGENT_PORT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="ExoStack Agent - AI Compute for Idle Laptops", version="1.0.0")

@app.get("/health")
async def health_check():
    """Basic health check"""
    return {"status": "healthy", "agent_id": AGENT_ID}

@app.get("/health/detailed")
async def get_detailed_health():
    """Detailed health check with AI compute readiness"""
    return health_monitor.get_detailed_health()

@app.get("/ai-readiness")
async def get_ai_readiness():
    """Get AI compute readiness information"""
    return health_monitor.get_ai_compute_readiness()

@app.get("/metrics/detailed")
async def get_detailed_metrics():
    """Get detailed system metrics"""
    return health_monitor.get_detailed_health()

@app.post("/tasks/execute")
async def execute_task(task_data: dict):
    """Execute AI task with readiness validation"""
    # Check if system is ready for AI compute
    readiness = health_monitor.get_ai_compute_readiness()
    
    if not readiness["ready_for_ai"]:
        return {
            "status": "rejected", 
            "error": "System not ready for AI compute",
            "readiness_score": readiness["readiness_score"],
            "recommendations": readiness["recommendations"]
        }
    
    task_id = task_data.get("id")
    start_time = time.time()
    
    try:
        # Apply compute limits based on power state
        compute_limits = readiness["compute_limits"]
        task_data["compute_limits"] = compute_limits
        
        result = await inference_engine.process_task(task_data)
        duration = time.time() - start_time
        health_monitor.record_task(task_id, "completed", duration)
        
        return {
            "status": "completed", 
            "result": result,
            "duration": duration,
            "compute_limits_used": compute_limits
        }
        
    except Exception as e:
        duration = time.time() - start_time
        health_monitor.record_task(task_id, "failed", duration)
        return {"status": "failed", "error": str(e), "duration": duration}

@app.get("/ping")
async def ping():
    """Ping endpoint for connectivity check"""
    return {"status": "ok", "timestamp": datetime.now().isoformat()}

@app.get("/capabilities")
async def get_capabilities():
    """Get agent capabilities and current state"""
    readiness = health_monitor.get_ai_compute_readiness()
    
    return {
        "agent_id": AGENT_ID,
        "capabilities": [
            "inference", 
            "text-generation",
            "idle-detection",
            "power-management",
            "ai-compute-readiness"
        ],
        "max_concurrent_tasks": readiness["compute_limits"]["max_concurrent_tasks"],
        "ready_for_ai": readiness["ready_for_ai"],
        "readiness_score": readiness["readiness_score"],
        "gpu_available": readiness["current_resources"]["gpu_available"],
        "power_state": readiness["power_state"]
    }

def register_agent(agent_id: str, hub_url: str) -> bool:
    """Register agent with hub, including AI compute capabilities"""
    try:
        # Get current capabilities and readiness
        readiness = health_monitor.get_ai_compute_readiness()
        
        response = requests.post(
            f"{hub_url}/nodes/register",
            json={
                "id": agent_id,
                "host": AGENT_HOST,
                "port": AGENT_PORT,
                "capabilities": [
                    "inference", 
                    "text-generation",
                    "idle-detection",
                    "power-management",
                    "ai-compute-readiness"
                ],
                "max_concurrent_tasks": readiness["compute_limits"]["max_concurrent_tasks"],
                "ready_for_ai": readiness["ready_for_ai"],
                "readiness_score": readiness["readiness_score"],
                "gpu_available": readiness["current_resources"]["gpu_available"],
                "laptop_optimized": True,
                "power_state": readiness["power_state"]
            },
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f"Agent {agent_id} registered successfully with AI compute capabilities")
            return True
        else:
            logger.error(f"Registration failed: {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Registration error: {e}")
        return False

def heartbeat(agent_id: str, hub_url: str) -> bool:
    """Send heartbeat with current AI compute readiness"""
    try:
        # Get current readiness and health
        readiness = health_monitor.get_ai_compute_readiness()
        health = health_monitor.get_detailed_health()
        
        heartbeat_data = {
            "timestamp": datetime.now().isoformat(),
            "ready_for_ai": readiness["ready_for_ai"],
            "readiness_score": readiness["readiness_score"],
            "idle_state": readiness["idle_state"],
            "power_state": readiness["power_state"],
            "current_resources": readiness["current_resources"],
            "compute_limits": readiness["compute_limits"],
            "health_status": health["status"]
        }
        
        response = requests.post(
            f"{hub_url}/nodes/{agent_id}/heartbeat",
            json=heartbeat_data,
            timeout=5
        )
        return response.status_code == 200
        
    except Exception as e:
        logger.debug(f"Heartbeat failed: {e}")
        return False

def run_inference():
    # Placeholder for inference logic
    pass

def main_loop():
    """Main agent loop with health monitoring and AI compute readiness"""
    logger.info(f"Starting ExoStack Agent {AGENT_ID} - AI Compute for Idle Laptops")
    
    # Start health monitoring
    health_monitor.start_collection()
    logger.info("Started health monitoring and idle detection")
    
    # Register with hub
    if not register_agent(AGENT_ID, HUB_URL):
        logger.error("Failed to register with hub, exiting...")
        health_monitor.stop_collection()
        return
    
    consecutive_failures = 0
    max_consecutive_failures = 5
    
    while True:
        try:
            logger.debug("Sending heartbeat with AI readiness...")
            if heartbeat(AGENT_ID, HUB_URL):
                consecutive_failures = 0
            else:
                consecutive_failures += 1
                if consecutive_failures >= max_consecutive_failures:
                    logger.error(f"{consecutive_failures} consecutive heartbeat failures, re-registering...")
                    register_agent(AGENT_ID, HUB_URL)
                    consecutive_failures = 0
            
            # Check AI compute readiness
            readiness = health_monitor.get_ai_compute_readiness()
            if readiness["ready_for_ai"]:
                logger.debug(f"System ready for AI compute (score: {readiness['readiness_score']})")
                run_inference()
            else:
                logger.debug(f"System not ready for AI compute (score: {readiness['readiness_score']})")
            
        except KeyboardInterrupt:
            logger.info("Received shutdown signal, exiting gracefully...")
            break
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}")
            
        time.sleep(10)
    
    # Cleanup
    health_monitor.stop_collection()
    logger.info("ExoStack Agent shutdown complete")

if __name__ == "__main__":
    main_loop()