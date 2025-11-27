
import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.worker.engine import WorkflowEngine
from src.worker.config import WorkerConfig, WorkflowConfig, AgentConfig, ResourcesConfig, ModelConfig

@pytest.fixture
def mock_config():
    return WorkerConfig(
        name="test",
        resources=ResourcesConfig(
            models={"m1": ModelConfig(type="openai", deployment="gpt-4")}, 
            tools=[]
        ),
        agents=[
            AgentConfig(id="a1", role="r1", model="m1", instructions="i1"),
            AgentConfig(id="a2", role="r2", model="m1", instructions="i2")
        ],
        workflow=WorkflowConfig(
            type="group_chat",
            steps=[], # Steps are needed to create agents in engine
            manager_model="m1"
        )
    )

@patch("src.worker.engine.GroupChatBuilder")
@patch("src.worker.engine.AgentFactory")
def test_group_chat_builder_usage(MockFactory, MockBuilder, mock_config):
    # Add steps to config so agents are created
    from src.worker.config import WorkflowStep
    mock_config.workflow.steps = [
        WorkflowStep(id="s1", type="agent", agent="a1", input_template="t1"),
        WorkflowStep(id="s2", type="agent", agent="a2", input_template="t2")
    ]

    engine = WorkflowEngine(mock_config)
    
    # Mock factory behavior
    mock_factory_instance = MockFactory.return_value
    mock_factory_instance.create_agent.return_value = MagicMock()
    mock_factory_instance.create_client.return_value = MagicMock()
    
    # Mock builder behavior
    mock_builder_instance = MockBuilder.return_value
    
    engine.build()
    
    # Verify participants called
    mock_builder_instance.participants.assert_called_once()
    
    # Verify set_prompt_based_manager was called (Standard for v1.0.0b251120)
    mock_builder_instance.set_prompt_based_manager.assert_called_once()
    
    # Verify create_client was called
    mock_factory_instance.create_client.assert_called_once()
